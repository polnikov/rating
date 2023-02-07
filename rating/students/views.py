import re
import xlrd
import logging

from collections import Counter
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q
from django.http import Http404, JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView, View
)

from groups.models import Group
from students.forms import ResultForm, StudentForm
from students.models import Basis, Result, Semester, Student, StudentLog
from students.validators import validate_mark, check_mark
from subjects.models import Cathedra, GroupSubject, Subject
from rating.settings import IMPORT_DELIMITER
from rating.functions import calculate_rating


logger = logging.getLogger(__name__)


class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'students/students.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        students = Student.active_objects.select_related('group', 'semester').order_by(
            'semester',
            'group',
            'level',
            'last_name',
            'first_name',
            'second_name',
            'status',
        )
        context['students_list'] = students
        num_active_students = students.filter(status__exact='Является студентом').count()
        context['num_students'] = num_active_students
        graduates = Student.active_objects.select_related('group', 'semester').filter(status='Выпускник')
        context['graduates'] = graduates
        return context


class StudentCreateView(LoginRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_add.html'
    success_url = '/students/'


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student

    def get(self, request, pk, **kwargs):
        student = get_object_or_404(Student.objects.select_related('group', 'semester', 'basis'), student_id__exact=pk)

        try:
            history = StudentLog.objects.select_related('user').filter(
                record_id=student.student_id).order_by('-timestamp').values()
        except Exception as ex:
            logger.info(f'История изменений по студенту {student} отсутствует', extra={'Exception': ex})
            history = 'Error'

        # all student marks
        marks = Result.objects.select_related().filter(
            students=student.student_id).filter(
            ~Q(groupsubject__subjects__form_control__exact='Зачет'))
        # all group results exclude non-nu,eric marks
        atts = GroupSubject.objects.select_related('subjects'
            ).filter(groups=student.group
            ).filter(~Q(subjects__form_control__exact='Зачет'))

        # calculation of the average ranking for semesters and the total
        rating_by_semester_bac = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0,
            6: 0,
            7: 0,
            8: 0,
        }
        rating_by_semester_mag = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
        }
        all_num_marks = []
        all_marks = []
        if student.level == Student.Level.BAC:
            semesters = range(1, 9)
            rating_by_semester = rating_by_semester_bac
        elif student.level == Student.Level.MAG:
            semesters = range(1, 5)
            rating_by_semester = rating_by_semester_mag

        for i in semesters:
            # all marks per semester
            sem_marks_all = marks.select_related('subjects').filter(
                groupsubject__subjects__semester__semester=i
            ).values('mark')
            # take only the last mark and exclude <ня> и <2>
            sem_marks = list(filter(lambda x: x not in ['ня', '2'], [i['mark'][-1] for i in sem_marks_all]))
            all_marks += sem_marks
            # quantity of groupsubjects with marks per semester
            num_atts = atts.filter(subjects__semester=i).count()
            all_num_marks.append(num_atts)
            # quantity of each mark <3 | 4 | 5>
            count_marks = dict(Counter(sem_marks))

            # calculate average ranking per semester
            if num_atts:
                sem_rating = round(sum([int(k)*v for k, v in count_marks.items()]) / num_atts, 2)
            else:
                sem_rating = 0

            rating_by_semester[i] = sem_rating

        # calculate total ranking
        if sum(all_num_marks):
            rating = round(sum(list(map(int, (all_marks)))) / sum(all_num_marks), 2)
        else:
            rating = 0

        marks = Result.objects.select_related().filter(students=student.student_id).order_by(
            'groupsubject__subjects__semester',
            '-groupsubject__subjects__form_control',
        )

        context = {
            'student': student,
            'history': history,
            'marks': marks,
            'rating': rating,
            'rating_by_semester': rating_by_semester
        }
        return render(request, 'students/student_detail.html', context=context)


class StudentRatingTableView(LoginRequiredMixin, ListView):
    """Head of table of the average ranking. Semesters"""
    def get(self, request):
        semesters = Semester.objects.all()
        groups = Group.objects.filter(is_archived=False)
        return render(request, 'students/students_rating.html', context={'semesters': semesters,
                                                                         'groups': groups})


class StudentRatingApiView(LoginRequiredMixin, View):
    """Расчет среднего балла студента."""

    def get(self, request):
        """Расчет среднего балла студента."""
        serialized_data = []
        sem_start = request.GET.get('semStart', '')
        sem_stop = request.GET.get('semStop', '')
        groups = request.GET.getlist('groups[]', False)

        if sem_start:
            start = sem_start
        else:
            start = 1

        if groups:
            students = Student.active_objects.select_related('group', 'semester', 'basis').filter(
                group__name__in=groups, semester__semester__gte=start)
        else:
            students = Student.active_objects.select_related(
                'group', 'semester', 'basis').filter(
                semester__semester__gte=start)

        flag_1 = not sem_start and not sem_stop
        flag_2 = sem_start and not sem_stop
        flag_3 = not sem_start and sem_stop
        flag_4 = sem_start and sem_stop == '-'

        if flag_1 or flag_2 or flag_3 or flag_4:
            logger.info(f'Расчет среднего балла за семестр {start} для студентов группы {groups}')
            # средний балл за указанный семестр. по умолчанию - за 1ый
            for student in students:
                rating = calculate_rating(student, start)

                serialized_data.append({
                    'studentId': student.student_id,
                    'fullname': student.fullname,
                    'group': student.group.name,
                    'currentSemester': student.semester.semester,
                    'basis': student.basis.name,
                    'level': student.level,
                    'rating': rating,
                    'isIll': student.is_ill,
                    'tag': student.tag,
                })
        else:
            logger.info(f'Расчет среднего балла за период с {start} по {stop} семестр для студентов группы {groups}')
            # средний балл за указанный период
            start, stop = sem_start, sem_stop

            for student in students:
                rating = calculate_rating(student, start, stop)

                serialized_data.append({
                    'studentId': student.student_id,
                    'fullname': student.fullname,
                    'group': student.group.name,
                    'currentSemester': student.semester.semester,
                    'basis': student.basis.name,
                    'level': student.level,
                    'rating': rating,
                    'isIll': student.is_ill,
                    'tag': student.tag,
                })

        serialized_data = sorted(serialized_data, key=lambda d: d['rating'])

        return JsonResponse({'data': serialized_data})


class StudentDeleteView(LoginRequiredMixin, DeleteView):
    """Удалить студента."""
    model = Student
    template_name = 'students/student_delete.html'
    success_url = '/students/'

    # переопределение ссылки на студента через номер зачетной книжки
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get(self.pk_url_kwarg)
        slug = self.kwargs.get(self.slug_url_kwarg)
        if pk is not None:
            queryset = queryset.filter(student_id=pk)

        if slug is not None and (pk is None or self.query_pk_and_slug):
            slug_field = self.get_slug_field()
            queryset = queryset.filter(**{slug_field: slug})

        if pk is None and slug is None:
            raise AttributeError(
                "Generic detail view %s must be called with either an object "
                "pk or a slug in the URLconf." % self.__class__.__name__
            )

        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj


class StudentUpdateView(LoginRequiredMixin, UpdateView):
    """Обновление информации о студенте."""
    model = Student
    form_class = StudentForm
    template_name = 'students/student_update.html'


def import_students(request):
    '''Импортировать студентов из CSV файла.'''
    logger.info('Импорт студентов')
    success = False
    errors = []  # список студентов, которые не были импортированы
    file_validation = date_validation = ''

    if request.method == 'POST':
        import_file = request.FILES['import_file'] if request.FILES else False

        # проверка, что файл выбран и формат файла CSV
        if not import_file or str(import_file).split('.')[-1] != 'csv':
            file_validation = False
            context = {'file_validation': file_validation}
            logger.error('Файл не выбран или неверный формат')
            return render(request, 'import/import_students.html', context)

        for n, line in enumerate(import_file):
            row = line.decode().strip().split(IMPORT_DELIMITER)
            if n == 0:
                pass
            else:
                if len(row[4]) == 2:
                    basis = row[4].upper()
                else:
                    basis = row[4].capitalize()
                is_basis = Basis.objects.filter(name=basis).exists()

                group = row[7]
                is_group = Group.objects.filter(name=group).exists()

                is_semester = Semester.objects.filter(id=row[8]).exists()

                citizenship = row[5].capitalize()
                is_citizenship = citizenship in list(map(lambda x: x[0], Student._meta.get_field('citizenship').choices))

                level = row[6].capitalize()
                is_level = level in list(map(lambda x: x[0], Student._meta.get_field('level').choices))

                raw_status = row[10].strip()
                if len(raw_status) == 5:
                    status = ' '.join(raw_status.split()[0].lower(), raw_status.split()[0].upper())
                else:
                    status = raw_status.capitalize()
                is_status = status in list(map(lambda x: x[0], Student._meta.get_field('status').choices))

                money = row[12]
                is_money = money in list(map(lambda x: x[0], Student._meta.get_field('money').choices))

                tag = row[11]
                is_tag = tag in list(map(lambda x: x[0], Student._meta.get_field('tag').choices)) + ['']

                if all([is_basis, is_group, is_semester, is_citizenship, is_level, is_status, is_tag, is_money]):
                    basis = Basis.objects.get(name=basis).id
                    group = Group.objects.get(name=group).id
                    semester = Semester.objects.get(id=row[8]).id
                else:
                    errors.append(f'[{n+1}] {row[1]} {row[2]} {row[3]}, номер: {row[0]}')
                    logger.error(f'Ошибка импорта студента: {row[1]} {row[2]} {row[3]}, номер: {row[0]}')
                    break

                # проверка формата даты зачисления
                pattern = r'^([0-9]{2})\.([0-9]{2})\.([0-9]{4})$'  # DD.MM.YYYY
                if not re.match(pattern, row[9]):
                    date_validation = False
                    logger.error(f'Неверный формат даты зачисления: {row[1]} {row[2]} {row[3]}, номер: {row[0]}')
                    break
                else:
                    # преобразование даты к формату поля модели
                    start_date = '-'.join(row[9].split('.')[::-1])

                try:
                    obj, created = Student.objects.get_or_create(
                        student_id=row[0],
                        defaults={
                            'last_name': row[1],
                            'first_name': row[2],
                            'second_name': row[3],
                            'basis_id': basis,
                            'citizenship': citizenship,
                            'level': level,
                            'group_id': group,
                            'semester_id': semester,
                            'start_date': start_date,
                            'status': status,
                            'tag': tag,
                            'money': money,
                        },
                    )
                    if not created:
                        errors.append(f'[{n+1}] {row[1]} {row[2]} {row[3]}, номер: {row[0]}')
                        logger.error(f'Не удалось создать объект студента: {row[1]} {row[2]} {row[3]}, номер: {row[0]}')
                except Exception as ex:
                    logger.error(f'Не удалось создать объект студента: {row[1]} {row[2]} {row[3]}, номер: {row[0]}', extra={'Exception': ex})
            if not errors:
                success = True

    context = {
        'file_validation': file_validation,
        'date_validation': date_validation,
        'errors': errors,
        'success': success,
    }
    return render(request, 'import/import_students.html', context)


def transfer_students(request):
    '''Перевести студентов на следующий семестр. В случае последнего семестра студент отправляется в <Архив> со сменой
    статуса на <Выпускник>.
    '''
    logger.info('Перевод студентов на следующий семестр')
    students_for_transfer = request.POST.getlist('checkedStudents[]', False)
    students_id = list(map(int, students_for_transfer))

    for st in students_id:
        student = Student.objects.get(student_id=st)
        current_semester = student.semester.semester
        level = student.level

        if (level == Student.Level.BAC and current_semester != 8) or (level == Student.Level.MAG and current_semester != 4):
            next_semester = current_semester + 1
            semester_obj = Semester.objects.get(semester=next_semester)
            student.semester = semester_obj
            student.save()
        else:
            # меняем статус студента на <Выпускник> и отправляем в <Архив>
            student.status = Student.Status.GRADUATED
            student.save()

    logger.info('Перевод студентов на следующий семестр успешно выполнен')
    return JsonResponse({"success": "Updated"})


class ResultCreateView(LoginRequiredMixin, CreateView):
    model = Result
    form_class = ResultForm
    template_name = 'students/result_add.html'

    def post(self, request, *args, **kwargs):
        student = request.POST['students'].replace('<option value=&quot;', '').split('&')[0]
        groupsubject = request.POST['groupsubjects'].replace('<option value=&quot;', '').split('&')[0]
        mark_0 = request.POST['mark_0']
        mark_1 = request.POST['mark_1']
        mark_2 = request.POST['mark_2']
        tag = request.POST['tag']

        form = ResultForm(data={'students': student,
                                'groupsubject': groupsubject,
                                'mark_0': mark_0,
                                'mark_1': mark_1,
                                'mark_2': mark_2,
                                'tag': tag})
        if form.is_valid():
            form.save()
            return redirect('groups:cards')

        return super().post(request, *args, **kwargs)


class ResultUpdateView(LoginRequiredMixin, UpdateView):
    model = Result
    form_class = ResultForm
    template_name = 'students/result_update.html'
    success_url = '/groups/cards'


class ResultDeleteView(LoginRequiredMixin, DeleteView):
    """Удалить оценку."""
    model = Result
    template_name = 'students/result_delete.html'
    success_url = '/groups/cards'


def import_results(request):
    '''Импортировать оценки из EXCEL файла.'''
    logger.info('Импорт оценок')
    success = False
    errors = []  # список студентов, по которым оценки не были импортированы

    if request.method == 'POST':
        import_files = request.FILES.getlist('import_file') if request.FILES else False

        # проверка выбора
        if not import_files:
            file_validation_exist = False
            context = {'file_validation_exist': file_validation_exist}
            return render(request, 'import/import_results.html', context)

        # проверка формата (xls)
        for file in import_files:
            if str(file).split('.')[-1] != 'xls':
                file_validation_format = False
                context = {'file_validation_format': file_validation_format}
                logger.error('Неверный формат файла')
                return render(request, 'import/import_results.html', context)

        semesters = {
            'первый': '1',
            'второй': '2',
            'третий': '3',
            'четвертый': '4',
            'пятый': '5',
            'шестой': '6',
            'седьмой': '7',
            'восьмой': '8',
        }
        types = {
            'Основная': 0,
            'Первая повторная аттестация': 1,
            'Вторая повторная аттестация': 2,
        }
        form_controls = {
            'зачет': 'Зачет',
            'дифференцированный зачет': 'Диффзачет',
            'курсовая работа': 'Курсовая работа',
            'курсовой проект': 'Курсовой проект',
        }
        marks = {
            'Не явился': 'ня',
            'Зачтено': 'зач',
            'Не зачтено': 'нз',
            'Отлично': '5',
            'Хорошо': '4',
            'Удовл.': '3',
            'Неудовл.': '2',
        }
        months = {
            'Января': 'january',
            'Февраля': 'february',
            'Марта': 'march',
            'Апреля': 'april',
            'Мая': 'may',
            'Июня': 'june',
            'Июля': 'july',
            'Августа': 'august',
            'Сентября': 'september',
            'Октября': 'october',
            'Ноября': 'november',
            'Декабря': 'december',
        }
        data = {
            'type': '',
            'semester': '',
            'group': '',
            'subject': '',
            'form_control': '',
            'cathedra': '',
            'zet': '',
            'teacher': '',
            'att_date': '',
            'marks': [],
        }

        # читаем файл
        for file in import_files:
            book = xlrd.open_workbook(file_contents=file.read())
            sheet = book.sheet_by_index(0)
            num_rows = sheet.nrows

            # формируем данные
            raw_data = []
            for n in range(num_rows):
                row_data = list(filter(lambda x: x != '', sheet.row_values(n)))
                if row_data:
                    raw_data.append(row_data)

            for i in range(len(raw_data)):
                if raw_data[i][0].lower().startswith('экзаменационная'):
                    data['form_control'] = 'Экзамен'
                    data['type'] = types.get(raw_data[i + 1][0], False)

                elif raw_data[i][0].lower().startswith('зачетная'):
                    data['form_control'] = form_controls.get(raw_data[i + 2][0].split('–')[-1].strip(), False)
                    data['type'] = types.get(raw_data[i + 1][0], False)

                elif raw_data[i][0].lower().startswith('учебный'):
                    data['semester'] = semesters.get(raw_data[i][3].split()[0].lower(), False)
                    data['group'] = raw_data[i][5][:-2]
                    data['subject'] = raw_data[i + 1][-1]
                    data['cathedra'] = raw_data[i + 2][1].capitalize()
                    data['zet'] = raw_data[i + 2][-1]

                    day = raw_data[i + 4][2]
                    month = raw_data[i + 4][4].strip()
                    year = '20' + str(int(raw_data[i + 4][6]))

                    raw_att_date = f'{year}-{months[month]}-{day}'
                    att_date = datetime.strptime(raw_att_date, '%Y-%B-%d')
                    data['att_date'] = att_date.date()

                elif raw_data[i][0].lower().startswith('фио'):
                    raw_teachers = raw_data[i][-1].split(', ')
                    teachers = []
                    for t in raw_teachers:
                        t = t.split()
                        if len(t) == 2:
                            teachers.append(f'{t[0]} {t[1][0]}.')
                        elif len(t) == 3:
                            teachers.append(f'{t[0]} {t[1][0]}.{t[2][0]}.')

                    data['teacher'] = ', '.join(teachers)

                elif raw_data[i][0].isdigit():
                    if data['form_control'] != 'Диффзачет':
                        st = raw_data[i][1:]
                        st = [st[0], st[1], marks.get(st[-1], False)]
                        if not check_mark(st[-1], data['form_control']):
                            check_mark_formcontrol = False
                            context = {'check_mark_formcontrol': check_mark_formcontrol}
                            logger.error('Оценки не соответствуют форме контроля')
                            return render(request, 'import/import_results.html', context)
                        data['marks'].append(st)
                    else:
                        st = []
                        st.extend(raw_data[i][1:3])
                        st.append(raw_data[i][-1])
                        st = [st[0], st[1], marks.get(st[-1], False)]
                        if not check_mark(st[-1], data['form_control']):
                            check_mark_formcontrol = False
                            context = {'check_mark_formcontrol': check_mark_formcontrol}
                            logger.error('Оценки не соответствуют форме контроля')
                            return render(request, 'import/import_results.html', context)
                        data['marks'].append(st)

            try:
                logger.info('Запись оценок в БД...')
                try:
                    group = Group.objects.get(name=data['group'])
                except Group.DoesNotExist:
                    errors.append(f'{file}: Ошибка группы - проверьте наименование или что группа существует.')
                    logger.error('Группа {0} отсутствует в БД'.format(data['group']))

                try:
                    subject = Subject.objects.filter(
                        Q(name=data['subject']) &
                        Q(form_control=data['form_control']) &
                        Q(semester=data['semester'])
                    )
                    if len(subject) > 1:
                        subject = Subject.objects.get(
                            Q(name=data['subject']) &
                            Q(form_control=data['form_control']) &
                            Q(cathedra=Cathedra.objects.get(name=data['cathedra'])) &
                            Q(semester=data['semester'])
                        )
                    else:
                        subject = Subject.objects.get(
                            Q(name=data['subject']) &
                            Q(form_control=data['form_control']) &
                            Q(semester=data['semester'])
                        )
                except Subject.DoesNotExist:
                    errors.append(f'{file}: Ошибка дисциплины - проверьте наименование или что дисциплина существует.')
                    logger.error('Предмет {0} отсутствует в БД'.format(data['subject']))

                if not subject.cathedra:
                    subject.cathedra.name = Cathedra.objects.get(name=data['cathedra'])
                    subject.save()
                if data['form_control'] not in ['Курсовая работа', 'Курсовой проект'] and not subject.zet:
                    subject.zet = data['zet']
                    subject.save()
                else:
                    if data['form_control'] == 'Курсовая работа':
                        subject.zet = 'КР'
                        subject.save()
                    if data['form_control'] == 'Курсовой проект':
                        subject.zet = 'КП'
                        subject.save()

                try:
                    groupsubject = GroupSubject.objects.get(Q(groups=group) & Q(subjects=subject))
                except GroupSubject.DoesNotExist:
                    errors.append(f'{file}: Ошибка назначения - проверьте, что назначение существует.')
                    logger.error(f'Назначение предмета {subject} группе {group} отсутствует в БД')

                if not groupsubject.teacher:
                    groupsubject.teacher = data['teacher']
                    groupsubject.save()
                if not groupsubject.att_date:
                    groupsubject.att_date = data['att_date']
                    groupsubject.save()

                for item in data['marks']:
                    logger.info('Поиск студентов в БД по номеру зачетной книжки')
                    try:
                        student = Student.objects.get(student_id=int(item[1]))
                    except Student.DoesNotExist:
                        errors.append(f'{file}: ID студента [{item[0]}] в ведомости не корректно.')
                        logger.error('Студент {0} отсутствует в БД'.format(item[0]))

                    sheet_type = data['type']
                    match sheet_type:
                        case 0:
                            try:
                                result = Result.objects.get(students=student, groupsubject=groupsubject)
                                result.mark = [item[-1]]
                                result.save()
                            except Result.DoesNotExist:
                                result = Result.objects.create(students=student, groupsubject=groupsubject, mark=[item[-1]])
                                result.save()
                        case 1:
                            try:
                                result = Result.objects.get(students=student, groupsubject=groupsubject)
                                result.mark[1] = item[-1]
                                result.save()
                            except IndexError:
                                result.mark.append(item[-1])
                                validation = validate_mark(result.mark)
                                if validation == True:
                                    result.save()
                                else:
                                    errors.append(f'{file}: {student.fullname}: {validation[-1]}')
                                    logger.error(f'Оценка не проходит валидацию. {file}: {student.fullname}: {validation[-1]}')
                        case 2:
                            try:
                                result = Result.objects.get(students=student, groupsubject=groupsubject)
                                result.mark[2] = item[-1]
                                result.save()
                            except IndexError:
                                result.mark.append(item[-1])
                                validation = validate_mark(result.mark)
                                if validation == True:
                                    result.save()
                                else:
                                    errors.append(f'{file}: {student.fullname}: {validation[-1]}')
                                    logger.error(f'Оценка не проходит валидацию. {file}: {student.fullname}: {validation[-1]}')
                if not errors:
                    success = True
                logger.info('Запись оценок в БД успешно выполнена')

            except Exception as ex:
                logger.error(f'Запись оценок из файла {file} в БД не удалась', extra={'Exception': ex})

    context = {'errors': errors, 'success': success}

    return render(request, 'import/import_results.html', context)


class StudentsMoneyListView(LoginRequiredMixin, ListView):
    """Отобразить студентов с указанием стипендии."""
    model = Student
    template_name = 'students/students_money.html'
    queryset = Student.active_objects.select_related('basis', 'group', 'semester')


class StudentsDebtsListView(LoginRequiredMixin, ListView):
    """Отобразить задолженности всех студентов."""
    model = Student
    template_name = 'students/students_debts.html'

    def get_queryset(self):
        negative = ['ня', 'нз', '2']

        # id всех студентов с отрицательными оценками
        negative_students = Result.objects.select_related('students').filter(
            mark__contained_by=negative, is_archived=False).values('students__student_id')
        # студенты
        students = Student.active_objects.select_related(
            'basis', 'group', 'semester').filter(
            student_id__in=negative_students)

        for st in students:
            all_marks = [
                i[0]
                for i in st.result_set.select_related().filter(
                    groupsubject__subjects__semester__semester=st.semester.semester, groupsubject__groups__name=st.group.name,
                    mark__contained_by=negative).values_list('mark')]
            marks_att1 = [i[0] for i in all_marks]
            marks_att2 = [i[1] for i in list(filter(lambda x: len(x) in [2, 3], all_marks))]
            marks_att3 = [i[2] for i in list(filter(lambda x: len(x) == 3, all_marks))]
            count_marks_att1 = dict(Counter(marks_att1))
            count_marks_att2 = dict(Counter(marks_att2))
            count_marks_att3 = dict(Counter(marks_att3))
            st.att1 = sum(list(map(lambda x: count_marks_att1.get(x, 0), negative)))
            st.att2 = sum(list(map(lambda x: count_marks_att2.get(x, 0), negative)))
            st.att3 = sum(list(map(lambda x: count_marks_att3.get(x, 0), negative)))

        return students


def search_results(request):
    if request.method == 'GET':
        search = request.GET.get('search')
        search_query = SearchQuery(search)

        search_vector_stu = SearchVector('student_id', 'last_name', 'first_name', 'second_name', 'comment')
        result_students = Student.objects.annotate(
            search=search_vector_stu, rank=SearchRank(search_vector_stu, search_query)
            ).filter(search=search_query).order_by("-rank")

        search_vector_sub = SearchVector('name', 'cathedra', 'comment')
        result_subjects = Subject.objects.annotate(
            search=search_vector_sub, rank=SearchRank(search_vector_sub, search_query)
            ).filter(search=search_query).order_by("-rank")

        context = {
            'search': search,
            'students': result_students,
            'subjects': result_subjects,
        }

    return render(request, 'search_results.html', context=context)


def download_excel_data(request):
    negative = ['ня', 'нз', '2']
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Zadolzhennosti FIEGH.xlsx"'

    att_level = request.GET.get('att')
    logger.info(f'Формирование excel файла с задолженностями за {att_level} период аттестации...')

    # id всех назначений с отрицательными оценками
    match att_level:
        case 'att1':
            negative_groupsubjects_ids = Result.objects.select_related().filter(
                mark__0__in=negative).values('groupsubject__id')
        case 'att2':
            negative_groupsubjects_ids = Result.objects.select_related().filter(
                mark__1__in=negative).values('groupsubject__id')
        case 'att3':
            negative_groupsubjects_ids = Result.objects.select_related().filter(
                mark__2__in=negative).values('groupsubject__id')

    if not negative_groupsubjects_ids:
        url = reverse('students:debts')
        logger.info(f'Задолженностей за {att_level} период аттестации нет')
        return HttpResponseRedirect(url)
    else:
        # назначения
        group_subjects = GroupSubject.active_objects.select_related().filter(id__in=negative_groupsubjects_ids)
        
        # кафедры
        cathedras = list(set(group_subjects.values_list('subjects__cathedra__short_name', flat=True)))

        # создаем файл
        book = Workbook()
        # названия столбцов заголовка
        header = ['Дисциплина', 'Форма контроля', 'Группа', 'Семестр', 'Преподаватель', 'Студенты']

        for cathedra in cathedras:
            # создаем лист с названием = аббревиатура кафедры и делаем активным
            book.create_sheet(title=cathedra, index=None)
            sheet = book[cathedra]
            sheet.column_dimensions['A'].width = 75
            sheet.column_dimensions['B'].width = 20
            sheet.column_dimensions['C'].width = 15
            sheet.column_dimensions['D'].width = 15
            sheet.column_dimensions['E'].width = 30
            sheet.column_dimensions['F'].width = 150
            sheet.auto_filter.ref = 'A1:F1'

            # записываем заголовок на лист
            for col in range(1, len(header) + 1):
                cell = sheet.cell(row=1, column=col, value=header[col - 1])
                sheet[cell.coordinate].font = Font(bold=True, size=14)

            # назначения по кафедре
            cathedra_group_subjects = group_subjects.filter(subjects__cathedra__short_name=cathedra)

            row = 2
            for gs in cathedra_group_subjects:
                # отрицательные результаты по каждому назначению кафедры
                match att_level:
                    case 'att1':
                        res = gs.result_set.select_related().filter(mark__0__in=negative)
                    case 'att2':
                        res = gs.result_set.select_related().filter(mark__1__in=negative)
                    case 'att3':
                        res = gs.result_set.select_related().filter(mark__2__in=negative)

                # фио студентов-должников по назначению
                students = res.values_list('students__last_name', 'students__first_name', 'students__second_name')
                students = ', '.join([' '.join(i) for i in students])
                res_data = [
                    gs.subjects.name,
                    gs.subjects.form_control,
                    gs.groups.name,
                    gs.subjects.semester.semester,
                    gs.teacher,
                ]
                res_data.append(students)

                for col, data in enumerate(res_data):
                    sheet.cell(row=row, column=col + 1, value=data)
                    sheet.cell(row=row, column=col + 1).font = Font(size=12)
                row += 1

        # добавляем оглавление
        sheet = book['Sheet']
        sheet.title = 'Оглавление'
        sheet.column_dimensions['A'].width = 200

        sheets = book.sheetnames
        sheets = sheets[1:]
        row = 1
        for sh in sheets:
            link = f'#{sh}!A1'
            sheet.cell(row=row, column=1, value=Cathedra.objects.get(short_name=sh).name).hyperlink = link
            sheet.cell(row=row, column=1).font = Font(size=14)
            row += 1

        book.save(response)
        logger.info(f'Файл с задолженностями за {att_level} период аттестации успешно сформирован')
        return response
