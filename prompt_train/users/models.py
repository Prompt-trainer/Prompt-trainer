from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Хешування паролю
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
    points = models.IntegerField(default=0)# валюта на платформі
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    exp = models.IntegerField(default=0)
    # Поле is_superuser відсутнє через наявність класу PermissionsMixin

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"  # Для скидання паролю
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