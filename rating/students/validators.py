def validate_mark(mark):
    negative_set = ['ня', 'нз', '2']

    if len(mark) == 0:
        return (False, 'Оценка не может быть пустой')
    # если оценка вторая
    elif len(mark) == 2:
        # проверяем, что первая оценка отрицательная
        if mark[0] not in negative_set:
            return (False, 'При выставлении второй оценки, первая не может быть положительной')
    # если оценка третья
    elif len(mark) == 3:
        # проверяем, что первые две оценки отрицательные
        if not set(mark[0:2]).issubset(negative_set):
            return (False, 'При выставлении третьей оценки, первые две не могут быть положительными')

    return True


def check_mark(mark, form):
    """Проверить соответствие оценки форме контроля дисциплины."""
    form_control_numeric = ['Экзамен', 'Диффзачет', 'Курсовой проект', 'Курсовая работа']
    set_1 = ['ня', '2', '3', '4', '5']
    set_2 = ['ня', 'нз', 'зач']
    mark_types = set_1 if form in form_control_numeric else set_2

    if mark not in mark_types:
        return False
    else:
        return True
