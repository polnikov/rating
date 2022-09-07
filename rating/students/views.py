import re
from collections import Counter

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView, View)
from groups.models import Group
from groups.views import _get_students_group_statistic_and_marks
from students.forms import ResultForm, StudentForm
from students.models import Basis, Result, Semester, Student, StudentLog
from subjects.models import GroupSubject

from rating.settings import IMPORT_DELIMITER


class StudentListView(LoginRequiredMixin, ListView):
    """Отобразить всех студентов."""
    model = Student
    template_name = 'students/students.html'

    def get_context_data(self,*args, **kwargs):
        context = super().get_context_data(*args,**kwargs)
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
            history = StudentLog.objects.select_related('user').filter(record_id=student.student_id)
        except:
            history = 'Error'

        # все оценки студента
        marks = Result.objects.select_related().filter(students=student.student_id)
        # все аттестации для данного направления (группы), исключая зачеты
        atts = GroupSubject.objects.select_related('subjects').filter(
            groups=student.group, 
            is_archived=False
        ).filter(~Q(subjects__form_control__exact='Зачет'))

        # вычисление среднего балла по семестрам и суммарного
        rating_by_semester = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0,
            6: 0,
            7: 0,
            8: 0,
        }
        all_num_marks = []
        all_marks = []
        for i in range(1, 9):
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
    #! TODO: переписать через функцию
    def get(self, request):
        serialized_data = []
        sem_start = request.GET.get('semStart', '')
        sem_stop = request.GET.get('semStop', '')
        groups = request.GET.getlist('groups[]', False)
        if (not sem_start and not sem_stop) or (sem_start and not sem_stop) or (not sem_start and sem_stop) or (sem_start and sem_stop == '-'):
            # средний балл за указанный семестр. по умолчанию - за 1ый
            if sem_start:
                start = sem_start
            else:
                start = 1
            if groups:
                students = Student.objects.select_related('group', 'semester', 'basis').filter(is_archived=False, group__name__in=groups, semester__semester__gte=start)
            else:
                students = Student.objects.select_related('group', 'semester', 'basis').filter(is_archived=False, semester__semester__gte=start)
            
            for student in students:
                # все оценки студента в указанном семестре
                marks = Result.objects.select_related().filter(students=student.student_id, groupsubject__subjects__semester__semester=start).values('mark')
                # все аттестации для данного направления (группы) в указанном семестре, исключая зачеты
                atts = GroupSubject.objects.select_related('subjects').filter(
                    groups=student.group,
                    subjects__semester__semester=start,
                    is_archived=False
                ).filter(~Q(subjects__form_control__exact='Зачет'))
                # вычисление среднего балла за семестр
                # берем только последнюю оценку и исключаем <ня> и <2>
                marks = list(filter(lambda x: x not in ['ня', '2'], [i['mark'][-1] for i in marks]))
                # количество аттестаций с оценками в семестре
                num_atts = atts.count()
                # количество каждой из оценок <3 | 4 | 5>
                count_marks = dict(Counter(marks))
                # определяем средний балл за семестр
                try:
                    rating = round(sum([int(k)*v for k, v in count_marks.items()]) / num_atts, 2)
                except ZeroDivisionError:
                    rating = 0

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
            if groups:
                students = Student.objects.select_related('group', 'semester', 'basis').filter(is_archived=False, group__name__in=groups, semester__semester__gte=start)
            else:
                students = Student.objects.select_related('group', 'semester', 'basis').filter(is_archived=False, semester__semester__gte=start)
            for student in students:
                # все оценки студента за указанный период
                marks = Result.objects.select_related().filter(students=student.student_id).filter(Q(groupsubject__subjects__semester__semester__gte=start) & Q(groupsubject__subjects__semester__semester__lte=stop)).values('mark')
                # все аттестации для данного направления (группы) в указанном семестре, исключая зачеты
                atts = GroupSubject.objects.select_related('subjects').filter(
                    groups=student.group,
                    is_archived=False
                ).filter(Q(subjects__semester__semester__gte=start) & Q(subjects__semester__semester__lte=stop)
                ).filter(~Q(subjects__form_control__exact='Зачет'))
                # вычисление среднего балла за период
                # берем только последнюю оценку и исключаем <ня> и <2>
                marks = list(filter(lambda x: x not in ['ня', '2'], [i['mark'][-1] for i in marks]))
                # количество аттестаций с оценками в семестре
                num_atts = atts.count()
                # количество каждой из оценок <3 | 4 | 5>
                count_marks = dict(Counter(marks))
                # определяем средний балл за период
                try:
                    rating = round(sum([int(k)*v for k, v in count_marks.items()]) / num_atts, 2)
                except ZeroDivisionError:
                    rating = 0

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
            raise Http404(_("No %(verbose_name)s found matching the query") % {'verbose_name': queryset.model._meta.verbose_name})
        return obj


class StudentUpdateView(LoginRequiredMixin, UpdateView):
    """Обновление информации о студенте."""
    model = Student
    form_class = StudentForm
    template_name = 'students/student_update.html'


def students_json(request):
    students = Student.objects.all()
    data = [student.get_data() for student in students]
    response = {'data': data}
    return JsonResponse(response)


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
            return render(request, 'import/import.html', context)

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
                    group = row[7].upper()
                    is_group = Group.objects.filter(name=group).exists()
                    is_semester = Semester.objects.filter(id=row[8]).exists()
                    citizenship = row[5].capitalize()
                    is_citizenship = citizenship in list(map(lambda x: x[0], Student._meta.get_field('citizenship').choices))
                    level = row[6].capitalize()
                    is_level = level in list(map(lambda x: x[0], Student._meta.get_field('level').choices))
                    status = row[10].capitalize()
                    is_status = status in list(map(lambda x: x[0], Student._meta.get_field('status').choices))
                    if all([is_basis, is_group, is_semester, is_citizenship, is_level, is_status]):
                        basis = Basis.objects.get(name=basis).id
                        group = Group.objects.get(name=group).id
                        semester = Semester.objects.get(id=row[8]).id
                    else:
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
                        start_date ='-'.join(row[9].split('.')[::-1])

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
                            'tag': row[11],
                            'money': row[12],
                        },
                    )
                    if not created:
                        errors.append(f'[{n+1}] {row[1]} {row[2]} {row[3]}, номер: {row[0]}')
            if not errors: success = True

        except Exception as import_students_error:
            print('[!] ---> Ошибка импорта студентов:', import_students_error, sep='\n')

    context = {
        'file_validation': file_validation,
        'date_validation': date_validation,
        'errors': errors,
        'success': success,
    }
    return render(request, 'import/import.html', context)


@login_required
def transfer_students(request):
    '''Перевести студентов на следующий семестр. В случае последнего семестра студент отправляется в <Архив> со сменой
    статуса на <Выпускник>.
    '''
    students_for_transfer = request.POST.getlist('checkedStudents[]', False)
    students_id = list(map(int, students_for_transfer))

    for id in students_id:
        student = Student.objects.get(student_id=id)
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

    return JsonResponse({"success":"Updated"})

########################################################################################################################

class ResultListView(LoginRequiredMixin, ListView):
    """Отобразить все оценки."""
    model = Result
    template_name = 'students/results.html'
    queryset = Result.objects.select_related().filter(students__is_archived=False)


class ResultCreateView(LoginRequiredMixin, CreateView):
    model = Result
    form_class = ResultForm
    template_name = 'students/result_add.html'
    success_url = '/students/results'


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
        negative_students = Result.objects.select_related('students').filter(mark__contained_by=negative).values('students__student_id')
        # студенты
        students = Student.objects.select_related('basis', 'group', 'semester').filter(is_archived=False, student_id__in=negative_students)

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
