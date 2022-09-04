import datetime
import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import DateInput, MultiWidget, RadioSelect, TextInput

from students.models import Result, Student


class StudentForm(forms.ModelForm):
    """Форма модели <Студент>"""
    class Meta:
        model = Student
        fields = [
            'last_name',
            'first_name',
            'second_name',
            'student_id',
            'citizenship',
            'basis',
            'level',
            'group',
            'semester',
            'start_date',
            'money',
            'status',
            'tag',
            'comment',
            'is_archived',
        ]
        widgets = {
            'student_id': TextInput(
                attrs={
                    'class': 'form-control',
                }),
            'start_date': DateInput(
                attrs={'placeholder': '24.06.1999'},
                format='%d.%m.%Y',
            ),
            'status': RadioSelect(),
            'tag': RadioSelect(),
            'money': RadioSelect(),
        }

    def clean_student_id(self):
        """Проверить формат номера зачетной книжки."""
        student_id = self.cleaned_data['student_id']

        if isinstance(student_id, str) is True:
            raise ValidationError('Неверный формат')
        return student_id

    def clean_start_date(self):
        """Проверить формат даты."""
        date = self.cleaned_data['start_date']
        pattern = r'^([0-9]{2})\.([0-9]{2})\.([0-9]{4})$'  # DD.MM.YYYY

        if not date or isinstance(date, datetime.date):
            return date
        elif not re.match(pattern, date):
            raise ValidationError('Неверный формат даты')
        else:
            return date

########################################################################################################################

class ResultForm(forms.ModelForm):
    """Форма модели <Оценка>"""
    class Meta:
        model = Result
        fields = [
            'groupsubject',
            'students',
            'mark',
            'tag',
        ]
        widgets = {
            'mark': MultiWidget(widgets=[TextInput, TextInput, TextInput]),
            'tag': RadioSelect(),
        }

    def clean_mark(self):
        """Проверить формат соответствия оценки форме контроля дисциплины."""
        form_control_numeric = ['Экзамен', 'Диффзачет', 'Курсовой проект', 'Курсовая работа']
        set_1 = ['ня', '2', '3', '4', '5']
        set_2 = ['ня', 'нз', 'зач']
        mark = self.cleaned_data['mark']
        subject_form_control = self.cleaned_data['groupsubject'].subjects.form_control
        mark_types = set_1 if subject_form_control in form_control_numeric else set_2

        if len(mark) != 0 and not set(mark).issubset(mark_types):
            raise ValidationError(f'Оценка не соответствует форме контроля. Возможные оценки: {" ".join(mark_types)}')
        return mark

########################################################################################################################
