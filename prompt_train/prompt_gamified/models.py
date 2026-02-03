from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from users.models import CustomUser


class Prompt(models.Model):
    prompt_text = models.CharField(max_length=500)
    improvement_hint = models.CharField(max_length=164)
    rate = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=1,
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.user} - '{self.prompt_text}'."


# Має бути модель для гри з оцінюванням промптів, які можна задати через адмінку.
