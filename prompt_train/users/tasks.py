from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60  # retry через 60 секунд
)
def send_registration_email_task(self, user_id):
    """
    Асинхронна відправка вітального email при реєстрації
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.get(id=user_id)

        if not user.email:
            logger.warning(f"Користувач {user.nickname} не має email адреси")
            return

        context = {
            "user_name": user.nickname,
            "username": user.nickname,
            "email": user.email,
            "site_url": settings.SITE_URL,
            "login_url": f"{settings.SITE_URL}/auth/login/",
        }

        html_message = render_to_string("users/welcome_email.html", context)
        
        send_mail(
            subject="👋 Ласкаво просимо до Prompt Trainer!",
            message=f"Вітаємо, {user.nickname}! Дякуємо за реєстрацію.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email відправлено користувачу {user.nickname}")
        return f"Email successfully sent to {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"Користувач з id {user_id} не знайдений")
        return f"User with id {user_id} not found"
    except Exception as exc:
        logger.error(f"Помилка при відправці email: {exc}")
        # Retry задачу до 3 разів з затримкою 60 секунд
        raise self.retry(exc=exc, countdown=60)


