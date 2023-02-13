from subjects.models import Subject


def validate_mark(mark):
    negative_set = ['ня', 'нз', '2']

    # if no one mark
    if len(mark) == 0:
        return (False, 'Оценка не может быть пустой')
    # if it is the second mark
    elif len(mark) == 2:
        # checking that the first mark is negative
        if mark[0] not in negative_set:
            return (False, 'При выставлении второй оценки, первая не может быть положительной')
    # if it is the third mark
    elif len(mark) == 3:
        # checking that the first two marks is negative
        if not set(mark[0:2]).issubset(negative_set):
            return (False, 'При выставлении третьей оценки, первые две не могут быть положительными')

    return True


def check_mark(mark, form):
    """Check that the mark corresponds to form control."""
    form_control_numeric = [Subject.Formcontrol.EXAM, Subject.Formcontrol.DIF, Subject.Formcontrol.KP, Subject.Formcontrol.KR]
    set_1 = ['ня', '2', '3', '4', '5']
    set_2 = ['ня', 'нз', 'зач']
    mark_types = set_1 if form in form_control_numeric else set_2

    if mark not in mark_types:
        return False
    else:
        return True
