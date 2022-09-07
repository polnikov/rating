import datetime
import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import DateInput, MultiWidget, RadioSelect, TextInput, Input

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
    students = Input()
    groupsubject = Input()
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
        set_3 = ['ня', 'нз', '2']
        mark = self.cleaned_data['mark']  # список оценок
        subject_form_control = self.cleaned_data['groupsubject'].subjects.form_control
        mark_types = set_1 if subject_form_control in form_control_numeric else set_2

        if len(mark) == 0:
            raise ValidationError('Оценка не может быть пустой')
        # если оценка первая, проверяем соответствие форме контроля
        elif len(mark) == 1 and mark[0] not in mark_types:
            raise ValidationError(f'Оценка не соответствует форме контроля. Возможные оценки: {" ".join(mark_types)}')
        # если оценка вторая
        elif len(mark) == 2:
            # проверяем соответствие каждой оценки форме контроля
            if not set(mark).issubset(mark_types):
                raise ValidationError(f'Оценка не соответствует форме контроля. Возможные оценки: {" ".join(mark_types)}')
            # проверяем, что первая оценка отрицательная
            if mark[0] not in set_3:
                raise ValidationError('При выставлении второй оценки, первая не может быть положительной')
        # если оценка третья
        elif len(mark) == 3:
            # проверяем соответствие каждой оценки форме контроля
            if not set(mark).issubset(mark_types):
                raise ValidationError(f'Оценка не соответствует форме контроля. Возможные оценки: {" ".join(mark_types)}')
            # проверяем, что первые две оценки отрицательные
            if not set(mark[0:2]).issubset(set_3):
                raise ValidationError('При выставлении третьей оценки, первые две не могут быть положительными')

        return mark

########################################################################################################################
