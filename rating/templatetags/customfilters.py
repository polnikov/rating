from django import template
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from students.models import Student


register = template.Library()


@register.filter(name='get_user_last_name')
def get_user_last_name(id):
    """Returns the user's last name by id. If the last name is missing - username."""
    user = get_object_or_404(User, id=id)
    if user.last_name:
        return user.last_name
    else:
        return user


@register.filter(name='date_or_else')
def date_or_else(value):
    """Transforms a date: YYYY-MM-DD ---> DD.MM.YYYY."""
    if value != None:
        value = value.split('-')
        return f'{value[2]}.{value[1]}.{value[0]}'


@register.filter(name='unpack_mark')
def unpack_mark(value):
    """Retrieves a mark from the list."""
    if len(value) == 0:
        return ''
    else:
        return value[0]


@register.filter(name='get_last_mark')
def get_last_mark(value):
    """Retrieves the last mark from the list."""
    match len(value):
        case 1:
            return value[0]
        case 2:
            return value[1]
        case 3:
            return value[2]


@register.filter(name='unpack_marks')
def unpack_marks(value):
    """Transforms a mark's list into a readable view."""
    if len(value) == 0:
        return ''
    else:
        return ' '.join(value)


@register.filter(name='short_basis')
def short_basis(value):
    """Cuts a subject's form control to a first capital letter."""
    return value.name[0]


@register.filter(name='short_form_control')
def short_form_control(value):
    """Transforms a subject's form control into short name."""
    FORMCONTROL = {
        'Экзамен': 'Э',
        'Диффзачет': 'Д',
        'Зачет': 'З',
        'Курсовой проект': 'КП',
        'Курсовая работа': 'КР'
    }
    return FORMCONTROL.get(value)


@register.filter(name='has_group')
def has_group(user, group_name):
    """Checks if a user is a member of a group."""
    return user.groups.filter(name=group_name).exists()


@register.filter(name='get_student_fullname')
def get_student_fullname(id_number):
    """Returns the student's full name by id."""
    try:
        student = Student.objects.get(student_id=id_number)
        return student.fullname
    except ObjectDoesNotExist:
        return f'Удалён [{id_number}]'
