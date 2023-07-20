import xlrd
import re
import json
import logging
from api import serializers
from datetime import datetime
from collections import Counter

from rest_framework import generics, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from django.http.response import JsonResponse
from django.db.models import Q

from groups.models import Group
from groups.forms import GroupForm
from subjects.forms import FacultyForm, CathedraForm, SubjectForm, GroupSubjectForm
from subjects.models import Cathedra, Faculty, GroupSubject, Subject, SubjectLog
from students.models import Result, Semester, Student, StudentLog, Basis
from students.validators import validate_mark, check_mark
from students.forms import StudentForm, ResultForm

from rating.settings import IMPORT_DELIMITER
from rating.functions import _get_students_group_statistic_and_marks, calculate_rating


logger = logging.getLogger(__name__)


# Students
class StudentsList(generics.ListAPIView):
    queryset = Student.objects.filter(status='Является студентом')
    serializer_class = serializers.StudentsListSerializer


class StudentsArchivedList(generics.ListAPIView):
    queryset = Student.archived_objects.all()
    serializer_class = serializers.StudentsListSerializer


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = serializers.StudentSerializer


    @action(methods=['post'], detail=False)
    def create_student(self, request):
        form = StudentForm(request.data)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=201)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['patch'], detail=True)
    def update_student(self, request, pk=None):
        try:
            student = Student.objects.get(student_id=pk)
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Student not found'}, status=404)

        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=200)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['delete'], detail=True)
    def delete_student(self, request, pk=None):
        queryset = Student.objects.all()

        try:
            student = queryset.get(student_id=pk)
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Student not found'}, status=404)

        student.delete()
        return JsonResponse({'success': True}, status=201)


class StudentLogList(generics.ListAPIView):
    queryset = StudentLog.objects.all()
    serializer_class = serializers.StudentLogSerializer


class StudentMoneyList(generics.ListAPIView):
    queryset = Student.active_objects.select_related('basis', 'group', 'semester')
    serializer_class = serializers.StudentMoneySerializer


def transfer_students(request):
    '''Transfer students to the next semester. In case of the last semester the student is sent to <Архив> with a status
    change to <Выпускник>.
    '''
    logger.info('Перевод студентов на следующий семестр...')
    students_for_transfer = request.POST.getlist('checkedStudents[]', False)
    profile = request.POST.get('profile', False)
    students_id = list(map(int, students_for_transfer))

    if not profile:
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
                # change the student status to <Выпускник> and sent to <Архив>
                student.status = Student.Status.GRADUATED
                student.save()
    else:
        group = Group.objects.get(name=profile)
        for st in students_id:
            student = Student.objects.get(student_id=st)
            student.group = group
            semester = Semester.objects.get(semester='7')
            student.semester = semester
            student.save()

    logger.info('|---> Перевод студентов на следующий семестр успешно выполнен')
    return JsonResponse({"success": "Updated"})


def import_students(request):
    '''Import students from CSV file.'''
    logger.info('Импорт студентов...')
    serialized_data = []
    success = False
    errors = []  # list of non-imported students

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
                        logger.error(f'|---> Ошибка импорта студента: {row[1]} {row[2]} {row[3]}, номер: {row[0]}')
                        break

                    # check start date format
                    pattern = r'^([0-9]{2})\.([0-9]{2})\.([0-9]{4})$'  # DD.MM.YYYY
                    if not re.match(pattern, row[9]):
                        errors.append(f'Неверный формат даты зачисления: {row[1]} {row[2]} {row[3]}, номер: {row[0]}')
                        logger.error(f'|---> Неверный формат даты зачисления: {row[1]} {row[2]} {row[3]}, номер: {row[0]}')
                        break
                    else:
                        # att date transformation
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
                            logger.error(f'|---> Не удалось создать объект студента: {row[1]} {row[2]} {row[3]}, номер: {row[0]}')
                    except Exception as ex:
                        logger.error(f'|---> Не удалось создать объект студента: {row[1]} {row[2]} {row[3]}, номер: {row[0]}', extra={'Exception': ex})

            if not errors:
                success = True
            logger.info('|---> Запись студентов в БД успешно выполнена')

        except Exception as students_import_error:
            logger.error(f'[!] |---> Ошибка импорта студентов: {students_import_error}, {errors}', exc_info=True)

    serialized_data.append({'errors': errors, 'success': success})
    return JsonResponse({'data': serialized_data})


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


@api_view(['GET'])
def students_debts(request):
    """Show current students debts."""
    data = []
    negative = ['ня', 'нз', '2']

    # students ids who has debts
    negative_students = Result.objects.select_related('students').filter(
        mark__contained_by=negative, is_archived=False).values('students__student_id')
    # filter students by ids
    students = Student.active_objects.select_related('basis', 'group', 'semester').filter(
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

        data.append({
            'student_id': st.student_id,
            'fullname': st.fullname,
            'group': st.group.name,
            'group_id': st.group.id,
            'semester': st.semester.semester,
            'basis': st.basis.name,
            'debts': {
                'att1': st.att1,
                'att3': st.att2,
                'att2': st.att3,
            },
        })

    return Response({'data': data})


# Results
class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = serializers.ResultSerializer


    @action(methods=['post'], detail=False)
    def create_result(self, request):
        student = request.POST['students']
        groupsubject = request.POST['groupsubjects'].replace('<option value=&quot;', '').split('&')[0]
        mark_0 = request.POST['mark_0']
        mark_1 = request.POST['mark_1']
        mark_2 = request.POST['mark_2']
        tag = request.POST['tag']
        is_archived = request.POST.get('is_archived', False)

        if is_archived:
            form = ResultForm(data={'students': student,
                                    'groupsubject': groupsubject,
                                    'mark_0': mark_0,
                                    'mark_1': mark_1,
                                    'mark_2': mark_2,
                                    'is_archived': is_archived,
                                    'tag': tag})
        else:
            form = ResultForm(data={'students': student,
                                    'groupsubject': groupsubject,
                                    'mark_0': mark_0,
                                    'mark_1': mark_1,
                                    'mark_2': mark_2,
                                    'tag': tag})
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=201)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['patch'], detail=True)
    def update_result(self, request, pk=None):
        instance = self.get_object()
        try:
            mark_1 = instance.mark[1]
        except IndexError:
            mark_1 = ''
        try:
            mark_2 = instance.mark[2]
        except IndexError:
            mark_2 = ''

        student = request.data.get('students', instance.students)
        groupsubject = request.data.get('groupsubject', instance.groupsubject)
        mark_0 = request.data.get('mark_0', instance.mark[0])
        mark_1 = request.data.get('mark_1', mark_1)
        mark_2 = request.data.get('mark_2', mark_2)
        tag = request.data.get('tag', instance.tag)
        is_archived = request.data.get('is_archived', instance.is_archived)

        form_data = {
            'students': student,
            'groupsubject': groupsubject,
            'mark_0': mark_0,
            'mark_1': mark_1,
            'mark_2': mark_2,
            'tag': tag,
            'is_archived': is_archived,
        }

        form = ResultForm(data=form_data, instance=instance)

        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=201)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['delete'], detail=True)
    def delete_result(self, request, pk=None):
        queryset = Result.objects.all()

        try:
            result = queryset.get(id=pk)
        except Result.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Result not found'}, status=404)

        result.delete()
        return JsonResponse({'success': True}, status=201)


class ResultsArchivedList(generics.ListAPIView):
    queryset = Result.objects.select_related().filter(is_archived=True)
    serializer_class = serializers.ResultArchivedSerializer


class ResultsForStudentList(generics.ListAPIView):
    serializer_class = serializers.ResultSerializer


    def get_queryset(self):
        student_id = self.request.query_params.get('student_id')
        return Result.objects.select_related().filter(students=student_id, is_archived=False)


class ResultsForSubjectList(generics.ListAPIView):
    serializer_class = serializers.ResultSerializer


    def get_queryset(self):
        subject_id = self.request.query_params.get('subject_id')
        return Result.objects.select_related().filter(groupsubject__subjects=subject_id, is_archived=False)


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
                'passReSession': m.pass_resession,
                'passLast': m.pass_last,
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
            'passReSession': statistic[5],
            'passLast': statistic[6],
        })


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
class SubjectsList(generics.ListAPIView):
    queryset = Subject.active_objects.all()
    serializer_class = serializers.SubjectsListSerializer


class SubjectsArchivedList(generics.ListAPIView):
    queryset = Subject.archived_objects.all()
    serializer_class = serializers.SubjectsListSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = serializers.SubjectSerializer


    @action(methods=['post'], detail=False)
    def create_subject(self, request):
        form = SubjectForm(request.data)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=201)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['patch'], detail=True)
    def update_subject(self, request, pk=None):
        print('======', pk)
        try:
            subject = Subject.objects.get(id=pk)
        except Subject.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Subject not found'}, status=404)

        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=200)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['delete'], detail=True)
    def delete_subject(self, request, pk=None):
        queryset = Subject.objects.all()

        try:
            subject = queryset.get(id=pk)
        except Subject.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Subject not found'}, status=404)

        subject.delete()
        return JsonResponse({'success': True}, status=201)


def import_subjects(request):
    '''Import subjects from CSV file.'''
    logger.info('Импорт дисциплин...')
    serialized_data = []
    success = False
    errors = []  # list of non-imported subjects

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
                    # check ZET format
                    pattern = r'([0-9]{2,3})\s\(([0-9]{1,2})\)'  # 72 (2)
                    if row[4] == '':
                        zet = ''
                    else:
                        try:
                            zet = re.search(pattern, row[4]).group(0)
                        except AttributeError:
                            errors.append(f'[{n+1}] {row[0]} {row[1]} {row[2]} семестр')
                            break

                    is_semester = Semester.objects.filter(id=row[2]).exists()
                    if is_semester:
                        semester = Semester.objects.get(id=row[2])
                    else:
                        errors.append(f'[{n+1}] {row[0]} {row[1]} {row[2]} семестр')
                        break

                    is_cathedra = Cathedra.objects.filter(name=row[3]).exists()
                    if is_cathedra:
                        cathedra = Cathedra.objects.get(name=row[3])
                    else:
                        errors.append(f'[{n+1}] ошибка в кафедре или её не существует: {row[3]}')
                        break

                    form_control = row[1].strip()
                    choices = list(map(lambda x: x[0], Subject._meta.get_field('form_control').choices))
                    if form_control not in choices:
                        errors.append(f'[{n+1}] {row[0]} {row[1]} {row[2]} семестр')
                        break

                    if row[0].startswith('"'):
                        subject_name = row[0].replace('"', "")
                    else:
                        subject_name = row[0].strip()

                    obj, created = Subject.objects.get_or_create(
                        name=subject_name,
                        form_control=form_control,
                        semester=semester,
                        cathedra=cathedra,
                        zet=zet,
                    )
                    if not created:
                        errors.append(f'[{n+1}] {subject_name} {row[1]} {row[2]} семестр - уже существует')
                        print('[!] ---> ', row)

            if not errors:
                success = True
            logger.info('|---> Запись дисциплин в БД успешно выполнена')

        except Exception as subjects_import_error:
            logger.error(f'[!] ---> Ошибка импорта дисциплин: {subjects_import_error}, {errors}', exc_info=True)

    serialized_data.append({'errors': errors, 'success': success})
    return JsonResponse({'data': serialized_data})


class SubjectLogList(generics.ListAPIView):
    queryset = SubjectLog.objects.all()
    serializer_class = serializers.SubjectLogSerializer


# GroupSubjects
class GroupSubjectsList(generics.ListAPIView):
    queryset = GroupSubject.active_objects.all()
    serializer_class = serializers.GroupSubjectsListSerializer


class GroupSubjectViewSet(viewsets.ModelViewSet):
    queryset = GroupSubject.objects.all()
    serializer_class = serializers.GroupSubjectsListSerializer


    def get_queryset(self):
        if self.request.GET.get('is_archived') == 'true':
            return GroupSubject.archived_objects.all()
        return super().get_queryset()


    @action(methods=['post'], detail=False)
    def create_groupsubject(self, request):
        subject = request.POST['subjects'].replace('<option value=&quot;', '').split('&')[0]
        group = request.POST['groups'].replace('<option value=&quot;', '').split('&')[0]
        teacher = request.POST['teacher']
        att_date = request.POST['att_date']
        comment = request.POST['comment']

        if request.POST.get('is_archived', False):
            is_archived = True
        else:
            is_archived = False
        
        form = GroupSubjectForm(data={
            'subjects': subject,
            'groups': group,
            'teacher': teacher,
            'att_date': att_date,
            'comment': comment,
            'is_archived': is_archived,
        })
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=201)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['patch'], detail=True)
    def update_groupsubject(self, request, pk=None):
        try:
            group_subject = GroupSubject.objects.get(id=pk)
        except GroupSubject.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'GroupSubject not found'}, status=404)

        form = GroupSubjectForm(request.POST, instance=group_subject)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}, status=200)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    @action(methods=['delete'], detail=True)
    def delete_groupsubject(self, request, pk=None):
        queryset = GroupSubject.objects.all()

        try:
            group_subject = queryset.get(id=pk)
        except GroupSubject.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'GroupSubject not found'}, status=404)

        group_subject.delete()
        return JsonResponse({'success': True}, status=201)


def import_groupsubjects(request):
    '''Import groupsubjects from CSV file.'''
    logger.info('Импорт назначений...')
    serialized_data = []
    success = False
    errors = []  # list of non-imported groupsubjects

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
                    is_subject = Subject.objects.filter(
                        name=row[0],
                        form_control=row[1],
                        semester=row[2],
                    ).exists()
                    is_group = Group.objects.filter(name=row[3])

                    if all([is_subject, is_group]):
                        subject = Subject.objects.get(name=row[0], form_control=row[1], semester=row[2])
                        group = Group.objects.get(name=row[3])

                        # check att date format
                        if row[5] != '':
                            pattern = r'^([0-9]{2})\.([0-9]{2})\.([0-9]{4})$'  # DD.MM.YYYY
                            if not re.match(pattern, row[5]):
                                errors.append(f'{n+1}: Неверный формат даты аттестации: {row[0]} [{row[5]}]')
                                logger.error(f'|---> {n+1}: Неверный формат даты аттестации: {row[0]} [{row[5]}]')
                                break
                            else:
                                # att date transformation
                                att_date = '-'.join(row[5].split('.')[::-1])

                                defaults = {
                                    'groups': group,
                                    'subjects': subject,
                                    'att_date': att_date,
                                    'teacher': row[4],
                                }
                        else:
                            defaults = {
                                'groups': group,
                                'subjects': subject,
                                'teacher': row[4],
                            }

                        if not GroupSubject.objects.filter(groups=group, subjects=subject).exists():
                            GroupSubject.objects.create(**defaults)
                        else:
                            errors.append(f'{n+1}: [{row[0]}] уже существует')
                            logger.error(f'[!] |---> [{row[0]}] уже существует')
                    else:
                        if not is_subject:
                            errors.append(f'{n+1}: [{row[0]}] дисциплины нет в [{row[2]}] семестре')
                            logger.error(f'[!] |---> {n+1}: [{row[0]}] дисциплины нет в [{row[2]}] семестре')
                        if not is_group:
                            errors.append(f'{n+1}: [{row[3]}] группа отсутствует')
                            logger.error(f'[!] |--->{n+1}: [{row[3]}] группа отсутствует')
            if not errors:
                success = True
            logger.info('|---> Запись назначений в БД успешно выполнена')

        except Exception as groupsubjects_import_error:
            logger.error(f'[!] |---> Ошибка импорта назначений: {groupsubjects_import_error}, {errors}', exc_info=True)

    serialized_data.append({'errors': errors, 'success': success})
    return JsonResponse({'data': serialized_data})


def reset_groupsubjects(request):
    '''Сбросить назначенные дисциплины группе в семестре (отправить в архив).'''
    if request.method == 'POST' and request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            group = data.get('groupName', '')
            semester = data.get('semester', '')
            logger.info(f'API: Сброс назначений для группы {group} в семестре {semester}')
            groupsubjects = data.get('subjectIds', [])
            print(group, semester, groupsubjects)

            if groupsubjects:
                groupsubjects = map(int, groupsubjects)
            
            for gs in groupsubjects:
                groupsubject = GroupSubject.objects.get(id=gs)
                groupsubject.is_archived = True
                groupsubject.save()
            return JsonResponse({'success': True}, status=201)
        except Exception as e:
            return JsonResponse({'success': True, 'errors': str(e)}, status=400)
