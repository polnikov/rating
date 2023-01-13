import re
import xlrd

from collections import Counter
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView, View
)

from groups.models import Group
from students.forms import ResultForm, StudentForm
from students.models import Basis, Result, Semester, Student, StudentLog
from students.validators import validate_mark
from subjects.models import Cathedra, GroupSubject, Subject

from rating.settings import IMPORT_DELIMITER


class StudentListView(LoginRequiredMixin, ListView):
    """Отобразить всех студентов."""
    model = Student
    template_name = 'students/students.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        students = Student.objects.select_related('group', 'semester').filter(is_archived=False).order_by(
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
        graduates = Student.objects.select_related('group', 'semester').filter(is_archived=True, status='Выпускник')
        context['graduates'] = graduates
        return context


class StudentCreateView(LoginRequiredMixin, CreateView):
    """Добавить нового студента."""
    model = Student
    form_class = StudentForm
    template_name = 'students/student_add.html'
    success_url = '/students/'


class StudentDetailView(LoginRequiredMixin, DetailView):
    """Сводная информация о студенте и история изменений по нему."""
    model = Student

    def get(self, request, pk, **kwargs):
        student = Student.objects.select_related('group', 'semester', 'basis').get(student_id__exact=pk)

        try:
            history = StudentLog.objects.select_related('user').filter(
                record_id=student.student_id).order_by('-timestamp').values()
        except:
            history = 'Error'

        # все оценки студента
        marks = Result.objects.select_related().filter(
            students=student.student_id).filter(
            ~Q(groupsubject__subjects__form_control__exact='Зачет'))
        # все аттестации для данного направления (группы), исключая зачеты
        atts = GroupSubject.objects.select_related('subjects').filter(
            groups=student.group,
            is_archived=False
        ).filter(~Q(subjects__form_control__exact='Зачет'))

        # вычисление среднего балла по семестрам и суммарного
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
        if student.level == 'Бакалавриат':
            semesters = range(1, 9)
            rating_by_semester = rating_by_semester_bac
        elif student.level == 'Магистратура':
            semesters = range(1, 5)
            rating_by_semester = rating_by_semester_mag

        for i in semesters:
            # все оценки за семестр
            sem_marks_all = marks.select_related('subjects').filter(
                groupsubject__subjects__semester__semester=i
            ).values('mark')
            # берем только последнюю оценку и исключаем <ня> и <2>
            sem_marks = list(filter(lambda x: x not in ['ня', '2'], [i['mark'][-1] for i in sem_marks_all]))
            all_marks += sem_marks
            # количество аттестаций с оценками в семестре
            num_atts = atts.filter(subjects__semester=i).count()
            all_num_marks.append(num_atts)
            # количество каждой из оценок <3 | 4 | 5>
            count_marks = dict(Counter(sem_marks))
            # определяем средний балл за семестр
            try:
                sem_rating = round(sum([int(k)*v for k, v in count_marks.items()]) / num_atts, 2)
            except ZeroDivisionError:
                sem_rating = 0
            rating_by_semester[i] = sem_rating

        # определяем суммарный средний балл
        try:
            rating = round(sum(list(map(int, (all_marks)))) / sum(all_num_marks), 2)
        except ZeroDivisionError:
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
    """Отображение шапки таблицы среднего балла студентов и вывод семестров."""
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
                students = Student.objects.select_related('group', 'semester', 'basis').filter(
                    is_archived=False, group__name__in=groups, semester__semester__gte=start)
        else:
            students = Student.objects.select_related(
                'group', 'semester', 'basis').filter(
                is_archived=False, semester__semester__gte=start)

        flag_1 = not sem_start and not sem_stop
        flag_2 = sem_start and not sem_stop
        flag_3 = not sem_start and sem_stop
        flag_4 = sem_start and sem_stop == '-'

        if flag_1 or flag_2 or flag_3 or flag_4:
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
    success = False
    errors = []  # список студентов, которые не были импортированы
    file_validation = date_validation = ''

    if request.method == 'POST':
        import_file = request.FILES['import_file'] if request.FILES else False

        # проверка, что файл выбран и формат файла CSV
        if not import_file or str(import_file).split('.')[-1] != 'csv':
            file_validation = False
            context = {'file_validation': file_validation}
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
                    print('[!] ---> Ошибка импорта студента:', [is_basis, is_group, is_semester, is_citizenship, is_level, is_status, is_tag, is_money])
                    errors.append(f'[{n+1}] {row[1]} {row[2]} {row[3]}, номер: {row[0]}')
                    break

                # проверка формата даты зачисления
                pattern = r'^([0-9]{2})\.([0-9]{2})\.([0-9]{4})$'  # DD.MM.YYYY
                if not re.match(pattern, row[9]):
                    date_validation = False
                    print('[!] ---> Неверный формат даты зачисления.')
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
                except Exception as import_students_error:
                    print('[!] ---> Ошибка импорта студента:', import_students_error, sep='\n')
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
    students_for_transfer = request.POST.getlist('checkedStudents[]', False)
    students_id = list(map(int, students_for_transfer))

    for st in students_id:
        student = Student.objects.get(student_id=st)
        current_semester = student.semester.semester
        level = student.level

        if (level == 'Бакалавриат' and current_semester != 8) or (level == 'Магистратура' and current_semester != 4):
            next_semester = current_semester + 1
            semester_obj = Semester.objects.get(semester=next_semester)
            student.semester = semester_obj
            student.save()
        else:
            # меняем статус студента на <Выпускник> и отправляем в <Архив>
            student.status = 'Выпускник'
            student.is_archived = True
            student.save()

    return JsonResponse({"success": "Updated"})

########################################################################################################################


class ResultListView(LoginRequiredMixin, ListView):
    """Отобразить все оценки."""
    model = Result
    template_name = 'students/results.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        results = Result.objects.select_related().filter(students__is_archived=False).order_by(
            '-groupsubject__subjects__att_date')
        context['result_list'] = results
        results_by_request = Result.objects.select_related().filter(students__is_archived=False, tag='СЗ').order_by(
            'groupsubject__subjects__teacher')
        context['results_by_request'] = results_by_request
        return context


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
            return redirect('students:results')

        return super().post(request, *args, **kwargs)


class ResultUpdateView(LoginRequiredMixin, UpdateView):
    model = Result
    form_class = ResultForm
    template_name = 'students/result_update.html'
    success_url = '/students/results'


class ResultDeleteView(LoginRequiredMixin, DeleteView):
    """Удалить оценку."""
    model = Result
    template_name = 'students/result_delete.html'
    success_url = '/students/results'


def import_results(request):
    '''Импортировать оценки из EXCEL файла.'''
    success = False
    errors = []  # список студентов, по которым оценки не были импортированы

    if request.method == 'POST':
        import_file = request.FILES['import_file'] if request.FILES else False
        # проверка, что файл выбран и формат файла xls
        if not import_file or str(import_file).split('.')[-1] != 'xls':
            file_validation = False
            context = {'file_validation': file_validation}
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
        book = xlrd.open_workbook(file_contents=import_file.read())
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
                    data['marks'].append(st)
                else:
                    st = []
                    st.extend(raw_data[i][1:3])
                    st.append(raw_data[i][-1])
                    st = [st[0], st[1], marks.get(st[-1], False)]
                    data['marks'].append(st)

        try:
            try:
                group = Group.objects.get(name=data['group'])
            except Group.DoesNotExist:
                errors.append('Ошибка группы - проверьте наименование или что группа существует.')

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
            except Subject.DoesNotExist:
                errors.append('Ошибка дисциплины - проверьте наименование или что дисциплина существует.')

            if not subject.cathedra:
                subject.cathedra = Cathedra.objects.get(name=data['cathedra'])
                subject.save()
            if data['form_control'] not in ['Курсовая работа', 'Курсовой проект'] and not subject.zet:
                subject.zet = data['zet']
                subject.save()

            try:
                groupsubject = GroupSubject.objects.get(Q(groups=group) & Q(subjects=subject))
            except GroupSubject.DoesNotExist:
                errors.append('Ошибка назначения - проверьте, что назначение существует.')

            if not groupsubject.teacher:
                groupsubject.teacher = data['teacher']
                groupsubject.save()
            if not groupsubject.att_date:
                groupsubject.att_date = data['att_date']
                groupsubject.save()

            for item in data['marks']:
                try:
                    student = Student.objects.get(student_id=int(item[1]))
                except Student.DoesNotExist:
                    errors.append(f'ID студента [{item[0]}] в ведомости не корректно.')

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
                                errors.append(f'{student.fullname}: {validation[-1]}')
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
                                errors.append(f'{student.fullname}: {validation[-1]}')
            if not errors:
                success = True

        except Exception as ex:
            print('----- ERROR >>>', ex)

    context = {'errors': errors, 'success': success}

    return render(request, 'import/import_results.html', context)

########################################################################################################################


class StudentsMoneyListView(LoginRequiredMixin, ListView):
    """Отобразить студентов с указанием стипендии."""
    model = Student
    template_name = 'students/students_money.html'
    queryset = Student.objects.select_related('basis', 'group', 'semester').filter(is_archived=False)

########################################################################################################################


class StudentsDebtsListView(LoginRequiredMixin, ListView):
    """Отобразить задолженности всех студентов."""
    model = Student
    template_name = 'students/students_debts.html'

    def get_queryset(self):
        negative = ['ня', 'нз', '2']

        # id всех студентов с отрицательными оценками
        negative_students = Result.objects.select_related('students').filter(
            mark__contained_by=negative).values('students__student_id')
        # студенты
        students = Student.objects.select_related(
            'basis', 'group', 'semester').filter(
            is_archived=False, student_id__in=negative_students)

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

########################################################################################################################


def calculate_rating(student, start, stop=False):
    '''Рассчитать средний балл студента за семестр или период.'''
    if start and stop:
        # все оценки студента за указанный период
        marks = Result.objects.select_related().filter(
            students=student.student_id).filter(
            Q(groupsubject__subjects__semester__semester__gte=start) &
            Q(groupsubject__subjects__semester__semester__lte=stop)).filter(
            ~Q(groupsubject__subjects__form_control__exact='Зачет')).values('mark')
        # все аттестации для данного направления (группы) в указанном семестре, исключая зачеты
        atts = GroupSubject.objects.select_related('subjects').filter(
            groups=student.group,
            is_archived=False
        ).filter(Q(subjects__semester__semester__gte=start) & Q(subjects__semester__semester__lte=stop)
        ).filter(~Q(subjects__form_control__exact='Зачет'))
    elif start and not stop:
        # все оценки студента в указанном семестре
        marks = Result.objects.select_related().filter(
            students=student.student_id,
            groupsubject__subjects__semester__semester=start
        ).filter(~Q(groupsubject__subjects__form_control__exact='Зачет')).values('mark')
        # все аттестации для данного направления (группы) в указанном семестре, исключая зачеты
        atts = GroupSubject.objects.select_related('subjects').filter(
            groups=student.group,
            subjects__semester__semester=start,
            is_archived=False
        ).filter(~Q(subjects__form_control__exact='Зачет'))

    # вычисление среднего балла за семестр или период
    # берем только последнюю оценку и исключаем <ня> и <2>
    marks = list(filter(lambda x: x not in ['ня', '2'], [i['mark'][-1] for i in marks]))
    # количество аттестаций с оценками в семестре или за период
    num_atts = atts.count()
    # количество каждой из оценок <3 | 4 | 5>
    count_marks = dict(Counter(marks))
    try:
        rating = round(sum([int(k)*v for k, v in count_marks.items()]) / num_atts, 2)
    except ZeroDivisionError:
        rating = 0

    return rating

########################################################################################################################


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

        search_vector_grsub = SearchVector('teacher', 'comment')
        result_groupsubjects = GroupSubject.objects.annotate(
            search=search_vector_grsub, rank=SearchRank(search_vector_grsub, search_query)
            ).filter(search=search_query).order_by("-rank")

        context = {
            'search': search,
            'students': result_students,
            'subjects': result_subjects,
            'groupsubjects': result_groupsubjects,
        }

    return render(request,'search_results.html', context=context)

