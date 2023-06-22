import logging

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Student, StudentLog


logger = logging.getLogger(__name__)

@receiver(pre_delete, sender=Student)
def save_deleted_student(sender, instance, **kwargs):
    try:
        StudentLog.objects.create(
            record_id=instance.student_id,
            field='Удаление',
            old_value=f'{instance.fullname} [{instance.student_id}]',
            new_value='Удалён из базы',
        )
    except Exception as ex:
        logger.error(f'Не удалось сохранить информацию об удалении студента {instance.fullname}', extra={'Exception': ex})


pre_delete.connect(save_deleted_student, sender=Student)
