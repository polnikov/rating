import datetime
import re
from django.core.exceptions import ValidationError
from django.forms import ModelForm, ModelChoiceField
from django.forms.widgets import DateInput, TextInput, Select, Input

from subjects.models import Cathedra, Faculty, GroupSubject, Subject


class SubjectForm(ModelForm):
    """Форма модели <Основа обучения>."""
    class Meta:
        model = Subject
        fields = [
            'name',
            'cathedra',
            'teacher',
            'form_control',
            'zet',
            'semester',
            'att_date',
            'comment',
            'is_archived',
        ]
        widgets = {
            'att_date': DateInput(
                attrs={'placeholder': '24.06.1999'},
                format='%d.%m.%Y',
            ),
        }

    def clean_teacher(self):
        """Проверить формат ФИО преподавателя."""
        teacher = self.cleaned_data['teacher']
        pattern_1 = r'^(\w{1,})\s(\w{1})\.(\w{1})\.$'  # Фамилия И.О.
        pattern_2 = r'^(\w{1,})-(\w{1,})\s(\w{1})\.(\w{1})\.$'  # Фамилия-Фамилия И.О.

        if not teacher:
            return teacher
        elif re.match(pattern_1, teacher) or re.match(pattern_2, teacher):
            return teacher
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

    def clean_zet(self):
        """Проверить формат ЗЕТ."""
        zet = self.cleaned_data['zet']
        pattern = r'^([0-9]{2,3})\s\(([0-9]{1,2})\)'  # 72 (2)

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
    subjects = Input()
    class Meta:
        model = GroupSubject
        fields = [
            'groups',
            'subjects',
        ]
