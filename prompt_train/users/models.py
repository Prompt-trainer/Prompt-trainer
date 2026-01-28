from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields): 
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password) # Хешування паролю
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
    nickname = models.CharField(max_length=80)
    rank = models.CharField(max_length=20) # Тут мають бути choices (?)
    poins = models.IntegerField()
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    # Поле is_superuser відсутнє через наявність класу PermissionsMixin

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email" # Для скидання паролю
    REQUIRED_FIELDS = ["first_name", "second_name"]
    objects = CustomUserManager()

    def __str__(self):
        return f'{self.first_name} {self.second_name} - {self.email}'