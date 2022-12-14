# Generated by Django 3.2.12 on 2022-08-15 18:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_currentuser.db.models.fields
import django_currentuser.middleware


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Basis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True, verbose_name='Основа обучения')),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='Запись создана')),
                ('updated_date', models.DateTimeField(auto_now=True, verbose_name='Запись обновлена')),
            ],
            options={
                'verbose_name': 'Основы обучения',
                'verbose_name_plural': 'Основы обучения',
            },
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mark', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=3), blank=True, default=list, null=True, size=3, verbose_name='Оценка')),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='Запись создана')),
                ('updated_date', models.DateTimeField(auto_now=True, verbose_name='Запись обновлена')),
            ],
            options={
                'verbose_name': 'Оценки',
                'verbose_name_plural': 'Оценки',
                'ordering': ['groupsubject', 'students'],
            },
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)], default=1, unique=True, verbose_name='Семестр')),
            ],
            options={
                'verbose_name': 'Семестры',
                'verbose_name_plural': 'Семестры',
            },
        ),
        migrations.CreateModel(
            name='StudentLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field', models.CharField(max_length=25, verbose_name='Свойство')),
                ('old_value', models.TextField(max_length=255, verbose_name='Было')),
                ('new_value', models.TextField(max_length=255, verbose_name='Стало')),
                ('timestamp', models.DateTimeField(auto_now=True, verbose_name='Дата и время изменения')),
                ('record_id', models.IntegerField(verbose_name='id записи')),
                ('user', django_currentuser.db.models.fields.CurrentUserField(default=django_currentuser.middleware.get_current_authenticated_user, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
            ],
            options={
                'verbose_name': 'Изменения по студентам',
                'verbose_name_plural': 'Изменения по студентам',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('student_id', models.IntegerField(primary_key=True, serialize=False, unique=True, verbose_name='Зачетная книжка')),
                ('last_name', models.CharField(max_length=30, verbose_name='Фамилия')),
                ('first_name', models.CharField(max_length=30, verbose_name='Имя')),
                ('second_name', models.CharField(blank=True, default='', max_length=30, verbose_name='Отчество')),
                ('citizenship', models.CharField(choices=[('Россия', 'Россия'), ('Иностранец', 'Иностранец')], default='Россия', max_length=20, verbose_name='Гражданство')),
                ('level', models.CharField(choices=[('Бакалавриат', 'Бакалавриат'), ('Магистратура', 'Магистратура')], default='Бакалавриат', max_length=15, verbose_name='Уровень обучения')),
                ('start_date', models.DateField(verbose_name='Дата зачисления')),
                ('status', models.CharField(choices=[('Является студентом', 'Является студентом'), ('Академический отпуск', 'Академический отпуск'), ('Отчислен', 'Отчислен'), ('Выпускник', 'Выпускник')], default='Является студентом', max_length=25, verbose_name='Текущий статус')),
                ('tag', models.CharField(blank=True, choices=[('из АО', 'из АО'), ('восстановлен', 'восстановлен'), ('перевелся на фак-т', 'перевелся на фак-т'), ('перевелся с фак-та', 'перевелся с фак-та')], max_length=25, verbose_name='Тэг')),
                ('comment', models.CharField(blank=True, default='', max_length=255, verbose_name='Примечание')),
                ('money', models.CharField(choices=[('нет', 'нет'), ('1.0', '1.0'), ('1.25', '1.25'), ('1.5', '1.5')], default='нет', max_length=5, verbose_name='Стипендия')),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='Запись создана')),
                ('updated_date', models.DateTimeField(auto_now=True, verbose_name='Запись обновлена')),
                ('basis', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='students.basis', verbose_name='Основа обучения')),
                ('group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='groups.group', verbose_name='Группа')),
                ('semester', models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='students.semester', verbose_name='Семестр')),
            ],
            options={
                'verbose_name': 'Студенты',
                'verbose_name_plural': 'Студенты',
                'ordering': ['group', 'last_name', '-status'],
            },
        ),
    ]
