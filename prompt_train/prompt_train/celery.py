import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prompt_train.settings')

app = Celery('prompt_train')

app.config_from_object('django.conf:settings', namespace='CELERY')
# Автоматично знаходи tasks з усіх зареєстрованих Django apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
