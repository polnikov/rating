from django.db import models
from django.urls import reverse

from rating.abstracts import CommonArchivedModel, CommonModelLog, CommonTimestampModel


class Subject(CommonArchivedModel, CommonTimestampModel):
    """Модель <Дисциплина>."""
    name = models.CharField(
        verbose_name='Дисциплина',
        max_length=150,
        blank=False,
        unique=False,
    )
    FORMCONTROL = (
        ('Экзамен', 'Экзамен'),
        ('Диффзачет', 'Диффзачет'),
        ('Зачет', 'Зачет'),
        ('Курсовой проект', 'Курсовой проект'),
        ('Курсовая работа', 'Курсовая работа'),
    )
    form_control = models.CharField(
        verbose_name='Форма контроля',
        choices=FORMCONTROL,
        blank=False,
        max_length=15,
    )
    semester = models.ForeignKey(
        'students.Semester',
        on_delete=models.PROTECT,
        verbose_name='Семестр',
        blank=False,
    )
    cathedra = models.ForeignKey(
        'subjects.Cathedra',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        default='',
        verbose_name='Кафедра',
    )
    zet = models.CharField(
        verbose_name='ЗЕТ',
        help_text='72 (2)',
        max_length=15,
        blank=True,
        default='',
        unique=False,
    )
    comment = models.CharField(
        verbose_name='Примечание',
        max_length=255,
        blank=True,
        unique=False,
        default='',
    )

    class Meta:
        verbose_name = 'Дисциплины'
        verbose_name_plural = 'Дисциплины'
        ordering = [
            'name',
            'semester',
            '-form_control',
            'cathedra',
        ]

    def __str__(self):
        if self.cathedra is None:
            return f'{self.name} | {self.form_control} | {self.semester} семестр | ***'
        else:
            return f'{self.name} | {self.form_control} | {self.semester} семестр | {self.cathedra.short_name}'

    def save(self, *args, **kwargs):
        # Проверяем, существует ли объект
        if Subject.objects.filter(id=self.pk).exists():
            if self.pk is not None:
                # Меняем модель
                old = Subject.objects.get(pk=self.pk)
                # получаем все поля модели
                field_names = [field.name for field in Subject._meta.fields]
                # готовим словарь для изменений
                update_fields = {}
                for field_name in field_names:
                    try:
                        if getattr(old, field_name) != getattr(self, field_name):
                            update_fields[field_name] = (
                                getattr(old, field_name), getattr(self, field_name))
                            update_fields['id'] = self.id
                    except Exception as ex:
                        print('[!] ---> Ошибка лога Subject', ex)
            # добавляем записи в таблицу
            try:
                for key in update_fields:
                    if key != 'id':
                        SubjectLog.objects.create(
                            field=Subject._meta.get_field(key).verbose_name,
                            old_value=update_fields[key][0],
                            new_value=update_fields[key][1],
                            record_id=update_fields['id'],
                        )
            except Exception as subject_log_ex:
                print(f'Не удалось записать изменения по дисциплинам:')
                print('[!] ---> Ошибка:', subject_log_ex)
        super(Subject, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('subjects:detail', args=[str(self.id)])

    @property
    def empty_cathedra(self):
        """Вернуть <Нет>, если кафедра не выбрана."""
        if not self.cathedra:
            return 'Нет'
        else:
            return self.cathedra

    @property
    def empty_zet(self):
        """Вернуть <Нет>, если ЗЕТ отсутствуют."""
        if not self.zet:
            return 'Нет'
        else:
            return self.zet


class SubjectLog(CommonModelLog):
    """Модель <Логирование изменений по дисциплинам>."""

    class Meta:
        verbose_name = 'Изменения в дисциплинах'
        verbose_name_plural = "Изменения в дисциплинах"
        ordering = [
            '-timestamp',
        ]

    def __str__(self):
        return f'{self.id}'

########################################################################################################################


class GroupSubject(CommonArchivedModel, CommonTimestampModel):
    """Модель <Назначение дисциплины группе>."""
    groups = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        verbose_name='Группа',
    )
    subjects = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        verbose_name='Дисциплина',
    )
    teacher = models.CharField(
        verbose_name='Преподаватель',
        help_text='Фамилия И.О.',
        max_length=150,
        blank=True,
        default='',
        unique=False,
    )
    att_date = models.DateField(
        verbose_name='Дата аттестации',
        auto_now=False,
        auto_now_add=False,
        unique=False,
        blank=True,
        null=True,
    )
    comment = models.CharField(
        verbose_name='Примечание',
        max_length=255,
        blank=True,
        unique=False,
        default='',
    )

    class Meta:
        verbose_name = 'Назначения дисциплин'
        verbose_name_plural = 'Назначения дисциплин'
        ordering = [
            'groups_id',
            'subjects',
            '-att_date',
        ]
        unique_together = (
            ('groups', 'subjects'),
        )

    def __str__(self):
        if self.teacher and not self.att_date:
            return f'{self.subjects} | {self.groups} | {self.teacher}'
        elif not self.teacher and self.att_date:
            return f'{self.subjects} | {self.groups} | {self.att_date}'
        elif not self.teacher and not self.att_date:
            return f'{self.subjects} | {self.groups}'
        else:
            return f'{self.subjects} | {self.groups} | {self.teacher} | {self.att_date}'

    def get_absolute_url(self):
        return reverse('subjects:groupsubject_update', args=[str(self.id)])

    @property
    def empty_att_date(self):
        """Делает пометку, где не указана дата аттестации."""
        if self.att_date == None or self.att_date == "":
            return 'Нет'
        else:
            return self.att_date

    @property
    def empty_teacher(self):
        """Делает пометку, где не указаны ФИО преподавателя."""
        if self.teacher == '':
            return 'Нет'
        else:
            return f'{self.teacher}'

########################################################################################################################


class Cathedra(CommonTimestampModel):
    """Модель <Кафедра>."""
    name = models.CharField(
        verbose_name='Кафедра',
        max_length=255,
        unique=True,
    )
    short_name = models.CharField(
        verbose_name='Сокращение',
        max_length=10,
        blank=True,
        default='',
    )
    faculty = models.ForeignKey(
        'subjects.Faculty',
        on_delete=models.SET_NULL,
        verbose_name='Факультет',
        blank=True,
        default='',
        null=True,
    )

    class Meta:
        verbose_name = 'Кафедры'
        verbose_name_plural = 'Кафедры'
        ordering = [
            'name',
        ]
        unique_together = (
            ('name', 'short_name', 'faculty'),
        )

    def __str__(self):
        return f'{self.name}'

    def get_absolute_url(self):
        return reverse('subjects:cathedra_update', args=[str(self.id)])

    @property
    def empty_short_name(self):
        """Вернуть <Нет>, если сокращение кафедры отсутствует."""
        if self.short_name == None:
            return 'Нет'
        else:
            return self.short_name

    @property
    def empty_faculty(self):
        """Вернуть <Нет>, если факультет кафедры отсутствует."""
        if self.faculty == None:
            return 'Нет'
        else:
            return self.faculty

########################################################################################################################


class Faculty(CommonTimestampModel):
    """Модель <Факультет>."""
    name = models.CharField(
        verbose_name='Полное название факультета',
        max_length=255,
    )
    short_name = models.CharField(
        verbose_name='Сокращение (аббревиатура)',
        max_length=10,
    )

    class Meta:
        verbose_name = 'Факультеты'
        verbose_name_plural = 'Факультеты'
        ordering = [
            'name',
        ]

    def __str__(self):
        return f'{self.name}'
