from api import serializers
import xlrd
import re
import logging
from datetime import datetime
from collections import Counter

from rest_framework import generics, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from django.http.response import JsonResponse
from django.shortcuts import render
from django.db.models import Q, F
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

from groups.models import Group
from groups.forms import GroupForm
from subjects.forms import FacultyForm, CathedraForm
from students.models import Result, Semester, Student, StudentLog, Basis
from students.validators import validate_mark, check_mark
from subjects.models import Cathedra, Faculty, GroupSubject, Subject, SubjectLog

from rating.settings import IMPORT_DELIMITER
from rating.functions import _get_students_group_statistic_and_marks, calculate_rating


logger = logging.getLogger(__name__)


# Students
class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = serializers.StudentSerializer


class StudentLogList(generics.ListAPIView):
    queryset = StudentLog.objects.all()
    serializer_class = serializers.StudentLogSerializer


class StudentMoneyList(generics.ListAPIView):
    queryset = Student.active_objects.select_related('basis', 'group', 'semester')
    serializer_class = serializers.StudentMoneySerializer


@api_view(['GET'])
def transfer_students(request):
    '''Перевести студентов на следующий семестр. В случае последнего семестра студент отправляется в <Архив> со сменой
    статуса на <Выпускник>.
    '''
    logger.info('API: Перевод студентов на следующий семестр...')
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


@api_view(['POST'])
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


# @api_view(['GET'])
def student_rating(request):
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


# Results
class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = serializers.ResultSerializer


def import_results(request):
    '''Import results from EXCEL file | files.'''
    logger.info('Импорт оценок...')
    serialized_data = []
    success = False
    errors = []  # list of students with non-imported results

    if request.method == 'POST':
        import_files = request.FILES.getlist('import_files') if request.FILES else False

        # checking that the file has been selected
        if not import_files:
            serialized_data.append({'error': 'file_validation_exist', 'success': success})
            logger.error('Файл не выбран')
            return JsonResponse({'data': serialized_data})

        # checking file format (xls)
        for import_file in import_files:
            if str(import_file).split('.')[-1] != 'xls':
                serialized_data.append({'error': 'file_validation_format', 'success': success})
                logger.error('Неверный формат файла')
                return JsonResponse({'data': serialized_data})

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
            'Удовлетворительно': '3',
            'Неудовл.': '2',
            'Неудовлетворительно': '2',
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

        # read file
        for import_file in import_files:
            book = xlrd.open_workbook(file_contents=import_file.read())
            sheet = book.sheet_by_index(0)
            num_rows = sheet.nrows

            # extract needed lines
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
                            serialized_data.append({'error': 'check_mark_formcontrol'})
                            logger.error('Оценки не соответствуют форме контроля')
                            return JsonResponse({'data': serialized_data})
                        data['marks'].append(st)
                    else:
                        st = []
                        st.extend(raw_data[i][1:3])
                        st.append(raw_data[i][-1])
                        st = [st[0], st[1], marks.get(st[-1], False)]
                        if not check_mark(st[-1], data['form_control']):
                            serialized_data.append({'error': 'check_mark_formcontrol'})
                            logger.error('Оценки не соответствуют форме контроля')
                            return JsonResponse({'data': serialized_data})
                        data['marks'].append(st)

            # write data to DB
            try:
                logger.info('|---> Запись оценок в БД...')
                try:
                    group = Group.objects.get(name=data['group'])
                except Group.DoesNotExist:
                    errors.append(f'{import_file}: Ошибка группы - проверьте наименование или что группа существует.')
                    logger.error('|---> Группа {0} отсутствует в БД'.format(data['group']))

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
                    errors.append(f'{import_file}: Ошибка дисциплины - проверьте наименование или что дисциплина существует.')
                    logger.error('|---> Предмет {0} отсутствует в БД'.format(data['subject']))

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
                    errors.append(f'{import_file}: Ошибка назначения - проверьте, что назначение существует.')
                    logger.error(f'|---> Назначение предмета {subject} группе {group} отсутствует в БД')

                if not groupsubject.teacher:
                    groupsubject.teacher = data['teacher']
                    groupsubject.save()
                if not groupsubject.att_date:
                    groupsubject.att_date = data['att_date']
                    groupsubject.save()

                for item in data['marks']:
                    logger.info('|---> Поиск студентов в БД по номеру зачетной книжки')
                    try:
                        student = Student.objects.get(student_id=int(item[1]))
                    except Student.DoesNotExist:
                        errors.append(f'{import_file}: ID студента [{item[0]}] в ведомости не корректно.')
                        logger.error('|---> Студент {0} отсутствует в БД'.format(item[0]))

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
                                    errors.append(f'{import_file}: {student.fullname}: {validation[-1]}')
                                    logger.error(f'|---> Оценка не проходит валидацию. {import_file}: {student.fullname}: {validation[-1]}')
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
                                    errors.append(f'{import_file}: {student.fullname}: {validation[-1]}')
                                    logger.error(f'|---> Оценка не проходит валидацию. {import_file}: {student.fullname}: {validation[-1]}')
                if not errors:
                    success = True
                logger.info('|---> Запись оценок в БД успешно выполнена')
            except Exception as ex:
                logger.error(f'|---> Запись оценок из файла {import_file} в БД не удалась', extra={'Exception': ex})

    serialized_data.append({'errors': errors, 'success': success})
    return JsonResponse({'data': serialized_data})


# Groups
class GroupsViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.filter(is_archived=False)
    serializer_class = serializers.GroupSerializer


    def get_queryset(self):
        if self.request.GET.get('is_archived') == 'true':
            return Group.objects.filter(is_archived=True)
        return super().get_queryset()


    def retrieve(self, request, pk=None):
        queryset = Group.objects.all()

        try:
            group = queryset.get(id=pk)
        except Group.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Group not found'}, status=404)

        serializer = self.get_serializer(group)
        return Response(serializer.data)


    @action(methods=['post'], detail=False)
    def create_group(self, request):
        form = GroupForm(request.data)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=201)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['patch'], detail=True)
    def update_group(self, request, pk=None):
        try:
            group = Group.objects.get(id=pk)
        except Group.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Group not found'}, status=404)

        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=200)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['delete'], detail=True)
    def delete_group(self, request, pk=None):
        queryset = Group.objects.all()

        try:
            group = queryset.get(id=pk)
        except Group.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Group not found'}, status=404)

        group.delete()
        return JsonResponse({'success': True}, status=201)


# @api_view(['GET', 'POST'])
def group_marks(request):
    '''Статистика и оценки студентов группы.'''
    if request.method == 'GET':
        groupname = request.GET.get('groupname', '')
        semester = request.GET.get('semester', '')
        logger.info(f'API ---> Запрос статистики и оценок группы {groupname} за {semester} семестр...')
        students = _get_students_group_statistic_and_marks(groupname, semester)

        data = []
        for m in students:
            # {groupsubject_id: [subject_id, form_control, result_id, [оценки]]}
            marks_data = [{k[0]:[k[1], k[2], v[0] if v != '-' else v, v[-1] if v != '-' else v]} for k, v in m.marks.items()]

            data.append({
                'studentId': m.student_id,
                'money': m.money,
                'att1': m.att1,
                'att2': m.att2,
                'att3': m.att3,
                'marks': marks_data,
                'passSession': m.pass_session,
            })

        # итоговая структура оценок [student.marks]
        # (groupsubject_id, subject_id, form_control): '-'
        # (groupsubject_id, subject_id, form_control): (result_id, [оценки])

        return JsonResponse({'data': data})

    if request.method == 'POST':
        # обработка оценок
        result_id = request.POST.get('resId', '')
        student_id = request.POST.get('studentId', '')
        groupsub_id = request.POST.get('groupSubId', '')
        form = request.POST.get('form', '')
        value = request.POST.get('value', '')
        group_name = request.POST.get('groupName', '')
        semester = request.POST.get('semester', '')
        logger.info(f'API ---> Запись оценок группы {group_name} за {semester} семестр...')

        # преобразуем строку с оценками в список
        # валидация оценок осуществляется на front-end
        marks = value.split()

        # проверяем, что это первая оценка
        if result_id == '-':
            student = Student.objects.get(student_id=int(student_id))
            groupsubject = GroupSubject.objects.get(id=int(groupsub_id))
            result = Result.objects.create(
                students=student,
                groupsubject=groupsubject,
                mark=marks,
            )
        else:
            is_result = Result.objects.filter(id=result_id).exists()
            if is_result:
                result = Result.objects.get(id=result_id)
                result.mark = marks
                result.save()

        # обработка изменения статистики студента
        statistic = _get_students_group_statistic_and_marks(group_name, semester, student_id)

        return JsonResponse({
            'success': 'Saved/Updated',
            'newResId': result.id,
            'money': statistic[0],
            'att1': statistic[1],
            'att2': statistic[2],
            'att3': statistic[3],
            'passSession': statistic[4],
        })


# @api_view(['GET'])
def students_debts(request):
    """Отобразить задолженности всех студентов."""
    data = []
    negative = ['ня', 'нз', '2']

    # id всех студентов с отрицательными оценками
    negative_students = Result.objects.select_related('students').filter(
        mark__contained_by=negative).values('students__student_id')
    # студенты
    students = Student.active_objects.select_related('basis', 'group', 'semester').filter(student_id__in=negative_students)

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
        data.append({
            'student_id': st.student_id,
            'fullname': st.fullname,
            'group': st.group.name,
            'semester': st.semester.semester,
            'basis': st.basis.name,
            'debts': {
                'att1': st.att1,
                'att3': st.att2,
                'att2': st.att3,
            },
        })

    return JsonResponse({'data': data})


# Faculties
class FacultyViewSet(viewsets.ModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = serializers.FacultySerializer


    @action(methods=['post'], detail=False)
    def create_faculty(self, request):
        form = FacultyForm(request.data)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=201)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['patch'], detail=True)
    def update_faculty(self, request, pk=None):
        try:
            faculty = Faculty.objects.get(id=pk)
        except Faculty.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Faculty not found'}, status=404)

        form = FacultyForm(request.POST, instance=faculty)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=200)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['delete'], detail=True)
    def delete_faculty(self, request, pk=None):
        queryset = Faculty.objects.all()

        try:
            faculty = queryset.get(id=pk)
        except Faculty.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Faculty not found'}, status=404)

        faculty.delete()
        return JsonResponse({'success': True}, status=201)


# Cathedras
class CathedraViewSet(viewsets.ModelViewSet):
    queryset = Cathedra.objects.all()
    serializer_class = serializers.CathedraSerializer


    @action(methods=['post'], detail=False)
    def create_cathedra(self, request):
        form = CathedraForm(request.data)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=201)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['patch'], detail=True)
    def update_cathedra(self, request, pk=None):
        try:
            cathedra = Cathedra.objects.get(id=pk)
        except Cathedra.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Cathedra not found'}, status=404)

        form = CathedraForm(request.POST, instance=cathedra)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=200)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['delete'], detail=True)
    def delete_cathedra(self, request, pk=None):
        queryset = Cathedra.objects.all()

        try:
            cathedra = queryset.get(id=pk)
        except Cathedra.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Cathedra not found'}, status=404)

        cathedra.delete()
        return JsonResponse({'success': True}, status=201)


def import_cathedras(request):
    '''Import cathedras from CSV file.'''
    logger.info('Импорт кафедр...')
    serialized_data = []
    success = False
    errors = []  # list of non-imported cathedras

    if request.method == 'POST':
        import_file = request.FILES['import_files'] if request.FILES else False

        # checking that the file has been selected and its format is CSV
        if not import_file or str(import_file).split('.')[-1] != 'csv':
            serialized_data.append({'error': 'file_validation', 'success': success})
            logger.error('Файл не выбран или неверный формат')
            return JsonResponse({'data': serialized_data})

        try:
            for n, line in enumerate(import_file):
                row = line.decode().strip().split(IMPORT_DELIMITER)
                if n == 0:
                    pass
                else:
                    is_faculty = Faculty.objects.filter(short_name=row[2]).exists()
                    if not is_faculty:
                        faculty = ''
                    else:
                        faculty = Faculty.objects.get(short_name=row[2]).id

                    if row[0].startswith('"'):
                        row[0] = row[0].replace('"', "")

                    obj, created = Cathedra.objects.get_or_create(
                        name=row[0],
                        defaults={
                            'short_name': row[1],
                            'faculty_id': faculty,
                        }
                    )
                    if not created:
                        errors.append(f'[{n+1}] {row[0]} {row[1]}')
            if not errors:
                success = True
            logger.info('|---> Запись кафедр в БД успешно выполнена')

        except Exception as import_cathedras_error:
            print('[!] ---> Ошибка импорта кафедр:', import_cathedras_error, sep='\n')

    serialized_data.append({'errors': errors, 'success': success})
    return JsonResponse({'data': serialized_data})


# Subjects
class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = serializers.SubjectSerializer


class SubjectLogList(generics.ListAPIView):
    queryset = SubjectLog.objects.all()
    serializer_class = serializers.SubjectLogSerializer


# GroupSubjects
class GroupSubjectViewSet(viewsets.ModelViewSet):
    queryset = GroupSubject.objects.all()
    serializer_class = serializers.GroupSubjectSerializer


# Semesters
class SemesterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Semester.objects.all()
    serializer_class = serializers.SemesterSerializer


# Search
# @api_view(['GET'])
def search(request):
    if request.method == 'GET':
        search = request.GET.get('search')
        search_query = SearchQuery(search)

        search_vector_stu = SearchVector('student_id', 'last_name', 'first_name', 'second_name')
        result_students = Student.objects.annotate(
            search=search_vector_stu, rank=SearchRank(search_vector_stu, search_query)
            ).filter(search=search_query).order_by("-rank")

        search_vector_sub = SearchVector('name', 'cathedra')
        result_subjects = Subject.objects.annotate(
            search=search_vector_sub, rank=SearchRank(search_vector_sub, search_query)
            ).filter(search=search_query).order_by("-rank")

        search_vector_grsub = SearchVector('teacher')
        result_groupsubjects = GroupSubject.objects.annotate(
            search=search_vector_grsub, rank=SearchRank(search_vector_grsub, search_query)
            ).filter(search=search_query).order_by("-rank")

        students = list(result_students.annotate(
            group_name=F('group__name'),
            semester_number=F('semester__semester'),
        ).values(
            'student_id',
            'last_name',
            'first_name',
            'second_name',
            'group_name',
            'semester_number',
        ))
        subjects = list(result_subjects.annotate(
            semester_number=F('semester__semester'),
            cathedra_name=F('cathedra__short_name'),
        ).values(
            'id',
            'name',
            'form_control',
            'semester_number',
            'cathedra_name',
        ))
        groupsubjects = list(result_groupsubjects.annotate(
            group=F('groups__name'),
            semester=F('subjects__semester__semester'),
            subject=F('subjects__name'),
            form_control=F('subjects__form_control'),
        ).values(
            'id',
            'teacher',
            'group',
            'semester',
            'subject',
            'form_control',
            'att_date',
        ))

        data = {
            'search': search,
            'students': students,
            'subjects': subjects,
            'groupsubjects': groupsubjects,
        }

    return JsonResponse({'data': data})
