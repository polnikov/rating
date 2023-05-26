from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView, TemplateView

from groups.models import Group
from groups.forms import GroupForm
from students.models import Result, Student
from subjects.models import GroupSubject, Subject


class ArchiveDataView(LoginRequiredMixin, ListView):

    def get(self, request):
        students = Student.archived_objects.select_related('group', 'semester')
        marks = Result.objects.select_related().filter(is_archived=True)
        subjects = Subject.archived_objects.select_related('semester', 'cathedra')
        groupsubjects = GroupSubject.archived_objects.select_related()
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
            },
        )


class HelpPageView(LoginRequiredMixin, TemplateView):
    template_name = 'help.html'
