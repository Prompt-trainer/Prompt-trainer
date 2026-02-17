from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_image_size(image):
    """Валідація розміру зображення (максимум 5MB)"""
    max_size_mb = 5
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'Розмір файлу не може перевищувати {max_size_mb}MB')


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
        upload_to='profile_pictures/',
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
