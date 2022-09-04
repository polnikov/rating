from django.db import models
from django.db.models.fields import IntegerField
from django.urls import reverse
from django.utils.translation import gettext as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from django_better_admin_arrayfield.models.fields import ArrayField
from django_currentuser.db.models import CurrentUserField

from rating.abstracts import CommonArchivedModel, CommonTimestampModel


class Student(CommonArchivedModel, CommonTimestampModel):
    """Модель <Студент>."""
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
    CITIZENSHIP = [
        ('Россия', 'Россия'),
        ('Иностранец', 'Иностранец'),
    ]
    citizenship = models.CharField(
        verbose_name='Гражданство',
        max_length=20,
        choices=CITIZENSHIP,
        default=CITIZENSHIP[0][1],
        blank=False,
    )
    LEVEL = [
        ('Бакалавриат', 'Бакалавриат'),
        ('Магистратура', 'Магистратура'),
    ]
    level = models.CharField(
        verbose_name='Уровень обучения',
        choices=LEVEL,
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
    STATUS = [
        ('Является студентом', 'Является студентом'),
        ('Академический отпуск', 'Академический отпуск'),
        ('Отчислен', 'Отчислен'),
        ('Выпускник', 'Выпускник'),
    ]
    status = models.CharField(
        verbose_name='Текущий статус',
        max_length=25,
        choices=STATUS,
        default=STATUS[0][1],
        blank=False,
    )
    TAG = [
        ('из АО', 'из АО'),
        ('восстановлен', 'восстановлен'),
        ('перевелся на фак-т', 'перевелся на фак-т'),
        ('перевелся с фак-та', 'перевелся с фак-та'),
    ]
    tag = models.CharField(
        verbose_name='Тэг',
        max_length=25,
        choices=TAG,
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
    MONEY = [
        ('нет', 'нет'),
        ('1.0', '1.0'),
        ('1.25', '1.25'),
        ('1.5', '1.5'),
    ]
    money = models.CharField(
        verbose_name='Стипендия',
        max_length=5,
        blank=False,
        choices=MONEY,
        default=MONEY[0][1]
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
        # Проверяем, существует ли объект
        if Student.objects.filter(student_id=self.pk).exists():
            if self.pk is not None:
                # Меняем модель
                old_object = Student.objects.get(pk=self.pk)
                # получаем все поля модели
                field_names = [field.name for field in Student._meta.fields]
                # готовим словарь для изменений
                update_fields = {}
                for field_name in field_names:
                    try:
                        if getattr(old_object, field_name) != getattr(self, field_name):
                            update_fields[field_name] = (
                                getattr(old_object, field_name), getattr(self, field_name))
                            update_fields['student_id'] = self.student_id
                    except Exception as ex:
                        print('[!] ---> Ошибка лога Student', ex)
            # добавляем записи в таблицу
            try:
                for key in update_fields:
                    if key != 'student_id':
                        StudentLog.objects.create(
                            field=Student._meta.get_field(key).verbose_name,
                            old_value=update_fields[key][0],
                            new_value=update_fields[key][1],
                            record_id=update_fields['student_id'],
                        )
            except Exception as student_log_ex:
                print(f'Не удалось записать изменения по студентам:')
                print('[!] ---> Ошибка:', student_log_ex)
        super(Student, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('students:detail', args=[str(self.student_id)])

    @property
    def fullname(self):
        """Возвращает полное ФИО."""
        return f'{self.last_name} {self.first_name} {self.second_name}'

    @property
    def is_ill(self):
        """Отмечает студентов, у которых в примечании есть запись <болеет>."""
        if 'болеет' in self.comment.lower():
            return True
        else:
            return False

    @property
    def course(self):
        """Возвращает текущий курс студента."""
        match int(self.semester.semester):
            case 1 | 2:
                return '1'
            case 3 | 4:
                return '2'
            case 5 | 6:
                return '3'
            case 7 | 8:
                return '4'

    def get_data(self):
        return {
            'student_id': self.student_id,
            'last_name': self.last_name,
            'first_name': self.first_name,
            'second_name': self.second_name,
            # 'basis': self.basis,
            'citizenship': self.citizenship,
            'level': self.level,
            # 'group': self.group,
            'start_date': self.start_date,
            'status': self.status,
            'comment': self.comment,
            'money': self.money,
            'created_date': self.created_date,
            'updated_date': self.updated_date,
        }


class StudentLog(models.Model):
    """Модель <Логирование изменений по студентам>."""
    user = CurrentUserField(
        verbose_name='Автор',
    )
    field = models.CharField(
        verbose_name='Свойство',
        max_length=25
    )
    old_value = models.TextField(
        verbose_name='Было',
        max_length=255,
    )
    new_value = models.TextField(
        verbose_name='Стало',
        max_length=255,
    )
    timestamp = models.DateTimeField(
        verbose_name='Дата и время изменения',
        auto_now=True
    )
    record_id = IntegerField(
        verbose_name='id записи',
    )

    class Meta:
        verbose_name = 'Изменения по студентам'
        verbose_name_plural = "Изменения по студентам"
        ordering = [
            '-timestamp',
        ]

    def __str__(self):
        return f'{self.id}'

########################################################################################################################

class Result(CommonArchivedModel, CommonTimestampModel, DynamicArrayMixin):
    """Модель <Результат>."""
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
        null = True,
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
        default=''
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

    def get_absolute_url(self):
        return reverse('students:result-detail', args=[str(self.id)])

    @property
    def empty_mark(self):
        """Делает пометку, если не указана оценка."""
        if self.mark == None:
            return '-'
        else:
            return self.mark

########################################################################################################################

class Basis(CommonTimestampModel):
    """Модель <Основа обучения>."""
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

########################################################################################################################

class Semester(models.Model):
    """Модель <Семестр>."""
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
