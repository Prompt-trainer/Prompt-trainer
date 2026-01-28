run:
	python manage.py runserver &
	celery -A prompt_train.celery worker -l info

stop:
	pkill -f runserver
	pkill -f celery

mm:
	python manage.py makemigrations

m:
	python manage.py migrate

