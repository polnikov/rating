import re
from collections import Counter

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import (TemplateView, CreateView, DeleteView, DetailView, ListView, UpdateView)
from groups.models import Group
from students.models import Result
from subjects.forms import (CathedraForm, FacultyForm, GroupSubjectForm, SubjectForm)
from subjects.models import (Cathedra, Faculty, GroupSubject, Subject, SubjectLog)

from rating.settings import IMPORT_DELIMITER


class SubjectView(LoginRequiredMixin, TemplateView):
    template_name = 'subjects/subjects.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subjects'] = Subject.objects.all().count()
        context['form'] = SubjectForm()
        return context


class SubjectCreateView(LoginRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/subject_add.html'
    success_url = '/subjects/'


class SubjectDetailView(LoginRequiredMixin, DetailView):
    model = Subject

    def get(self, request, pk, **kwargs):
        # current subject
        subject = get_object_or_404(Subject, id=pk)
        # groups with subject groupsubject in current semester
        groups = GroupSubject.active_objects.filter(subjects=subject.id).order_by('groups__code', 'groups__name')
        # выборка студентов, сдававших дисциплину в соответствующем семестре
        # students who have current subject
        students = Result.objects.select_related().filter(groupsubject__subjects=subject.id)

        # subjects changes history
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


class CathedraView(LoginRequiredMixin, TemplateView):
    template_name = 'subjects/cathedras.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cathedras'] = Cathedra.objects.all().count()
        context['form'] = CathedraForm()
        return context


class FacultyView(LoginRequiredMixin, TemplateView):
    template_name = 'subjects/faculties.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faculties'] = Faculty.objects.all().count()
        context['form'] = FacultyForm()
        return context


class GroupSubjectListView(LoginRequiredMixin, ListView):
    model = GroupSubject
    template_name = 'subjects/groupsubjects.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        groupsubjects = GroupSubject.active_objects.select_related('subjects__semester', 'groups')
        context['groupsubjects_list'] = groupsubjects.order_by('subjects__semester', 'groups', '-subjects__form_control')
        context['empty_date'] = groupsubjects.filter(att_date__exact=None).count()
        context['empty_teacher'] = groupsubjects.filter(teacher__exact='').count()
        return context


class GroupSubjectCreateView(LoginRequiredMixin, CreateView):
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
    model = GroupSubject
    form_class = GroupSubjectForm
    template_name = 'subjects/groupsubject_update.html'
    success_url = '/subjects/groupsubjects'


class GroupSubjectDeleteView(LoginRequiredMixin, DeleteView):
    model = GroupSubject
    template_name = 'subjects/groupsubject_delete.html'
    success_url = '/subjects/groupsubjects'


def import_groupsubjects(request):
    '''Import groupsubjects from CSV file.'''
    success = False
    errors = []  # list of non-imported groupsubjects
    file_validation = date_validation = ''

    if request.method == 'POST':
        import_file = request.FILES['import_file'] if request.FILES else False

        # checking that the file has been selected and its format is CSV
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

                        # check att date format
                        if row[5] != '':
                            pattern = r'^([0-9]{2})\.([0-9]{2})\.([0-9]{4})$'  # DD.MM.YYYY
                            if not re.match(pattern, row[5]):
                                date_validation = False
                                print('[!] ---> Неверный формат даты аттестации.')
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


class SubjectsDebtsListView(LoginRequiredMixin, ListView):
    model = GroupSubject
    template_name = 'subjects/subjects_debts.html'

    def get_queryset(self):
        negative = ['ня', 'нз', '2']

        # ids of all groupsubjects with negative marks
        negative_subjects = Result.objects.select_related('groupsubject__subjects').filter(
            mark__contained_by=negative).values('groupsubject__id')
        # groupsubjects
        group_subjects = GroupSubject.active_objects.select_related('subjects__semester', 'groups').filter(
            id__in=negative_subjects).order_by('-subjects__semester')

        for gsub in group_subjects:
            all_marks = [
                i[0]
                for i in gsub.result_set.select_related('students__semester_semester').filter(
                    mark__contained_by=negative, students__is_archived=False).values_list('mark')]
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
