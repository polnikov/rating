import datetime
import re

from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.forms.widgets import DateInput, TextInput, Input

from groups.models import Group
from subjects.models import Cathedra, Faculty, GroupSubject, Subject


class SubjectForm(ModelForm):
    """Форма модели <Основа обучения>."""
    class Meta:
        model = Subject
        fields = [
            'name',
            'cathedra',
            'form_control',
            'zet',
            'semester',
            'comment',
            'is_archived',
        ]

    def clean_zet(self):
        """Проверить формат ЗЕТ."""
        zet = self.cleaned_data['zet']
        pattern = r'^([0-9]{2,3})\s\(([0-9]{1,2})\)$'  # 72 (2)

        if not zet:
            return zet
        elif not re.match(pattern, zet):
            raise ValidationError('Неверный формат ЗЕТ')
        else:
            return zet

########################################################################################################################


class FacultyForm(ModelForm):
    """Форма модели <Факультет>."""
    class Meta:
        model = Faculty
        fields = [
            'name',
            'short_name',
        ]

########################################################################################################################


class CathedraForm(ModelForm):
    """Форма модели <Кафедра>."""
    class Meta:
        model = Cathedra
        fields = [
            'name',
            'short_name',
            'faculty',
        ]
        widgets = {
            'name': TextInput(
                attrs={'placeholder': 'без слова <кафедра>'},
            ),
            'short_name': TextInput(
                attrs={'placeholder': 'пример: КСФиХ'},
            ),
        }

########################################################################################################################


class GroupSubjectForm(ModelForm):
    """Форма модели <Назначение дисциплины>."""
    def __init__(self, *args, **kwargs):
        super(GroupSubjectForm, self).__init__(*args, **kwargs)
        self.fields['groups'].queryset = Group.objects.filter(is_archived=False)
        self.fields['subjects'].queryset = Subject.objects.filter(is_archived=False).order_by('semester')

    subjects = Input()

    class Meta:
        model = GroupSubject
        fields = [
            'groups',
            'subjects',
            'teacher',
            'att_date',
            'comment',
            'is_archived',
        ]
        widgets = {
            'att_date': DateInput(
                attrs={'placeholder': '24.06.1999'},
                format='%d.%m.%Y',
            ),
            'teacher': TextInput(
                attrs={'placeholder': 'Формат: Иванов И.И.'},
            ),
        }

    def clean_teacher(self):
        """Проверить формат ФИО преподавателя."""
        raw_teachers = self.cleaned_data['teacher']
        if not raw_teachers:
            return ''
        else:
            teachers = check_teachers_name(raw_teachers)

        if teachers:
            return teachers
        else:
            raise ValidationError('Неверный формат ФИО')

    def clean_att_date(self):
        """Проверить формат даты."""
        date = self.cleaned_data['att_date']
        pattern = r'^([0-9]{2})\.([0-9]{2})\.([0-9]{4})$'  # DD.MM.YYYY

        if not date or isinstance(date, datetime.date):
            return date
        elif not re.match(pattern, date):
            raise ValidationError('Неверный формат даты')
        else:
            return date


def check_teachers_name(names: list):
    pattern_1 = r'^(\w{1,})\s(\w{1})\.(\w{1})\.$'  # Фамилия И.О.
    pattern_2 = r'^(\w{1,})-(\w{1,})\s(\w{1})\.(\w{1})\.$'  # Фамилия-Фамилия И.О.
    teachers = []
    raw_teachers = names.split(', ')

    if len(raw_teachers) == 1:  # ['Фамилия И.О.']
        teacher = raw_teachers[0]
        if not teacher:
            return False
        elif re.match(pattern_1, teacher) or re.match(pattern_2, teacher):
            return teacher
        else:
            return False
    else:
        for name in raw_teachers:  # ['Фамилия1 И.О.', 'Фамилия1 И.О.']
            if not re.match(pattern_1, name) or re.match(pattern_2, name):
                return False
            else:
                teachers.append(name)
        return ', '.join(teachers)
