import itertools
from collections import Counter

from subjects.models import GroupSubject
from students.models import Result, Student

from django.db.models import Q


def _get_students_group_statistic_and_marks(groupname, semester, student=None):
    '''Сформировать статистику и оценки студентов группы. При указании в <student> ID студента, будет запрошена
    статистика только указанного студента.

    return if student=None: `objects`
    return if student: `list`
    '''
    negative = ['ня', 'нз', '2']
    # дисциплины, назначенные текущей группе в соответствующем семестре
    subjects = GroupSubject.active_objects.select_related().filter(
        groups__name=groupname, subjects__semester=semester).order_by(
        'subjects__form_control', 'subjects__name')

    # добавляем порядковую нумерацию дисциплин
    for n, s in enumerate(subjects):
        s.n = n

    # id всех назначенных дисциплин
    subjects_id = [i.subjects.id for i in subjects]
    # количество назначенных предметов
    q_sub = subjects.count()
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
        elif basis == 'ИГ' and (att1 > 0 or no_marks_yet or is_C_marks):
            student.money = '1.0'
            student.save()
        else:
            if att1 > 0:
                student.money = 'нет'
                student.save()
            elif no_marks_yet or is_C_marks:
                student.money = 'нет'
                student.save()
            elif no_A_marks:
                student.money = '1.0'
                student.save()
            elif no_B_marks:
                student.money = '1.5'
                student.save()
            else:
                student.money = '1.25'
                student.save()

        att1 = '' if not cnt1 else cnt1
        att2 = '' if not cnt2 else cnt2
        att3 = '' if not cnt3 else cnt3

        if '-' in marks:
            student.pass_session = False
            student.pass_resession = False
            student.pass_last = False
        elif all(map(lambda x: x[0] not in negative, marks)):
            student.pass_session = True
            student.pass_resession = False
            student.pass_last = False
        elif not att2:
            cnt_second_marks = len(list(filter(lambda x: len(x) == 2, marks)))
            if att1 == cnt_second_marks:
                student.pass_session = False
                student.pass_resession = True
                student.pass_last = False
            else:
                student.pass_session = False
                student.pass_resession = False
                student.pass_last = False
        elif not att3:
            cnt_third_marks = len(list(filter(lambda x: len(x) == 3, marks)))
            if att2 == cnt_third_marks:
                student.pass_session = False
                student.pass_resession = False
                student.pass_last = True
            else:
                student.pass_session = False
                student.pass_resession = False
                student.pass_last = False
        else:
            student.pass_session = False
            student.pass_resession = False
            student.pass_last = False

        return [student.money, att1, att2, att3, student.pass_session, student.pass_resession, student.pass_last]
    else:
        # студенты текущей группы
        students = Student.active_objects.select_related('basis', 'semester').filter(
            group__name=groupname, semester=semester).order_by('last_name')
        # существующие оценки студентов текущей группы по назначенным группе дисциплинам
        results = Result.objects.select_related().filter(groupsubject__groups__name=groupname,
                                                         groupsubject__subjects__semester=semester)

        # готовим структуру оценок по каждому студенту
        num_subjects = len(subjects)
        marks = {(i.fullname, i.student_id):['-' for i in range(num_subjects)] for i in students}

        # переносим результаты по каждому студенту
        for res in results:
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

            basis = m.basis.name
            if basis == 'Контракт':
                m.money = 'нет'
                m.save()
            else:
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

                if basis == 'ИГ' and (m.att1 > 0 or no_marks_yet or is_C_marks):
                    m.money = '1.0'
                    m.save()
                else:
                    if m.att1 > 0:
                        m.money = 'нет'
                        m.save()
                    elif no_marks_yet or is_C_marks:
                        m.money = 'нет'
                        m.save()
                    elif no_A_marks:
                        m.money = '1.0'
                        m.save()
                    elif no_B_marks:
                        m.money = '1.5'
                        m.save()
                    else:
                        m.money = '1.25'
                        m.save()

            m.att1 = '' if not cnt1 else cnt1
            m.att2 = '' if not cnt2 else cnt2
            m.att3 = '' if not cnt3 else cnt3
            
            student_marks = [i[1] for i in list(filter(lambda x: x != '-', [v for v in m.marks.values()]))]
            if '-' in [v for v in m.marks.values()]:
                m.pass_session = False
                m.pass_resession = False
                m.pass_last = False
            elif all(map(lambda x: x[0] not in negative, student_marks)):
                m.pass_session = True
                m.pass_resession = False
                m.pass_last = False
            elif not m.att2:
                cnt_second_marks = len(list(filter(lambda x: len(x) == 2, student_marks)))
                if m.att1 == cnt_second_marks:
                    m.pass_session = False
                    m.pass_resession = True
                    m.pass_last = False
                else:
                    m.pass_session = False
                    m.pass_resession = False
                    m.pass_last = False
            elif not m.att3:
                cnt_third_marks = len(list(filter(lambda x: len(x) == 3, student_marks)))
                if m.att2 == cnt_third_marks:
                    m.pass_session = False
                    m.pass_resession = False
                    m.pass_last = True
                else:
                    m.pass_session = False
                    m.pass_resession = False
                    m.pass_last = False
            else:
                m.pass_session = False
                m.pass_resession = False
                m.pass_last = False

        return students


def calculate_rating(student, start, stop=False):
    '''Рассчитать средний балл студента за семестр или период.'''
    if start and stop:
        # все оценки студента за указанный период
        marks = Result.objects.select_related().filter(
            students=student.student_id).filter(
            Q(groupsubject__subjects__semester__semester__gte=start) &
            Q(groupsubject__subjects__semester__semester__lte=stop)).filter(
            ~Q(groupsubject__subjects__form_control__exact='Зачет')).values('mark')
        # все аттестации для данного направления (группы) в указанном семестре, исключая зачеты
        atts = GroupSubject.objects.select_related('subjects').filter(
            groups=student.group,
        ).filter(Q(subjects__semester__semester__gte=start) & Q(subjects__semester__semester__lte=stop)
        ).filter(~Q(subjects__form_control__exact='Зачет'))
    elif start and not stop:
        # все оценки студента в указанном семестре
        marks = Result.objects.select_related().filter(
            students=student.student_id,
            groupsubject__subjects__semester__semester=start
        ).filter(~Q(groupsubject__subjects__form_control__exact='Зачет')).values('mark')
        # все аттестации для данного направления (группы) в указанном семестре, исключая зачеты
        atts = GroupSubject.objects.select_related('subjects').filter(
            groups=student.group,
            subjects__semester__semester=start,
        ).filter(~Q(subjects__form_control__exact='Зачет'))

    # вычисление среднего балла за семестр или период
    # берем только последнюю оценку и исключаем <ня> и <2>
    marks = list(filter(lambda x: x not in ['ня', '2'], [i['mark'][-1] for i in marks]))
    # количество аттестаций с оценками в семестре или за период
    num_atts = atts.count()
    # количество каждой из оценок <3 | 4 | 5>
    count_marks = dict(Counter(marks))
    try:
        rating = round(sum([int(k) * v for k, v in count_marks.items()]) / num_atts, 2)
    except ZeroDivisionError:
        rating = 0

    return rating
