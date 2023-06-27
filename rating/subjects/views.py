from collections import Counter

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views.generic import (TemplateView, DetailView, ListView)
from students.models import Result
from subjects.forms import (CathedraForm, FacultyForm, GroupSubjectForm, SubjectForm)
from subjects.models import (Cathedra, Faculty, GroupSubject, Subject, SubjectLog)


class SubjectView(LoginRequiredMixin, TemplateView):
    template_name = 'subjects/subjects.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subjects'] = Subject.active_objects.all().count()
        context['form'] = SubjectForm()
        return context


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
        form = SubjectForm()

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
            'form': form,
        }
        return render(request, 'subjects/subject_detail.html', context=context)


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


class GroupSubjectView(LoginRequiredMixin, TemplateView):
    template_name = 'subjects/groupsubjects.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        groupsubjects = GroupSubject.active_objects.all()
        context['groupsubjects'] = groupsubjects.count()
        context['empty_dates'] = groupsubjects.filter(att_date__exact=None).count()
        context['empty_teachers'] = groupsubjects.filter(teacher__exact='').count()
        context['form'] = GroupSubjectForm()
        return context


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
