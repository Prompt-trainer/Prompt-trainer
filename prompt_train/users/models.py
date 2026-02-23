import os
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
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
    
    # Активні елементи косметики, які відображаються в профілі користувача
    active_ring = models.ForeignKey(
        'Cosmetic',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='active_ring_users'
    )
    active_element = models.ForeignKey(
        'Cosmetic',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='active_element_users'
    )
    active_title = models.ForeignKey(
        'Cosmetic',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='active_title_users'
    )

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["nickname"]
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.nickname} - {self.email}"

    def save(self, *args, **kwargs):
        # Визначаємо, чи це новий користувач
        is_new = self.pk is None

        # Видаляємо старе зображення, якщо воно було замінене
        if not is_new:
            try:
                old_instance = CustomUser.objects.get(pk=self.pk)
                if old_instance.profile_picture and old_instance.profile_picture != self.profile_picture:
                    old_instance.profile_picture.delete(save=False)
            except CustomUser.DoesNotExist:
                pass
        
        # Оновлення рангу на основі досвіду
        old_rank = self.rank
        new_rank = self.rank
        if self.exp > 18:
            new_rank = "D"
        elif self.exp > 12:
            new_rank = "R"
        elif self.exp > 7:
            new_rank = "G"
        elif self.exp > 3:
            new_rank = "S"
        if old_rank != new_rank:
            self.rank = new_rank
        
        super().save(*args, **kwargs)

        # Додаємо бронзову рангову рамку для нового користувача
        if is_new:
            bronze_ring = Cosmetic.objects.filter(
                type="rank_ring",
                rank_required="B"
            ).first()
            if bronze_ring:
                UserCosmetic.objects.get_or_create(user=self, cosmetic=bronze_ring)

        # Додаємо всі доступні рангові рамки, якщо ранг змінився
        if old_rank != new_rank and self.pk:
            available_rings = self.get_available_rank_rings()
            if available_rings.exists():
                with transaction.atomic():
                    for ring in available_rings:
                        UserCosmetic.objects.get_or_create(user=self, cosmetic=ring)

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def get_available_rank_rings(self):
        RANK_ORDER = ['B', 'S', 'G', 'R', 'D']
        # Задаємо індекс рангу користувача
        try:
            user_rank_index = RANK_ORDER.index(self.rank)
        except ValueError:
            return Cosmetic.objects.none()

        # Повертаємо лише рангові кільця, у яких необхідний ранг не більше рангу користувача.
        return Cosmetic.objects.filter(
            type="rank_ring",
            rank_required__in=RANK_ORDER[:user_rank_index + 1]
        )
    
    def buy_cosmetic(self, cosmetic):
        if cosmetic.type == "rank_ring":
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


class Cosmetic(models.Model):
    name = models.CharField(max_length=50)
    price = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        default=1, null=True, blank=True) # рангове кільце не має ціни
    svg_code = models.CharField()
    type = models.CharField(max_length=20, choices=[
        ("ring", "Ring"),
        ("rank_ring", "Rank ring"),
        ("element", "Element"),
        ("title", "Title")
    ], default="ring")
    # Задає, чи потрібен конкретний ранг для можливості мати елемент косметики.
    # Потрібно задавати null для всіх елементів косметики з типом НЕ rank_ring
    rank_required = models.CharField(max_length=1, choices=[
        ("B", "Bronze"),
        ("S", "Silver"),
        ("G", "Gold"),
        ("R", "Ruby"),
        ("D", "Diamond"),
    ], null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.price}"
    
    def clean(self):
        if self.type == 'rank_ring' and self.price is not None:
            raise ValidationError("Рангові кільця не можуть мати ціни.")
        if self.type != 'rank_ring' and self.price is None:
            raise ValidationError("У цього елемента косметики має бути ціна.")


class UserCosmetic(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cosmetic = models.ForeignKey(Cosmetic, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True) # дата отримання елементу косметики

    def __str__(self):
        return f"{self.user} - {self.cosmetic}"

    class Meta:
        # гарантує купівлю елемента косметики лише в одиничній кількості
        unique_together = ("user", "cosmetic")

    def activate_cosmetic(self):
        """Активує косметику для користувача, оновлюючи відповідні поля в CustomUser"""
        user = self.user
        
        # Оновлюємо відповідне поле в CustomUser в залежності від типу косметики
        if self.cosmetic.type in ["ring", "rank_ring"]:
            user.active_ring = self.cosmetic
        elif self.cosmetic.type == "element":
            user.active_element = self.cosmetic
        elif self.cosmetic.type == "title":
            user.active_title = self.cosmetic
        
        user.save()
