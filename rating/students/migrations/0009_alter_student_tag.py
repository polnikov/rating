# Generated by Django 3.2.12 on 2023-01-20 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0008_alter_studentlog_old_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='tag',
            field=models.CharField(blank=True, choices=[('из АО', 'из АО'), ('восстановлен', 'восстановлен'), ('перевелся на фак-т', 'перевелся на фак-т'), ('перевелся с фак-та', 'перевелся с фак-та'), ('целевой', 'целевой')], default='', max_length=25, verbose_name='Тэг'),
        ),
    ]