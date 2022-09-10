from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView
from groups.models import Group
from students.models import Result, Student
from subjects.models import GroupSubject, Subject


class ArchiveDataView(LoginRequiredMixin, ListView):

    def get(self, request):
        students = Student.objects.select_related('group', 'semester').filter(is_archived=True)
        marks = Result.objects.select_related().filter(is_archived=True)
        subjects = Subject.objects.select_related('semester', 'cathedra').filter(is_archived=True)
        groupsubjects = GroupSubject.objects.select_related().filter(is_archived=True)
        groups = Group.objects.filter(is_archived=True)

        return render(
            request,
            'archive/archive_data.html',
            context={
                'students': students,
                'marks': marks,
                'subjects': subjects,
                'groupsubjects': groupsubjects,
                'groups': groups,
            }
        )
