import os
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_image_size(image):
    """Валідація розміру зображення (максимум 5MB)"""
    max_size_mb = 5
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'Розмір файлу не може перевищувати {max_size_mb}MB')


# Функція для визначення шляху зображення профіля
def get_profile_picture_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'profile_pictures/user_{instance.id}{ext}'


# Функція для визначення storage
def get_profile_picture_storage():
    if settings.USE_S3:
        from .storage_backends import MediaStorage
        return MediaStorage()
    from django.core.files.storage import default_storage
    return default_storage

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self.create_user(email, password, **extra_fields)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=80, unique=True)
    profile_picture = models.ImageField(
        upload_to=get_profile_picture_path,
        blank=True,
        null=True,
        storage=get_profile_picture_storage(),
        validators=[validate_image_size],
        help_text='Максимальний розмір: 5MB. Формати: JPG, PNG, GIF'
    )
    rank = models.CharField(
        max_length=20,
        choices=[
            ("B", "Bronze"),
            ("S", "Silver"),
            ("G", "Gold"),
            ("R", "Ruby"),
            ("D", "Diamond"),
        ],
        default="B",
    )
    points = models.IntegerField(default=0)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    exp = models.IntegerField(default=0)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["nickname"]
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.nickname} - {self.email}"

    def save(self, *args, **kwargs):
        # Видаляємо старе зображення, якщо воно було замінене
        if self.pk:
            try:
                old_instance = CustomUser.objects.get(pk=self.pk)
                if old_instance.profile_picture and old_instance.profile_picture != self.profile_picture:
                    old_instance.profile_picture.delete(save=False)
            except CustomUser.DoesNotExist:
                pass
        
        # Оновлення рангу на основі досвіду
        new_rank = self.rank
        if self.exp > 18:
            new_rank = "D"
        elif self.exp > 12:
            new_rank = "R"
        elif self.exp > 7:
            new_rank = "G"
        elif self.exp > 3:
            new_rank = "S"
        if self.rank != new_rank:
            self.rank = new_rank
        super().save(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def get_available_rang_rings(self):
        from prompt_gamified.models import Cosmetic

        RANK_ORDER = ['B', 'S', 'G', 'R', 'D']
        # Задаємо індекс рангу користувача
        user_rank_index = RANK_ORDER.index(self.rank)

        # Повертаємо лише рангові кільця, у яких
        # необхідний ранг не більше рангу користувача.
        return Cosmetic.objects.filter(
            type="rank_ring",
            # Наприклад, кільце 'G' з індексом 2 не попаде в user_rank_index зі значенням 1,
            # бо RANK_ORDER[:1 + 1] видає лише елементи з індексом 0 і 1
            rank_required__in=RANK_ORDER[:user_rank_index +1]
        )
    
    def buy_cosmetic(self, cosmetic):
        from prompt_gamified.models import UserCosmetic

        if cosmetic.type == "rang_ring":
            raise ValidationError("Рангові кільця не можуть бути купленими.")
        if UserCosmetic.objects.filter(user=self, cosmetic=cosmetic).exists():
            raise ValidationError("Не можна придбати вже куплений елемент косметики.")
        if self.points < cosmetic.price:
            raise ValidationError("Не вистачає поінтів на купівлю елемента косметики.")
        
        with transaction.atomic():
            self.points -= cosmetic.price
            self.save()

            UserCosmetic.objects.create(
                user=self, cosmetic=cosmetic
            )
