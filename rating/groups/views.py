import itertools
from collections import Counter

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import (CreateView, DeleteView, ListView,
                                  TemplateView, UpdateView, View)

from groups.forms import GroupForm
from groups.models import Group
from students.models import Result, Student
from subjects.models import GroupSubject


class GroupListView(LoginRequiredMixin, ListView):
    """Отобразить все группы."""
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

########################################################################################################################

class GroupCardsView(LoginRequiredMixin, ListView):
    """Отобразить карточки групп."""
    model = Group
    template_name = 'groups/group_cards.html'
    ordering = ['code']

    def get_queryset(self):
        return Group.objects.filter(is_archived=False).values('id', 'name', 'direction', 'profile', 'level', 'code')

########################################################################################################################

class GroupDetailListView(LoginRequiredMixin, TemplateView):
    '''Отображение студентов соответствующей группы и семестра и назначенных им дисциплин.'''
    template_name = 'groups/group_detail.html'

    def get(self, request, groupname, semester, **kwargs):
        context = self.get_context_data(**kwargs)
        # текущая группа
        group = Group.objects.get(name=groupname)
        # студенты текущей группы
        students = Student.objects.select_related('basis', 'group').filter(group__name=groupname, semester=semester, is_archived=False).order_by('last_name')
        # дисциплины, назначенные текущей группе в соответствующем семестре
        subjects = GroupSubject.objects.select_related('subjects').filter(groups__name=groupname, subjects__semester=semester, is_archived=False).order_by('subjects__form_control')
        # текущий курс группы
        course = students[0].course if students else '<i class="icon red close"></i>'
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
                'marks': marks_data
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
        })


def _get_students_group_statistic_and_marks(groupname, semester, student=None):
    '''Сформировать статистику и оценки студентов группы. При указании в <student> ID студента, будет запрошена 
    статистика только указанного студента.

    return if student=None: `objects`
    return if student: `list`
    '''
    # дисциплины, назначенные текущей группе в соответствующем семестре
    subjects = GroupSubject.objects.select_related().filter(groups__name=groupname, subjects__semester=semester).order_by('subjects__form_control')

    # добавляем порядковую нумерацию дисциплин
    for n, s in enumerate(subjects):
        s.n = n

    # id всех назначенных дисциплин
    subjects_id = [i.subjects.id for i in subjects]
    # id всех назначений
    group_subjects_id = [i.id for i in subjects]
    # формы контроля назначенных дисциплин
    form_control = [i.subjects.form_control for i in subjects]
    key = list(itertools.zip_longest(group_subjects_id, subjects_id, form_control))

    if student:
        # существующие оценки студента текущей группы по назначенным группе дисциплинам
        results = Result.objects.select_related('groupsubject').filter(groupsubject__groups__name=groupname,
                                        groupsubject__subjects__semester=semester,
                                        students=int(student))
        marks = [i.mark for i in results]
        negative = ['ня', 'нз', '2']
        # считаем количество задолженностей по каждому этапу аттестации
        cnt1, cnt2, cnt3 = 0, 0, 0
        for m in marks:
            q_marks = len(m)
            match q_marks:
                case 1:
                    if m[0] in negative:
                        cnt1 += 1
                case 2:
                    if m[0] in negative:
                        cnt1 += 1
                    if m[1] in negative:
                        cnt2 += 1
                case 3:
                    if m[0] in negative:
                        cnt1 += 1
                    if m[1] in negative:
                        cnt2 += 1
                    if m[2] in negative:
                        cnt3 += 1

        att1, att2, att3 = cnt1, cnt2, cnt3
        # print('----->>>>>', att1)
        # print('----->>>>>', att2)
        # print('----->>>>>', att3)

    ######### подсчет оценок для определения стипендии

        # извлекаем все первые оценки в единый список
        first_marks = list(map(lambda x: x[0], marks))
        # считем количество каждого типа оценки
        first_marks = dict(Counter(first_marks))

        # условные критерии для определения типа стипендии
        no_marks_yet = not bool(len(first_marks))     # нет ни одной оценки
        is_C_marks = '3' in first_marks               # есть хотя бы одна 3-ка
        no_A_marks = not ('5' in first_marks)         # нет ни одной 5-ки
        no_B_marks = not ('4' in first_marks)         # нет ни одной 4-ки
        student = Student.objects.select_related('basis').get(student_id=int(student))
        basis = student.basis.name

        if basis == 'Контракт':
            student.money = 'нет'
            student.save()
            # print('==========', 1)
        elif basis == 'ИГ':
            student.money = '1.0'
            student.save()
            # print('==========', 2)
        elif att1 > 0:
            student.money = 'нет'
            student.save()
            # print('==========', 3)
        elif no_marks_yet or is_C_marks:
            student.money = 'нет'
            student.save()
            # print('==========', 4)
        elif no_A_marks:
            student.money = '1.0'
            student.save()
            # print('==========', 5)
        elif no_B_marks:
            student.money = '1.5'
            student.save()
            # print('==========', 6)
        else:
            student.money = '1.25'
            student.save()
            # print('==========', 7)

        att1 = '' if not cnt1 else cnt1
        att2 = '' if not cnt2 else cnt2
        att3 = '' if not cnt3 else cnt3

        return [student.money, att1, att2, att3]

    else:
        # студенты текущей группы
        students = Student.objects.select_related('basis', 'semester').filter(group__name=groupname, semester=semester, is_archived=False).order_by('last_name')
        # существующие оценки студентов текущей группы по назначенным группе дисциплинам
        results = Result.objects.select_related().filter(groupsubject__groups__name=groupname, groupsubject__subjects__semester=semester)


        # готовим структуру оценок по каждому студенту
        num_subjects = len(subjects)
        marks = {(i.fullname, i.student_id):['-' for i in range(num_subjects)] for i in students}

        # переносим результаты по каждому студенту
        for res in results:
            # print('-res-res-res-res-res-', res)
            # ключ для определения студента
            res_k = (res.students.fullname, res.students.student_id)
            # ищем студента соответствующего студента в структуре
            for k in marks:
                if k == res_k:
                    # определяем id дисциплины
                    id_sub = res.groupsubject.subjects.id
                    # ищем дисциплину в списке дисциплин для определения её позиции
                    for s in subjects:
                        if s.subjects.id == id_sub:
                            marks[k][s.n] = (res.id, res.mark)
                            break

        # добавляем студентам массив оценок
        for s in students:
            k_s = (s.fullname, s.student_id)
            for m in marks:
                if k_s == m:
                    s.marks = dict(zip(key, marks[m]))

        negative = ['ня', 'нз', '2']
        for m in students:
            # считаем количество задолженностей по каждому этапу аттестации
            cnt1, cnt2, cnt3 = 0, 0, 0
            for v in m.marks.values():
                if v == '-':
                    m.att1 = False
                    m.att2 = False
                    m.att3 = False
                else:
                    marks = v[1]
                    # список всех оценок студента
                    q_marks = len(marks)
                    match q_marks:
                        case 1:
                            if marks[0] in negative:
                                cnt1 += 1
                        case 2:
                            if marks[0] in negative:
                                cnt1 += 1
                            if marks[1] in negative:
                                cnt2 += 1
                        case 3:
                            if marks[0] in negative:
                                cnt1 += 1
                            if marks[1] in negative:
                                cnt2 += 1
                            if marks[2] in negative:
                                cnt3 += 1

            m.att1, m.att2, m.att3 = cnt1, cnt2, cnt3
            # print('----->>>>>', m.att1)
            # print('----->>>>>', m.att2)
            # print('----->>>>>', m.att3)

    ######### подсчет оценок для определения стипендии

            # исключаем все "-" из оценок
            all_marks = list(filter(lambda x: isinstance(x, tuple), m.marks.values()))
            # извлекаем все первые оценки в единый список
            all_marks = list(map(lambda x: x[1][0], all_marks))
            # считем количество каждого типа оценки
            all_marks = dict(Counter(all_marks))

            # условные критерии для определения типа стипендии
            no_marks_yet = not bool(len(all_marks))     # нет ни одной оценки
            is_C_marks = '3' in all_marks               # есть хотя бы одна 3-ка
            no_A_marks = not ('5' in all_marks)         # нет ни одной 5-ки
            no_B_marks = not ('4' in all_marks)         # нет ни одной 4-ки
            basis = m.basis

            if basis == 'Контракт':
                m.money = 'нет'
                m.save()
                # print('==========', 1)
            elif basis == 'ИГ':
                m.money = '1.0'
                m.save()
                # print('==========', 2)
            elif m.att1 > 0:
                m.money = 'нет'
                m.save()
                # print('==========', 3)
            elif no_marks_yet or is_C_marks:
                m.money = 'нет'
                m.save()
                # print('==========', 4)
            elif no_A_marks:
                m.money = '1.0'
                m.save()
                # print('==========', 5)
            elif no_B_marks:
                m.money = '1.5'
                m.save()
                # print('==========', 6)
            else:
                m.money = '1.25'
                m.save()
                # print('==========', 7)

            m.att1 = '' if not cnt1 else cnt1
            m.att2 = '' if not cnt2 else cnt2
            m.att3 = '' if not cnt3 else cnt3

        return students






