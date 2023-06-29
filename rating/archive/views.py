from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView, TemplateView

from groups.models import Group
from groups.forms import GroupForm
from students.models import Result, Student
from students.forms import ResultForm
from subjects.models import GroupSubject, Subject
from subjects.forms import GroupSubjectForm


class ArchiveDataView(LoginRequiredMixin, ListView):

    def get(self, request):
        students = Student.archived_objects.all().count()
        marks = Result.objects.filter(is_archived=True).count()
        subjects = Subject.archived_objects.all().count()
        groupsubjects = GroupSubject.archived_objects.all().count()
        groups = Group.objects.filter(is_archived=True).count()

        return render(
            request,
            'archive/archive_data.html',
            context={
                'students': students,
                'marks': marks,
                'subjects': subjects,
                'groupsubjects': groupsubjects,
                'groups': groups,
                'group_form': GroupForm(),
                'groupsubject_form': GroupSubjectForm(),
                'result_form': ResultForm(),
            },
        )


class HelpPageView(LoginRequiredMixin, TemplateView):
    template_name = 'help.html'
