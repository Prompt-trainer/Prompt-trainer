from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .tasks import send_registration_email_task
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def send_email_on_user_creation(sender, instance, created, **kwargs):
    """
    Відправка вітального email при створенні нового користувача.
    Працює для звичайної реєстрації та OAuth (Google, GitHub).
    """
    if created:
        logger.info(f"Новий користувач створений: {instance.email} (nickname: {instance.nickname})")
        
        send_registration_email_task.delay(instance.id)
        logger.info(f"Email task delayed для користувача {instance.id}")
