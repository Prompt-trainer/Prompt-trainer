# Prompt Trainer

Гейміфікована платформа для навчання написанню AI-промптів через ігри та челенджі.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-darkgreen?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-red?logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5-37814A?logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?logo=nginx&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS_S3-storage-FF9900?logo=amazons3&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Про проєкт

**Prompt Trainer** — це вебзастосунок, що перетворює вивчення prompt engineering на захопливу гру.

Що вміє платформа:
- **Навчання через ігри** — проходи челенджі, покращуй свої промпти, отримуй оцінку від AI
- **Система рангів** — Bronze → Silver → Gold → Ruby → Diamond на основі накопиченого досвіду (XP)
- **Real-time чат** — зашифроване спілкування між користувачами через WebSocket
- **Магазин косметики** — кільця, елементи та тайтли для персоналізації профілю
- **Таблиця лідерів** — змагайся з іншими гравцями
- **OAuth через GitHub і Google** — швидкий вхід без реєстрації

---

## Технології

| Технологія | Призначення |
|---|---|
| Python 3.13 / Django 6 | Основний веб-фреймворк |
| Django Channels + Daphne | WebSocket підтримка (real-time чат) |
| Celery + Redis | Асинхронні задачі (email розсилка) |
| PostgreSQL | База даних |
| Nginx | Reverse proxy, роздача статики, SSL |
| Docker / Docker Compose | Контейнеризація |
| AWS S3 | Зберігання медіафайлів |
| Perplexity API | AI оцінювання промптів |
| django-allauth | OAuth аутентифікація (GitHub) |
| Cryptography (Fernet) | Шифрування повідомлень чату |

---

## Встановлення

### Варіант A: Docker (рекомендовано)

**Вимоги:** Docker, Docker Compose

```bash
# 1. Клонуй репозиторій
git clone https://github.com/Prompt-trainer/Prompt-trainer.git
cd Prompt-trainer

# 2. Перейди до кореня Django проєкту
cd prompt_train

# 3. Скопіюй .env_example та заповни змінні
cp .env_example .env

# 4. Запусти контейнери
docker compose -f docker/docker-compose.dev.yml up --build -d

# 5. Застосуй міграції
docker compose -f docker/docker-compose.dev.yml exec web uv run python manage.py migrate

# 6. Створи суперкористувача (адмін)
docker compose -f docker/docker-compose.dev.yml exec web uv run python manage.py createsuperuser
```

Відкрий [http://localhost:8000](http://localhost:8000)

---

### Варіант B: Локально (без Docker)

**Вимоги:** Python 3.13+, PostgreSQL, Redis

```bash
# 1. Клонуй репозиторій
git clone https://github.com/Prompt-trainer/Prompt-trainer.git
cd Prompt-trainer/prompt_train

# 2. Встанови uv (менеджер пакетів)
pip install uv

# 3. Встанови залежності
uv sync

# 4. Скопіюй .env_example та заповни змінні
# Встанови PG_HOST=localhost, REDIS_HOST=localhost
cp .env_example .env

# 5. Застосуй міграції
python manage.py migrate

# 6. Створи суперкористувача
python manage.py createsuperuser
```

Запусти два термінали:

```bash
# Термінал 1 — Django сервер
make run
# або: python manage.py runserver

# Термінал 2 — Celery воркер
celery -A prompt_train.celery worker -l info
```

Відкрий [http://localhost:8000](http://localhost:8000)

---

## Структура проєкту

```
Prompt-trainer/
├── prompt_train/
│   ├── chat/                    # Real-time WebSocket чат
│   ├── prompt_gamified/         # Ігровий модуль та AI інтеграція
│   ├── users/                   # Користувачі, профілі, косметика
│   ├── prompt_train/            # Налаштування Django проєкту
│   ├── docker/                  # Docker конфігурація
│   │   ├── Dockerfile.dev
│   │   ├── Dockerfile.prod
│   │   ├── docker-compose.dev.yml
│   │   └── docker-compose.prod.yml
│   ├── nginx/                   # Nginx конфігурація
│   │   ├── nginx.conf
│   │   └── certs/               # SSL сертифікати
│   ├── static/                  # Статичні файли (розробка)
│   ├── staticfiles/             # Зібрані статичні файли (production)
│   ├── templates/               # Django шаблони
│   ├── manage.py
│   └── Makefile
├── pyproject.toml               # Python залежності
└── README.md
```

---

## Корисні команди

Команди доступні з директорії `prompt_train/` через `Makefile`:

**Сервер**

| Команда | Дія |
|---|---|
| `make run` | Запустити сервер + Celery |
| `make stop` | Зупинити сервер + Celery |
| `make migrate` | Застосувати міграції |
| `make makemigrations` | Створити нові міграції |
| `make tests` | Запустити тести |
| `make static` | Зібрати статичні файли |
| `make shell` | Відкрити Django shell |
| `make superuser` | Створити суперкористувача |

**Якість коду**

| Команда | Дія |
|---|---|
| `make lint` | Перевірити код (ruff check) |
| `make format` | Форматувати код (ruff format) |

**Docker**

| Команда | Дія |
|---|---|
| `make docker-up` | Запустити контейнери (dev) |
| `make docker-down` | Зупинити контейнери |
| `make docker-logs` | Переглянути логи контейнерів |

---

## Ліцензія

Цей проєкт поширюється під ліцензією [MIT](https://opensource.org/licenses/MIT).
