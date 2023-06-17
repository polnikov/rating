from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView
from django.shortcuts import get_object_or_404

from groups.forms import GroupForm
from groups.models import Group
from students.models import Student
from subjects.models import GroupSubject


class GroupView(LoginRequiredMixin, TemplateView):
    template_name = 'groups/groups.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.filter(is_archived=False).count()
        context['form'] = GroupForm()
        return context


class GroupCardsView(LoginRequiredMixin, ListView):
    """Отобразить карточки групп."""
    model = Group
    template_name = 'groups/group_cards.html'
    ordering = ['code', 'name']

    def get_queryset(self):
        return Group.objects.filter(is_archived=False).values('id', 'name', 'direction', 'profile', 'level', 'code')


class GroupDetailListView(LoginRequiredMixin, TemplateView):
    '''Отображение студентов соответствующей группы и семестра и назначенных им дисциплин.'''
    template_name = 'groups/group_detail.html'

    def get(self, request, groupname, semester, **kwargs):
        context = self.get_context_data(**kwargs)
        # текущая группа
        group = get_object_or_404(Group, name=groupname)
        # студенты текущей группы
        students = Student.active_objects.select_related('basis', 'group').filter(
            group__name=groupname,
            semester=semester,
            status='Является студентом'
        ).order_by('last_name')
        # дисциплины, назначенные текущей группе в соответствующем семестре
        subjects = GroupSubject.active_objects.select_related('subjects').filter(
            groups__name=groupname,
            subjects__semester=semester,
        ).order_by('subjects__form_control', 'subjects__name')
        # текущий курс группы
        course = students[0].course if students else '-'

        if group.level == 'Бакалавриат':
            if 'Сб(ИС)' in group.name:
                max_semester = 4
                min_semester = 1
            elif 'Сб(ИС-' in group.name:
                max_semester = 8
                min_semester = 5
            else:
                max_semester = 8
                min_semester = 1
        else:
            max_semester = 4
            min_semester = 1

        previous_semester = semester - 1 if semester > min_semester else False
        next_semester = semester + 1 if semester < max_semester else False
        
        # профильные группы строительства
        groups = Group.objects.filter(is_archived=False, name__contains='Сб(ИС-')

        context = {
            'students': students,
            'subjects': subjects,
            'group': group,
            'groups': groups,
            'semester': semester,
            'course': course,
            'previous_semester': previous_semester,
            'next_semester': next_semester,
        }
        return self.render_to_response(context)
