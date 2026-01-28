run:
	python manage.py runserver &
	celery -A prompt_train.celery worker -l info

stop:
	pkill -f runserver
	pkill -f celery
