from django.test import TestCase
from django.utils import timezone
from chat.models import Conversation, Message
from users.models import CustomUser
from cryptography.fernet import Fernet
from django.conf import settings


class ConversationModelTest(TestCase):
    """Тести для моделі Conversation"""

    def setUp(self):
        """Створення тестових користувачів"""
        self.user1 = CustomUser.objects.create_user(
            email="user1@test.com", password="pass123", nickname="user1"
        )
        self.user2 = CustomUser.objects.create_user(
            email="user2@test.com", password="pass123", nickname="user2"
        )
        self.user3 = CustomUser.objects.create_user(
            email="user3@test.com", password="pass123", nickname="user3"
        )

    def test_conversation_creation(self):
        """Перевірка створення розмови"""
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)

        self.assertEqual(conversation.participants.count(), 2)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user2, conversation.participants.all())

    def test_conversation_str_representation(self):
        """Перевірка строкового представлення"""
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)

        expected = f"Conversation: {self.user1.nickname} & {self.user2.nickname}"
        self.assertEqual(str(conversation), expected)

    def test_get_or_create_conversation_new(self):
        """Перевірка створення нової розмови"""
        conversation = Conversation.get_or_create_conversation(self.user1, self.user2)

        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.participants.count(), 2)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user2, conversation.participants.all())

    def test_get_or_create_conversation_existing(self):
        """Перевірка отримання існуючої розмови"""
        conversation1 = Conversation.get_or_create_conversation(self.user1, self.user2)
        conversation2 = Conversation.get_or_create_conversation(self.user1, self.user2)

        self.assertEqual(conversation1.id, conversation2.id)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_get_or_create_conversation_reversed_order(self):
        """Перевірка, що порядок користувачів не має значення"""
        conversation1 = Conversation.get_or_create_conversation(self.user1, self.user2)
        conversation2 = Conversation.get_or_create_conversation(self.user2, self.user1)

        self.assertEqual(conversation1.id, conversation2.id)

    def test_conversation_ordering(self):
        """Перевірка сортування розмов"""
        conv1 = Conversation.objects.create()
        conv1.participants.add(self.user1, self.user2)

        conv2 = Conversation.objects.create()
        conv2.participants.add(self.user1, self.user3)

        conversations = Conversation.objects.all()
        self.assertEqual(conversations[0], conv2)

    def test_conversation_updated_at(self):
        """Перевірка автоматичного оновлення updated_at"""
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)

        old_time = conversation.updated_at
        conversation.save()

        self.assertGreaterEqual(conversation.updated_at, old_time)

    def test_multiple_participants(self):
        """Перевірка розмови з кількома учасниками"""
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2, self.user3)

        self.assertEqual(conversation.participants.count(), 3)


class MessageModelTest(TestCase):
    """Тести для моделі Message"""

    def setUp(self):
        """Налаштування тестового середовища"""
        if not hasattr(settings, "CHAT_ENCRYPTION_KEY"):
            settings.CHAT_ENCRYPTION_KEY = Fernet.generate_key().decode()

        self.user1 = CustomUser.objects.create_user(
            email="msg1@test.com", password="pass123", nickname="msguser1"
        )
        self.user2 = CustomUser.objects.create_user(
            email="msg2@test.com", password="pass123", nickname="msguser2"
        )
        self.conversation = Conversation.get_or_create_conversation(
            self.user1, self.user2
        )

    def test_message_creation(self):
        """Перевірка створення повідомлення"""
        message = Message.objects.create(
            user=self.user1, conversation=self.conversation, content="Hello, World!"
        )
        self.assertEqual(message.user, self.user1)
        self.assertEqual(message.conversation, self.conversation)
        self.assertFalse(message.is_edited)
        self.assertFalse(message.is_read)

    def test_message_encryption(self):
        """Перевірка шифрування повідомлення"""
        plain_text = "Secret message"
        message = Message.objects.create(
            user=self.user1, conversation=self.conversation, content=plain_text
        )

        self.assertNotEqual(message.content, plain_text)
        self.assertEqual(message.get_decrypted_content(), plain_text)

    def test_message_decryption(self):
        """Перевірка розшифрування повідомлення"""
        plain_text = "Test decryption"
        message = Message.objects.create(
            user=self.user1, conversation=self.conversation, content=plain_text
        )

        decrypted = message.get_decrypted_content()
        self.assertEqual(decrypted, plain_text)

    def test_message_str_representation(self):
        """Перевірка строкового представлення"""
        message = Message.objects.create(
            user=self.user1,
            conversation=self.conversation,
            content="Long message for testing string representation",
        )
        str_repr = str(message)
        self.assertTrue(str_repr.startswith(f"{self.user1.nickname}:"))

    def test_message_ordering(self):
        """Перевірка сортування повідомлень"""
        msg1 = Message.objects.create(
            user=self.user1, conversation=self.conversation, content="First message"
        )
        msg2 = Message.objects.create(
            user=self.user2, conversation=self.conversation, content="Second message"
        )

        messages = Message.objects.all()
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)

    def test_conversation_updated_on_message(self):
        """Перевірка оновлення часу розмови при новому повідомленні"""
        old_time = self.conversation.updated_at

        Message.objects.create(
            user=self.user1, conversation=self.conversation, content="Update test"
        )

        self.conversation.refresh_from_db()
        self.assertGreater(self.conversation.updated_at, old_time)

    def test_message_without_conversation(self):
        """Перевірка створення повідомлення без розмови"""
        message = Message.objects.create(
            user=self.user1, content="No conversation message"
        )
        self.assertIsNone(message.conversation)

    def test_message_is_edited_default(self):
        """Перевірка значення is_edited за замовчуванням"""
        message = Message.objects.create(
            user=self.user1, conversation=self.conversation, content="Test"
        )
        self.assertFalse(message.is_edited)
        self.assertIsNone(message.edited_at)

    def test_message_is_read_default(self):
        """Перевірка значення is_read за замовчуванням"""
        message = Message.objects.create(
            user=self.user1, conversation=self.conversation, content="Test"
        )
        self.assertFalse(message.is_read)

    def test_multiple_messages_in_conversation(self):
        """Перевірка кількох повідомлень у розмові"""
        for i in range(5):
            Message.objects.create(
                user=self.user1 if i % 2 == 0 else self.user2,
                conversation=self.conversation,
                content=f"Message {i}",
            )

        messages = Message.objects.filter(conversation=self.conversation)
        self.assertEqual(messages.count(), 5)

    def test_encryption_key_generation(self):
        """Перевірка генерації ключа шифрування"""
        cipher = Message.get_cipher()
        self.assertIsNotNone(cipher)

    def test_unicode_content_encryption(self):
        """Перевірка шифрування Unicode контенту"""
        unicode_text = "Привіт, світ! 🌍"

        message = Message.objects.create(
            user=self.user1, conversation=self.conversation, content=unicode_text
        )

        self.assertEqual(message.get_decrypted_content(), unicode_text)


class MessageEncryptionTest(TestCase):
    """Окремі тести для шифрування повідомлень"""

    def setUp(self):
        if not hasattr(settings, "CHAT_ENCRYPTION_KEY"):
            settings.CHAT_ENCRYPTION_KEY = Fernet.generate_key().decode()

        self.user = CustomUser.objects.create_user(
            email="encrypt@test.com", password="pass123", nickname="encryptuser"
        )

    def test_encrypt_and_decrypt_cycle(self):
        """Перевірка повного циклу шифрування/розшифрування"""
        original_text = "This is a secret message!"

        message = Message.objects.create(user=self.user, content=original_text)

        encrypted_content = message.content
        self.assertNotEqual(encrypted_content, original_text)

        decrypted = message.get_decrypted_content()
        self.assertEqual(decrypted, original_text)

    def test_different_messages_different_encryption(self):
        """Перевірка, що різні повідомлення мають різне шифрування"""
        msg1 = Message.objects.create(user=self.user, content="Message 1")
        msg2 = Message.objects.create(user=self.user, content="Message 2")

        self.assertNotEqual(msg1.content, msg2.content)

    def test_long_message_encryption(self):
        """Перевірка шифрування довгого повідомлення"""
        long_text = "A" * 1000

        message = Message.objects.create(user=self.user, content=long_text)

        self.assertEqual(message.get_decrypted_content(), long_text)

    def test_special_characters_encryption(self):
        """Перевірка шифрування спеціальних символів"""
        special_text = "!@#$%^&*()_+-={}[]|\\:\";'<>?,./~`"

        message = Message.objects.create(user=self.user, content=special_text)

        self.assertEqual(message.get_decrypted_content(), special_text)

    def test_multiline_message_encryption(self):
        """Перевірка шифрування багаторядкового повідомлення"""
        multiline_text = "Line 1\nLine 2\nLine 3\nLine 4"

        message = Message.objects.create(user=self.user, content=multiline_text)

        self.assertEqual(message.get_decrypted_content(), multiline_text)


class ConversationManagementTest(TestCase):
    """Тести для управління розмовами"""

    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            email="conv1@test.com", password="pass123", nickname="conv1"
        )
        self.user2 = CustomUser.objects.create_user(
            email="conv2@test.com", password="pass123", nickname="conv2"
        )

    def test_user_can_have_multiple_conversations(self):
        """Перевірка, що користувач може мати кілька розмов"""
        user3 = CustomUser.objects.create_user(
            email="conv3@test.com", password="pass123", nickname="conv3"
        )

        conv1 = Conversation.get_or_create_conversation(self.user1, self.user2)
        conv2 = Conversation.get_or_create_conversation(self.user1, user3)

        user1_conversations = Conversation.objects.filter(participants=self.user1)
        self.assertEqual(user1_conversations.count(), 2)

    def test_delete_user_keeps_conversation(self):
        """Перевірка, що розмова зберігається після видалення користувача"""
        conversation = Conversation.get_or_create_conversation(self.user1, self.user2)
        conv_id = conversation.id

        self.user1.delete()

        # Розмова повинна існувати
        self.assertTrue(Conversation.objects.filter(id=conv_id).exists())

    def test_conversation_with_messages_count(self):
        """Перевірка підрахунку повідомлень у розмові"""
        conversation = Conversation.get_or_create_conversation(self.user1, self.user2)

        for i in range(10):
            Message.objects.create(
                user=self.user1, conversation=conversation, content=f"Message {i}"
            )

        message_count = conversation.messages.count()
        self.assertEqual(message_count, 10)

    def test_get_latest_message_in_conversation(self):
        """Перевірка отримання останнього повідомлення"""
        conversation = Conversation.get_or_create_conversation(self.user1, self.user2)

        Message.objects.create(
            user=self.user1, conversation=conversation, content="First"
        )

        last_msg = Message.objects.create(
            user=self.user2, conversation=conversation, content="Last"
        )

        latest = conversation.messages.last()
        self.assertEqual(latest.id, last_msg.id)
        self.assertEqual(latest.content, last_msg.content)
