from django.db import models


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
