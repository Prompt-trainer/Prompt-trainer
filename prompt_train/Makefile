run:
	python manage.py runserver &
	celery -A prompt_train.celery worker -l info

stop:
	pkill -f runserver
	pkill -f celery

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate
