from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import (CreateView, DeleteView, ListView, TemplateView, UpdateView, View)
from django.shortcuts import get_object_or_404

from groups.forms import GroupForm
from groups.models import Group
from students.models import Result, Student
from subjects.models import GroupSubject
from rating.functions import _get_students_group_statistic_and_marks


class GroupListView(LoginRequiredMixin, ListView):
    """Отобразить все активные группы."""
    model = Group
    template_name = 'groups/groups.html'
    ordering = ['level']

    def get_queryset(self):
        return Group.objects.filter(is_archived=False).values('id', 'name', 'direction', 'profile', 'level', 'code')


class GroupCreateView(LoginRequiredMixin, CreateView):
    """Добавить новую группу."""
    model = Group
    template_name = 'groups/group_add.html'
    form_class = GroupForm
    success_url = '/groups/'


class GroupDeleteView(LoginRequiredMixin, DeleteView):
    """Удалить группу."""
    model = Group
    template_name = 'groups/group_delete.html'
    success_url = '/groups/'


class GroupUpdateView(LoginRequiredMixin, UpdateView):
    """Обновить информацию о группе."""
    model = Group
    template_name = 'groups/group_update.html'
    form_class = GroupForm
    success_url = '/groups/'


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
        context = {
            'students': students,
            'subjects': subjects,
            'group': group,
            'semester': semester,
            'course': course,
        }
        return self.render_to_response(context)


class GroupMarksApiView(LoginRequiredMixin, View):
    '''Статистика и оценки студентов группы.'''

    def get(self, request):
        groupname = request.GET.get('groupname', '')
        semester = request.GET.get('semester', '')
        students = _get_students_group_statistic_and_marks(groupname, semester)

        serialized_data = []
        for m in students:
            # {groupsubject_id: [subject_id, form_control, result_id, [оценки]]}
            marks_data = [{k[0]:[k[1], k[2], v[0] if v != '-' else v, v[-1] if v != '-' else v]} for k, v in m.marks.items()]
            serialized_data.append({
                'studentId': m.student_id,
                'money': m.money,
                'att1': m.att1,
                'att2': m.att2,
                'att3': m.att3,
                'marks': marks_data,
                'passSession': m.pass_session,
            })

        # итоговая структура оценок [student.marks]
        # (groupsubject_id, subject_id, form_control): '-'
        # (groupsubject_id, subject_id, form_control): (result_id, [оценки])

        return JsonResponse({'data': serialized_data})

    def post(self, request):
        # обработка оценок
        result_id = request.POST.get('resId', '')
        student_id = request.POST.get('studentId', '')
        groupsub_id = request.POST.get('groupSubId', '')
        form = request.POST.get('form', '')
        value = request.POST.get('value', '')
        group_name = request.POST.get('groupName', '')
        semester = request.POST.get('semester', '')

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
        })
