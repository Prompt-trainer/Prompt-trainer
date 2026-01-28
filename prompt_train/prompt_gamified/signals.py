from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
import logging

from .models import Cart, Product
from ..users.tasks import send_cart_notification_email_task, send_welcome_email_task

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """
    Відправляє вітальний email через Celery після реєстрації
    """
    if created:
        """Використовуємо transaction.on_commit щоб переконатися,
        що користувач збережений у БД перед відправкою task"""
        transaction.on_commit(lambda: send_welcome_email_task.delay(instance.id))
        logger.info(f"Welcome email task queued for user {instance.username}")
