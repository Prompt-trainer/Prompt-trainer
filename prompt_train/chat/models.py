from django.db import models
from django.contrib.auth import get_user_model
from cryptography.fernet import Fernet
from django.conf import settings

User = get_user_model()

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.nickname}: {self.get_decrypted_content()[:50]}"

    @staticmethod
    def get_cipher():
        key = settings.CHAT_ENCRYPTION_KEY.encode() if isinstance(settings.CHAT_ENCRYPTION_KEY, str) else settings.CHAT_ENCRYPTION_KEY
        if len(key) != 44:
            key = Fernet.generate_key()
        return Fernet(key)

    def encrypt_content(self, plain_text):
        cipher = self.get_cipher()
        encrypted = cipher.encrypt(plain_text.encode())
        self.content = encrypted.decode()

    def get_decrypted_content(self):
        try:
            cipher = self.get_cipher()
            decrypted = cipher.decrypt(self.content.encode())
            return decrypted.decode()
        except:
            return self.content

    def save(self, *args, **kwargs):
        if not self.pk:  
            plain_text = self.content
            self.encrypt_content(plain_text)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
        ]
