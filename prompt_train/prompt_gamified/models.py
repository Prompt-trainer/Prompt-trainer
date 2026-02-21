from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

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
        ("S", "Silver"),
        ("G", "Gold"),
        ("R", "Ruby"),
        ("D", "Diamond"),
    ], null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.price}"
    
    def clean(self):
        if self.type == 'rank_ring' and self.type is not None:
            raise ValidationError("Рангові кільця не можуть мати ціни.")
        if self.type != 'rank_ring' and self.type is None:
            raise ValidationError("У цього елемента косметики має бути ціна.")


class UserCosmetic(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cosmetic = models.ForeignKey(Cosmetic, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True) # дата отримання елементу косметики
    active = models.BooleanField(default=False) # чи обраний елемент у користувача

    def __str__(self):
        return f"{self.user} - {self.cosmetic}, chosen: {self.active}"

    class Meta:
        # гарантує купівлю елемента косметики лише в одиничній кількості
        unique_together = ("user", "cosmetic")

    def activate_cosmetic(self, user, cosmetic):
        RING_TYPES = ["ring", "rang_ring"]

        # Робимо неактивними всі звичайні та рангові кільця
        # та активуємо вибране
        if self.cosmetic.type in RING_TYPES:
            UserCosmetic.objects.filter(
                user=self.user,
                cosmetic__type__in=RING_TYPES,
                active=True
            ).update(active=False)
        # Робимо неактивними елементи косметики такого ж типу (не відноситься до кілець)
        # та активуємо вибраний
        else:
            UserCosmetic.objects.filter(
                user=self.user,
                cosmetic__type=self.cosmetic.type,
                active=True
            ).update(active=False)

        self.active = True
        self.save()
