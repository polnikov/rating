from django import template
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404


register = template.Library()


@register.filter(name='get_user_last_name')
def get_user_last_name(id):
    """Возвращает фамилию пользователя по id. Если фамилия отсутствует - username"""
    user = get_object_or_404(User, id=id)
    if user.last_name:
        return user.last_name
    else:
        return user


@register.filter(name='date_or_else')
def date_or_else(value):
    """Преобразует дату: YYYY-MM-DD ---> DD.MM.YYYY."""
    if value != None:
        value = value.split('-')
        return f'{value[2]}.{value[1]}.{value[0]}'


@register.filter(name='unpack_mark')
def unpack_mark(value):
    """Извлекает оценку из списка."""
    if len(value) == 0:
        return ''
    else:
        return value[0]


@register.filter(name='unpack_marks')
def unpack_marks(value):
    """Преобразует список оценок в читаемый вид."""
    if len(value) == 0:
        return ''
    else:
        return ' '.join(value)


@register.filter(name='short_basis')
def short_basis(value):
    """Подменяет полное название основы обучения на первую заглавную букву."""
    return value.name[0]


@register.filter(name='short_form_control')
def short_form_control(value):
    """Подменяет полное название формы контроля на аббревиатуру."""
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
    """Проверяет принадлежность пользователя к группе."""
    return user.groups.filter(name=group_name).exists()
