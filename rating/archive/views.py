from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from groups.models import Group
from students.models import Result, Student
from subjects.models import GroupSubject, Subject


class ArchiveStudentsView(LoginRequiredMixin, ListView):
   template_name = 'archive/archive_students.html'

   def get_queryset(self):
      return Student.objects.select_related('group', 'semester').filter(is_archived=True)


class ArchiveMarksView(LoginRequiredMixin, ListView):
   template_name = 'archive/archive_marks.html'

   def get_queryset(self):
      return Result.objects.select_related().filter(is_archived=True)


class ArchiveSubjectsView(LoginRequiredMixin, ListView):
   template_name = 'archive/archive_subjects.html'

   def get_queryset(self):
      return Subject.objects.select_related('semester', 'cathedra').filter(is_archived=True)


class ArchiveGroupsubjectsView(LoginRequiredMixin, ListView):
   template_name = 'archive/archive_groupsubjects.html'

   def get_queryset(self):
      return GroupSubject.objects.select_related().filter(is_archived=True)


class ArchiveGroupsView(LoginRequiredMixin, ListView):
   template_name = 'archive/archive_groups.html'

   def get_queryset(self):
      return Group.objects.filter(is_archived=True)

