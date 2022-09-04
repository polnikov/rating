import datetime
import re
from dal import autocomplete
from django.core.exceptions import ValidationError
from django.forms import ModelForm, ModelChoiceField
from django.forms.widgets import DateInput, TextInput, Select

from subjects.models import Cathedra, Faculty, GroupSubject, Subject


class SubjectForm(ModelForm):
    """Форма модели <Основа обучения>."""
    cathedra = ModelChoiceField(queryset=Cathedra.objects.all())
    class Meta:
        model = Subject
        fields = [
            'name',
            # 'cathedra',
            'teacher',
            'form_control',
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
            'cathedra': autocomplete.ModelSelect2(url='subjects/cathedra-autocomplete')
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
    class Meta:
        model = GroupSubject
        fields = [
            'groups',
            'subjects',
        ]
