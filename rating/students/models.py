import logging
from dateutil.relativedelta import relativedelta

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from django_better_admin_arrayfield.models.fields import ArrayField

from rating.abstracts import CommonArchivedModel, CommonTimestampModel, CommonModelLog


logger = logging.getLogger(__name__)


class ArchivedStudentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=True)


class ActiveStudentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)


class Student(CommonArchivedModel, CommonTimestampModel):
    objects = models.Manager()
    archived_objects = ArchivedStudentManager()
    active_objects = ActiveStudentManager()

    class Citizenship(models.TextChoices):
        RUS = 'Россия', 'Россия'
        INT = 'Иностранец', 'Иностранец'

    class Level(models.TextChoices):
        BAC = 'Бакалавриат', 'Бакалавриат'
        MAG = 'Магистратура', 'Магистратура'

    class Status(models.TextChoices):
        ACTIVE = 'Является студентом', 'Является студентом'
        DELAY = 'Академический отпуск', 'Академический отпуск'
        FIRED = 'Отчислен', 'Отчислен'
        GRADUATED = 'Выпускник', 'Выпускник'

    class Tag(models.TextChoices):
        FROM_DELAY = 'из АО', 'из АО'
        RETURNED = 'восстановлен', 'восстановлен'
        TRANSFER_IN = 'перевелся на фак-т', 'перевелся на фак-т'
        TRANSFER_OUT = 'перевелся с фак-та', 'перевелся с фак-та'
        GOV = 'целевой', 'целевой'

    class Money(models.TextChoices):
        D = 'нет', 'нет'
        C = '1.0', '1.0'
        B = '1.25', '1.25'
        A = '1.5', '1.5'


    student_id = models.IntegerField(
        verbose_name='Зачетная книжка',
        primary_key=True,
        blank=False,
        unique=True,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=30,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=30,
    )
    second_name = models.CharField(
        verbose_name='Отчество',
        max_length=30,
        blank=True,
        unique=False,
        default='',
    )
    basis = models.ForeignKey(
        'students.Basis',
        on_delete=models.SET_NULL,
        verbose_name='Основа обучения',
        null=True,
    )
    semester = models.ForeignKey(
        'students.Semester',
        on_delete=models.PROTECT,
        verbose_name='Семестр',
        default=1,
        blank=False,
    )
    citizenship = models.CharField(
        verbose_name='Гражданство',
        max_length=20,
        choices=Citizenship.choices,
        default=Citizenship.RUS,
        blank=False,
    )
    level = models.CharField(
        verbose_name='Уровень обучения',
        choices=Level.choices,
        default='Бакалавриат',
        blank=False,
        max_length=15,
    )
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.SET_NULL,
        verbose_name='Группа',
        null=True,
    )
    start_date = models.DateField(
        verbose_name='Дата зачисления',
        auto_now=False,
        auto_now_add=False,
    )
    status = models.CharField(
        verbose_name='Текущий статус',
        max_length=25,
        choices=Status.choices,
        default=Status.ACTIVE,
        blank=False,
    )
    tag = models.CharField(
        verbose_name='Тэг',
        max_length=25,
        choices=Tag.choices,
        blank=True,
        default='',
    )
    comment = models.CharField(
        verbose_name='Примечание',
        max_length=255,
        blank=True,
        unique=False,
        default='',
    )
    money = models.CharField(
        verbose_name='Стипендия',
        max_length=5,
        blank=False,
        choices=Money.choices,
        default=Money.D
    )

    class Meta:
        ordering = [
            'group',
            'semester',
            'last_name',
        ]
        verbose_name = 'Студенты'
        verbose_name_plural = 'Студенты'

    def __str__(self):
        return f'{self.last_name} {self.first_name} {self.second_name} | {self.group}-{self.semester}'

    def save(self, *args, **kwargs):
        # Checking if the object is exist
        if Student.objects.filter(student_id=self.pk).exists():
            if self.pk is not None:
                # Changing the model
                old_object = Student.objects.get(pk=self.pk)
                # Getting all model fields
                field_names = [field.name for field in Student._meta.fields]
                # Preparing a dict for changes
                update_fields = {}
                for field_name in field_names:
                    try:
                        if getattr(old_object, field_name) != getattr(self, field_name):
                            update_fields[field_name] = (
                                getattr(old_object, field_name), getattr(self, field_name))
                            update_fields['student_id'] = self.student_id
                    except Exception as ex:
                        logger.error(f'Изменения поля {old_object} студента {self.student_id} не удалось сохранить', extra={'Exception': ex})
            # Adding records to table
            try:
                for key in update_fields:
                    if key != 'student_id':
                        StudentLog.objects.create(
                            field=Student._meta.get_field(key).verbose_name,
                            old_value=update_fields[key][0],
                            new_value=update_fields[key][1],
                            record_id=update_fields['student_id'],
                        )
            except Exception as ex:
                logger.error(f'Не удалось сохранить изменения студента {self.student_id}', extra={'Exception': ex})

        # send student to archive if his status in (<Отчислен>, <АО>, <Выпускник>)
        if self.status in [Student.Status.FIRED, Student.Status.GRADUATED] or self.status == Student.Status.DELAY:
            self.is_archived = True
        else:
            self.is_archived = False

        # if student has basis equal <Контракт> - set a money for him <нет>
        if self.basis.name == 'Контракт':
            self.money = 'нет'

        super(Student, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('students:detail', args=[str(self.student_id)])

    @property
    def fullname(self):
        """Return full name."""
        return f'{self.last_name} {self.first_name} {self.second_name}'

    @property
    def is_ill(self):
        """Indicate if student is ill."""
        if 'болеет' in self.comment.lower():
            return True
        else:
            return False

    @property
    def course(self):
        """Return current student course."""
        match int(self.semester.semester):
            case 1 | 2:
                return '1'
            case 3 | 4:
                return '2'
            case 5 | 6:
                return '3'
            case 7 | 8:
                return '4'

    @property
    def graduate_year(self):
        """Return graduate year of the student."""
        if self.status == Student.Status.GRADUATED:
            match self.level:
                case Student.Level.BAC:
                    return self.start_date + relativedelta(years=4)
                case Student.Level.MAG:
                    return self.start_date + relativedelta(years=2)

    @property
    def money_rate(self):
        """Return money type of the student."""
        match self.money:
            case Student.Money.D:
                return 0
            case Student.Money.C:
                return 1
            case Student.Money.B:
                return 2
            case Student.Money.A:
                return 3


class StudentLog(CommonModelLog):
    """Модель <Логирование изменений по студентам>."""

    class Meta:
        verbose_name = 'Изменения по студентам'
        verbose_name_plural = "Изменения по студентам"
        ordering = [
            '-timestamp',
        ]

    def __str__(self):
        return f'{self.id}'


class Result(CommonArchivedModel, CommonTimestampModel, DynamicArrayMixin):
    MARK = (
        ('ня', 'ня'),
        ('нз', 'нз'),
        ('зач', 'зач'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    )
    mark = ArrayField(
        models.CharField(max_length=3, blank=True),
        size=3,
        blank=True,
        null=True,
        verbose_name='Оценка',
        default=list,
    )
    students = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        verbose_name='Студент',
    )
    groupsubject = models.ForeignKey(
        'subjects.GroupSubject',
        on_delete=models.CASCADE,
        verbose_name='Дисциплина',
        default='',
    )
    TAG = [
        ('СЗ', 'СЗ'),
    ]
    tag = models.CharField(
        verbose_name='Тэг',
        max_length=10,
        choices=TAG,
        blank=True,
        default='',
    )

    class Meta:
        verbose_name = 'Оценки'
        verbose_name_plural = 'Оценки'
        ordering = [
            'groupsubject',
            'students',
        ]
        unique_together = (
            ('students', 'groupsubject'),
        )

    def __str__(self):
        return f'{self.groupsubject} | {self.students} | {self.mark}'

    @property
    def empty_mark(self):
        """Делает пометку, если не указана оценка."""
        """Return <-> if the mark is empty."""
        if self.mark == None:
            return '-'
        else:
            return self.mark


class Basis(CommonTimestampModel):
    name = models.CharField(
        verbose_name='Основа обучения',
        max_length=20,
        unique=True,
    )

    class Meta:
        verbose_name = 'Основы обучения'
        verbose_name_plural = 'Основы обучения'

    def __str__(self):
        return f'{self.name}'


class Semester(models.Model):
    SEMESTER = [
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
        (6, 6),
        (7, 7),
        (8, 8),
    ]
    semester = models.IntegerField(
        verbose_name='Семестр',
        choices=SEMESTER,
        blank=False,
        unique=True,
        default=SEMESTER[0][1]
    )

    class Meta:
        verbose_name = 'Семестры'
        verbose_name_plural = 'Семестры'

    def __str__(self):
        return f'{self.semester}'
