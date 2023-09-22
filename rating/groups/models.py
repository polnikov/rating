from django.db import models
from django.urls import reverse

from rating.abstracts import CommonArchivedModel, CommonTimestampModel


class Group(CommonTimestampModel, CommonArchivedModel):
    """Модель <Группа>."""

    class Level(models.TextChoices):
        BAC = 'Бакалавриат', 'Бакалавриат'
        MAG = 'Магистратура', 'Магистратура'

    name = models.CharField(
        verbose_name='Группа',
        max_length=20,
        unique=True,
    )
    direction = models.CharField(
        verbose_name='Направление подготовки',
        max_length=50,
    )
    profile = models.CharField(
        verbose_name='Профиль | Специализация',
        max_length=100,
        default='-',
    )
    level = models.CharField(
        verbose_name='Уровень обучения',
        choices=Level.choices,
        default=Level.BAC,
        blank=False,
        max_length=15,
    )
    code = models.CharField(
        verbose_name='Шифр направления',
        max_length=10,
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = [
            'level',
            'code',
            'name',
        ]


    def __str__(self):
        return f'{self.name}'

    def get_absolute_url(self):
        return reverse('groups:cards', args=[str(self.id)])
