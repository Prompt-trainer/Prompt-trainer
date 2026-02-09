from django.db import models
from django.contrib.auth import get_user_model
from cryptography.fernet import Fernet
from django.conf import settings
class Conversation(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        users = self.participants.all()[:2]
        return f"Conversation: {' & '.join([u.nickname for u in users])}"
    
    @classmethod
    def get_or_create_conversation(cls, user1, user2):
        conversation = cls.objects.filter(
            participants=user1
        ).filter(
            participants=user2
        ).first()
        
        if not conversation:
            conversation = cls.objects.create()
            conversation.participants.add(user1, user2)
        
        return conversation


class Message(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages',
        null=True,
        blank=True
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    
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
        except Exception as e:  
            print(f"Decryption error: {e}")
            return self.content  
    
    def save(self, *args, **kwargs):
        if not self.pk: 
            try:
                cipher = self.get_cipher()
                cipher.decrypt(self.content.encode())
            except Exception:
                plain_text = self.content
                self.encrypt_content(plain_text)
        
        super().save(*args, **kwargs)
        
        if self.conversation:
            Conversation.objects.filter(id=self.conversation.id).update(
                updated_at=self.timestamp
            )
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['conversation', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
