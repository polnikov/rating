# Generated by Django 3.2.12 on 2022-11-09 15:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0006_subject_zet'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='groupsubject',
            options={'ordering': ['groups_id', 'subjects', '-att_date'], 'verbose_name': 'Назначения дисциплин', 'verbose_name_plural': 'Назначения дисциплин'},
        ),
        migrations.AlterModelOptions(
            name='subject',
            options={'ordering': ['name', 'semester', '-form_control', 'cathedra'], 'verbose_name': 'Дисциплины', 'verbose_name_plural': 'Дисциплины'},
        ),
        migrations.RemoveField(
            model_name='subject',
            name='att_date',
        ),
        migrations.RemoveField(
            model_name='subject',
            name='teacher',
        ),
        migrations.AddField(
            model_name='groupsubject',
            name='att_date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата аттестации'),
        ),
        migrations.AddField(
            model_name='groupsubject',
            name='comment',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Примечание'),
        ),
        migrations.AddField(
            model_name='groupsubject',
            name='teacher',
            field=models.CharField(blank=True, default='', help_text='Фамилия И.О.', max_length=150, verbose_name='Преподаватель'),
        ),
        migrations.AlterField(
            model_name='cathedra',
            name='faculty',
            field=models.ForeignKey(blank=True, default='', null=True, on_delete=django.db.models.deletion.SET_NULL, to='subjects.faculty', verbose_name='Факультет'),
        ),
        migrations.AlterField(
            model_name='subject',
            name='cathedra',
            field=models.ForeignKey(blank=True, default='', null=True, on_delete=django.db.models.deletion.SET_NULL, to='subjects.cathedra', verbose_name='Кафедра'),
        ),
    ]
