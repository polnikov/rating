# Generated by Django 3.2.12 on 2022-11-09 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0007_alter_studentlog_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentlog',
            name='old_value',
            field=models.TextField(max_length=255, null=True, verbose_name='Было'),
        ),
    ]