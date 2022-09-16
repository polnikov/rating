from django.db import models
from django_currentuser.db.models import CurrentUserField


class CommonTimestampModel(models.Model):
   """Абстрактная модель для временных полей <Создано> и <Обновлено>."""
   created_date = models.DateTimeField(
      verbose_name='Запись создана',
      auto_now_add=True,
      )
   updated_date = models.DateTimeField(
      verbose_name='Запись обновлена',
      auto_now=True,
   )

   class Meta:
      abstract = True


class CommonArchivedModel(models.Model):
   """Абстрактная модель для поля <Архив>."""
   is_archived = models.BooleanField(
      verbose_name='Архив',
      default=False,
   )

   class Meta:
      abstract = True


class CommonModelLog(models.Model):
   """Модель <Логирование изменений модели>."""
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
      null=True,
   )
   new_value = models.TextField(
      verbose_name='Стало',
      max_length=255,
   )
   timestamp = models.DateTimeField(
      verbose_name='Дата и время изменения',
      auto_now=True
   )
   record_id = models.IntegerField(
      verbose_name='id записи',
   )

   class Meta:
      abstract = True
