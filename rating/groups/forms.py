import re

from django.core.exceptions import ValidationError
from django.forms import ModelForm

from groups.models import Group


class GroupForm(ModelForm):
    """Форма добавления | обновления групп."""
    class Meta:
        model = Group
        fields = [
            'name',
            'direction',
            'profile',
            'level',
            'code',
            'is_archived',
        ]

    def clean_code(self):
        """Проверить формат шифра направления."""
        code = self.cleaned_data['code']
        pattern = r'^([0-9]{2})\.([0-9]{2})\.([0-9]{2})$'

        if not re.match(pattern, code):
            raise ValidationError('Неверный формат')
        return code
