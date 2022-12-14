import re
from collections import Counter

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from groups.models import Group
from students.models import Result, Semester
from subjects.forms import (CathedraForm, FacultyForm, GroupSubjectForm,
                            SubjectForm)
from subjects.models import (Cathedra, Faculty, GroupSubject, Subject,
                             SubjectLog)

from rating.settings import IMPORT_DELIMITER


class SubjectListView(LoginRequiredMixin, ListView):
    """Отобразить все предметы."""
    model = Subject
    template_name = 'subjects/subjects.html'
    queryset = Subject.objects.select_related('semester', 'cathedra').filter(is_archived=False)


class SubjectCreateView(LoginRequiredMixin, CreateView):
    """Добавить новый предмет."""
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/subject_add.html'
    success_url = '/subjects/'


class SubjectDetailView(LoginRequiredMixin, DetailView):
    """Сводная информация о дисциплине и история изменений по ней."""
    model = Subject

    def get(self, request, pk, **kwargs):
        # текущая дисциплина
        subject = get_object_or_404(Subject, id=pk)
        # группы, которым назначена текущая дисциплина в соответствующем семестре
        groups = GroupSubject.objects.filter(
            subjects=subject.id, is_archived=False).order_by(
            'groups__code', 'groups__name')
        # выборка студентов, сдававших дисциплину в соответствующем семестре
        students = Result.objects.select_related().filter(groupsubject__subjects=subject.id)

        # отображение истории изменений дисциплины
        try:
            history = SubjectLog.objects.select_related().filter(record_id=subject.id).order_by('-timestamp').values()
        except:
            history = 'Error'

        context = {
            'subject': subject,
            'history': history,
            'groups': groups,
            'students': students,
        }
        return render(request, 'subjects/subject_detail.html', context=context)


class SubjectDeleteView(LoginRequiredMixin, DeleteView):
    """Удалить предмет."""
    model = Subject
    template_name = 'subjects/subject_delete.html'
    success_url = '/subjects/'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        pk = self.kwargs.get('pk')
        groups = GroupSubject.objects.filter(subjects=pk)
        groups_data = []
        for group in groups:
            groups_data.append(f'{group.groups}-{group.subjects.semester.semester}')
        context['groups'] = groups_data
        return context


class SubjectUpdateView(LoginRequiredMixin, UpdateView):
    """Обновить информацию о предметах."""
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/subject_update.html'


def import_subjects(request):
    '''Импортировать дисциплины из CSV файла.'''
    success = False
    errors = []  # список дисциплин, которые не были импортированы
    file_validation = ''

    if request.method == 'POST':
        import_file = request.FILES['import_file'] if request.FILES else False

        # проверка, что файл выбран и формат файла CSV
        if not import_file or str(import_file).split('.')[-1] != 'csv':
            file_validation = False
            context = {'file_validation': file_validation}
            return render(request, 'import/import_subjects.html', context)

        try:
            for n, line in enumerate(import_file):
                row = line.decode().strip().split(IMPORT_DELIMITER)
                if n == 0:
                    pass
                else:
                    # проверка формата ЗЕТ
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

                    if row[3] and Cathedra.objects.filter(name=row[3]).exists():
                        cathedra = Cathedra.objects.get(name=row[3])

                    form_control = row[1].strip()
                    choices = list(map(lambda x: x[0], Subject._meta.get_field('form_control').choices))
                    if form_control not in choices:
                        errors.append(f'[{n+1}] {row[0]} {row[1]} {row[2]} семестр')
                        break

                    if row[0].startswith('"'):
                        subject_name = row[0].replace('"', "")
                    else:
                        subject_name = row[0].strip()

                    if cathedra:
                        obj, created = Subject.objects.get_or_create(
                            name=subject_name,
                            form_control=form_control,
                            semester=semester,
                            cathedra=cathedra,
                            zet=zet
                        )
                    else:
                        obj, created = Subject.objects.get_or_create(
                            name=subject_name,
                            form_control=form_control,
                            semester=semester,
                            zet=zet
                        )
                    if not created:
                        errors.append(f'[{n+1}] {subject_name} {row[1]} {row[2]} семестр - уже существует')
                        print('[!] ---> ', row)

            if not errors:
                success = True

        except Exception as subjects_import_error:
            print('[!] ---> Ошибка импорта дисциплин:', subjects_import_error, sep='\n')
            print(errors)
    context = {
        'file_validation': file_validation,
        'errors': errors,
        'success': success,
    }
    return render(request, 'import/import_subjects.html', context)

########################################################################################################################


class CathedraListView(LoginRequiredMixin, ListView):
    """Отобразить все кафедры."""
    model = Cathedra
    template_name = 'subjects/cathedras.html'
    queryset = Cathedra.objects.select_related('faculty')


class CathedraCreateView(LoginRequiredMixin, CreateView):
    """Добавить новую кафедру."""
    model = Cathedra
    form_class = CathedraForm
    template_name = 'subjects/cathedra_add.html'
    success_url = '/subjects/cathedras'


class CathedraUpdateView(LoginRequiredMixin, UpdateView):
    """Обновить информацию о кафедре."""
    model = Cathedra
    form_class = CathedraForm
    template_name = 'subjects/cathedra_update.html'
    success_url = '/subjects/cathedras'


class CathedraDeleteView(LoginRequiredMixin, DeleteView):
    """Удалить кафедру."""
    model = Cathedra
    template_name = 'subjects/cathedra_delete.html'
    success_url = '/subjects/cathedras'


def import_cathedras(request):
    '''Импортировать кафедры из CSV файла.'''
    success = False
    errors = []  # список кафедр, которые не были импортированы
    file_validation = ''

    if request.method == 'POST':
        import_file = request.FILES['import_file'] if request.FILES else False

        # проверка, что файл выбран и формат файла CSV
        if not import_file or str(import_file).split('.')[-1] != 'csv':
            file_validation = False
            context = {'file_validation': file_validation}
            return render(request, 'import/import_cathedras.html', context)

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

        except Exception as import_cathedras_error:
            print('[!] ---> Ошибка импорта кафедр:', import_cathedras_error, sep='\n')

    context = {
        'file_validation': file_validation,
        'errors': errors,
        'success': success,
    }
    return render(request, 'import/import_cathedras.html', context)

########################################################################################################################


class FacultyListView(LoginRequiredMixin, ListView):
    """Отобразить все факультеты."""
    model = Faculty
    template_name = 'subjects/faculties.html'


class FacultyCreateView(LoginRequiredMixin, CreateView):
    """Добавить новый факультет."""
    model = Faculty
    form_class = FacultyForm
    template_name = 'subjects/faculty_add.html'
    success_url = '/subjects/faculties'


class FacultyUpdateView(LoginRequiredMixin, UpdateView):
    """Обновить информацию о факультетах."""
    model = Faculty
    form_class = FacultyForm
    template_name = 'subjects/faculty_update.html'
    success_url = '/subjects/faculties'


class FacultyDeleteView(LoginRequiredMixin, DeleteView):
    """Удалить предмет."""
    model = Faculty
    template_name = 'subjects/faculty_delete.html'
    success_url = '/subjects/faculties'

########################################################################################################################


class GroupSubjectListView(LoginRequiredMixin, ListView):
    """Отобразить все назначения на дисциплины."""
    model = GroupSubject
    template_name = 'subjects/groupsubjects.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        groupsubjects = GroupSubject.objects.select_related('subjects__semester', 'groups').filter(is_archived=False)
        context['groupsubjects_list'] = groupsubjects.order_by('subjects__semester', 'groups', '-subjects__form_control')
        context['empty_date'] = groupsubjects.filter(att_date__exact=None).count()
        context['empty_teacher'] = groupsubjects.filter(teacher__exact='').count()
        return context


class GroupSubjectCreateView(LoginRequiredMixin, CreateView):
    """Добавить новое назначение дисциплины для групп."""
    model = GroupSubject
    form_class = GroupSubjectForm
    template_name = 'subjects/groupsubject_add.html'
    
    def post(self, request, *args, **kwargs):
        subject = request.POST['subjects'].replace('<option value=&quot;', '').split('&')[0]
        group = request.POST['groups'].replace('<option value=&quot;', '').split('&')[0]
        teacher = request.POST['teacher']
        att_date = request.POST['att_date']

        if request.POST.get('is_archived', False):
            is_archived = True
        else:
            is_archived = False
        
        form = GroupSubjectForm(data={
            'subjects': subject,
            'groups': group,
            'teacher': teacher,
            'att_date': att_date,
            'is_archived': is_archived,
        })
        if form.is_valid():
            form.save()
            return redirect('subjects:groupsubjects')

        return super().post(request, *args, **kwargs)


class GroupSubjectUpdateView(LoginRequiredMixin, UpdateView):
    """Обновить информацию о факультетах."""
    model = GroupSubject
    form_class = GroupSubjectForm
    template_name = 'subjects/groupsubject_update.html'
    success_url = '/subjects/groupsubjects'


class GroupSubjectDeleteView(LoginRequiredMixin, DeleteView):
    """Удалить дисциплину."""
    model = GroupSubject
    template_name = 'subjects/groupsubject_delete.html'
    success_url = '/subjects/groupsubjects'


def import_groupsubjects(request):
    '''Импортировать назначения дисциплин из CSV файла.'''
    success = False
    errors = []  # список назначений, которые не были импортированы
    file_validation = date_validation = ''

    if request.method == 'POST':
        import_file = request.FILES['import_file'] if request.FILES else False

        # проверка, что файл выбран и формат файла CSV
        if not import_file or str(import_file).split('.')[-1] != 'csv':
            file_validation = False
            context = {'file_validation': file_validation}
            return render(request, 'import/import_groupsubjects.html', context)

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

                        # проверка формата даты зачисления
                        if row[5] != '':
                            pattern = r'^([0-9]{2})\.([0-9]{2})\.([0-9]{4})$'  # DD.MM.YYYY
                            if not re.match(pattern, row[5]):
                                date_validation = False
                                print('[!] ---> Неверный формат даты аттестации.')
                                break
                            else:
                                # преобразование даты к формату поля модели
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
                            errors.append(f'[{n+1}] уже существует')
                    else:
                        if not is_subject:
                            errors.append(f'[{n+1}] дисциплины нет в этом семестре')
                        if not is_group:
                            errors.append(f'[{n+1}] группа отсутствует')
            if not errors:
                success = True

        except Exception as groupsubjects_import_error:
            print('[!] ---> Ошибка импорта назначений:', groupsubjects_import_error, sep='\n')

    context = {
        'file_validation': file_validation,
        'date_validation': date_validation,
        'errors': errors,
        'success': success,
    }
    return render(request, 'import/import_groupsubjects.html', context)

########################################################################################################################


class SubjectsDebtsListView(LoginRequiredMixin, ListView):
    """Отобразить задолженности всех студентов."""
    model = GroupSubject
    template_name = 'subjects/subjects_debts.html'

    def get_queryset(self):
        negative = ['ня', 'нз', '2']

        # id всех назначений с отрицательными оценками
        negative_subjects = Result.objects.select_related('groupsubject__subjects').filter(
            mark__contained_by=negative).values('groupsubject__id')
        # назначения
        group_subjects = GroupSubject.objects.select_related('subjects__semester', 'groups').filter(
            is_archived=False, id__in=negative_subjects).order_by('-subjects__semester')

        for gsub in group_subjects:
            all_marks = [
                i[0]
                for i in gsub.result_set.select_related('students__semester_semester').filter(
                    mark__contained_by=negative).values_list('mark')]
            marks_att1 = [i[0] for i in all_marks]
            marks_att2 = [i[1] for i in list(filter(lambda x: len(x) in [2, 3], all_marks))]
            marks_att3 = [i[2] for i in list(filter(lambda x: len(x) == 3, all_marks))]
            count_marks_att1 = dict(Counter(marks_att1))
            count_marks_att2 = dict(Counter(marks_att2))
            count_marks_att3 = dict(Counter(marks_att3))
            gsub.att1 = sum(list(map(lambda x: count_marks_att1.get(x, 0), negative)))
            gsub.att2 = sum(list(map(lambda x: count_marks_att2.get(x, 0), negative)))
            gsub.att3 = sum(list(map(lambda x: count_marks_att3.get(x, 0), negative)))

        return group_subjects
