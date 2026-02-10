from django.test import TestCase
from django.core.exceptions import ValidationError
from users.models import CustomUser, CustomUserManager


class CustomUserManagerTest(TestCase):
    """Тести для CustomUserManager"""

    def test_create_user(self):
        """Перевірка створення звичайного користувача"""
        user = CustomUser.objects.create_user(
            email="test@example.com", password="testpass123", nickname="testuser"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.nickname, "testuser")
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Перевірка створення суперкористувача"""
        admin = CustomUser.objects.create_superuser(
            email="admin@example.com", password="adminpass123", nickname="admin"
        )
        self.assertEqual(admin.email, "admin@example.com")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_superuser)

    def test_normalize_email(self):
        """Перевірка нормалізації email"""
        user = CustomUser.objects.create_user(
            email="Test@EXAMPLE.COM", password="testpass123", nickname="testuser"
        )
        self.assertEqual(user.email, "Test@example.com")


class CustomUserModelTest(TestCase):
    """Тести для моделі CustomUser"""

    def setUp(self):
        """Створення тестового користувача перед кожним тестом"""
        self.user = CustomUser.objects.create_user(
            email="user@example.com", password="password123", nickname="testuser"
        )

    def test_user_creation_defaults(self):
        """Перевірка значень за замовчуванням"""
        self.assertEqual(self.user.rank, "B")
        self.assertEqual(self.user.points, 0)
        self.assertEqual(self.user.exp, 0)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_active)

    def test_unique_email(self):
        """Перевірка унікальності email"""
        with self.assertRaises(Exception):
            CustomUser.objects.create_user(
                email="user@example.com", password="pass123", nickname="anotheruser"
            )

    def test_unique_nickname(self):
        """Перевірка унікальності nickname"""
        with self.assertRaises(Exception):
            CustomUser.objects.create_user(
                email="another@example.com", password="pass123", nickname="testuser"
            )

    def test_user_str_representation(self):
        """Перевірка строкового представлення"""
        expected = f"{self.user.nickname} - {self.user.email}"
        self.assertEqual(str(self.user), expected)

    def test_rank_upgrade_bronze_to_silver(self):
        """Перевірка підвищення рангу з Bronze до Silver"""
        self.user.exp = 4
        self.user.save()
        self.assertEqual(self.user.rank, "S")

    def test_rank_upgrade_to_gold(self):
        """Перевірка підвищення рангу до Gold"""
        self.user.exp = 8
        self.user.save()
        self.assertEqual(self.user.rank, "G")

    def test_rank_upgrade_to_ruby(self):
        """Перевірка підвищення рангу до Ruby"""
        self.user.exp = 13
        self.user.save()
        self.assertEqual(self.user.rank, "R")

    def test_rank_upgrade_to_diamond(self):
        """Перевірка підвищення рангу до Diamond"""
        self.user.exp = 19
        self.user.save()
        self.assertEqual(self.user.rank, "D")

    def test_rank_stays_bronze(self):
        """Перевірка, що ранг залишається Bronze"""
        self.user.exp = 3
        self.user.save()
        self.assertEqual(self.user.rank, "B")

    def test_rank_boundaries(self):
        """Перевірка граничних значень для рангів"""
        self.user.exp = 3
        self.user.save()
        self.assertEqual(self.user.rank, "B")

        self.user.exp = 4
        self.user.save()
        self.assertEqual(self.user.rank, "S")

    def test_has_perm_for_staff(self):
        """Перевірка прав доступу для staff"""
        self.user.is_staff = True
        self.user.save()
        self.assertTrue(self.user.has_perm("any_permission"))

    def test_has_perm_for_non_staff(self):
        """Перевірка відсутності прав для non-staff"""
        self.assertFalse(self.user.has_perm("any_permission"))

    def test_has_module_perms_for_staff(self):
        """Перевірка прав на модуль для staff"""
        self.user.is_staff = True
        self.user.save()
        self.assertTrue(self.user.has_module_perms("any_app"))

    def test_has_module_perms_for_non_staff(self):
        """Перевірка відсутності прав на модуль для non-staff"""
        self.assertFalse(self.user.has_module_perms("any_app"))

    def test_username_field(self):
        """Перевірка USERNAME_FIELD"""
        self.assertEqual(CustomUser.USERNAME_FIELD, "email")

    def test_email_field(self):
        """Перевірка EMAIL_FIELD"""
        self.assertEqual(CustomUser.EMAIL_FIELD, "email")

    def test_required_fields(self):
        """Перевірка REQUIRED_FIELDS"""
        self.assertIn("nickname", CustomUser.REQUIRED_FIELDS)


class CustomUserRankSystemTest(TestCase):
    """Окремі тести для системи рангів"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="rank@test.com", password="pass123", nickname="rankuser"
        )

    def test_progressive_rank_increase(self):
        """Перевірка поступового підвищення рангу"""
        ranks = [
            (0, "B"),
            (3, "B"),
            (4, "S"),
            (7, "S"),
            (8, "G"),
            (12, "G"),
            (13, "R"),
            (18, "R"),
            (19, "D"),
        ]
        for exp, expected_rank in ranks:
            self.user.exp = exp
            self.user.save()
            self.user.refresh_from_db()
            self.assertEqual(
                self.user.rank,
                expected_rank,
                f"Exp {exp} має давати ранг {expected_rank}, отримано {self.user.rank}",
            )

    def test_rank_persists_after_save(self):
        """Перевірка, що ранг зберігається після збереження"""
        self.user.exp = 10
        self.user.save()
        self.assertEqual(self.user.rank, "G")

        self.user.points = 100
        self.user.save()
        self.assertEqual(self.user.rank, "G")
