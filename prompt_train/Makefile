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

run_https:
	daphne -e ssl:8000:privateKey=key.pem:certKey=cert.pem   
	celery -A prompt_train.celery worker -l info