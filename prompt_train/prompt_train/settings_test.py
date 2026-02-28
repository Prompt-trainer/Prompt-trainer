from .settings import *

# Вимкнути AWS S3 для тестів
DEFAULT_FILE_STORAGE = 'django.core.files.storage.InMemoryStorage'
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Celery: виконувати задачі синхронно без Redis
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Email: не надсилати реальні листи під час тестів
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
