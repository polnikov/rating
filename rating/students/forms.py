import datetime
import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import DateInput, MultiWidget, RadioSelect, TextInput, Input

from groups.models import Group
from students.models import Result, Student
from subjects.models import Subject, GroupSubject


class StudentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        self.fields['group'].queryset = Group.objects.filter(is_archived=False)

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
        student_id = self.cleaned_data['student_id']

        if isinstance(student_id, str) is True:
            raise ValidationError('Неверный формат')
        return student_id

    def clean_start_date(self):
        date = self.cleaned_data['start_date']
        pattern = r'^([0-9]{2})\.([0-9]{2})\.([0-9]{4})$'  # DD.MM.YYYY

        if not date or isinstance(date, datetime.date):
            return date
        elif not re.match(pattern, date):
            raise ValidationError('Неверный формат даты')
        else:
            return date


class ResultForm(forms.ModelForm):
    def __init__(self, subject_name=None, groups_names=None, *args, **kwargs):
        super(ResultForm, self).__init__(*args, **kwargs)
        if subject_name:
            self.fields['groupsubject'].queryset = GroupSubject.active_objects.filter(
                subjects__name=subject_name
            ).order_by(
                'groups__name',
                'subjects__semester__semester',
            )
        if groups_names:
            self.fields['students'].queryset = Student.active_objects.filter(group__name__in=groups_names)

    students = Input()
    groupsubject = Input()

    class Meta:
        model = Result
        fields = [
            'groupsubject',
            'students',
            'mark',
            'tag',
            'is_archived',
        ]
        widgets = {
            'mark': MultiWidget(widgets=[TextInput, TextInput, TextInput]),
            'tag': RadioSelect(),
        }

    def clean_mark(self):
        """Check that the mark corresponds to form control."""
        form_control_numeric = [Subject.Formcontrol.EXAM, Subject.Formcontrol.DIF, Subject.Formcontrol.KP, Subject.Formcontrol.KR]
        set_1 = ['ня', '2', '3', '4', '5']
        set_2 = ['ня', 'нз', 'зач']
        set_3 = ['ня', 'нз', '2']
        mark = self.cleaned_data['mark']  # list of marks
        subject_form_control = self.cleaned_data['groupsubject'].subjects.form_control
        mark_types = set_1 if subject_form_control in form_control_numeric else set_2

        # if no one mark
        if len(mark) == 0:
            raise ValidationError('Оценка не может быть пустой')
        # if it is the first mark
        elif len(mark) == 1 and mark[0] not in mark_types:
            raise ValidationError(f'Оценка не соответствует форме контроля. Возможные оценки: {" ".join(mark_types)}')
        # if it is the second mark
        elif len(mark) == 2:
            # check that every mark corresponds to form control
            if not set(mark).issubset(mark_types):
                raise ValidationError(f'Оценка не соответствует форме контроля. Возможные оценки: {" ".join(mark_types)}')
            # check that the first mark is negative
            if mark[0] not in set_3:
                raise ValidationError('При выставлении второй оценки, первая не может быть положительной')
        # if it is the third mark
        elif len(mark) == 3:
            # check that every mark corresponds to form control
            if not set(mark).issubset(mark_types):
                raise ValidationError(f'Оценка не соответствует форме контроля. Возможные оценки: {" ".join(mark_types)}')
            # check that two first marks are negative
            if not set(mark[0:2]).issubset(set_3):
                raise ValidationError('При выставлении третьей оценки, первые две не могут быть положительными')

        return mark
