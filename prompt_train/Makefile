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

https:
	daphne -e ssl:8000:privateKey=key.pem:certKey=cert.pem prompt_train.asgi:application
	celery -A prompt_train.celery worker -l info
static:
	python manage.py collectstatic

tests:
	python manage.py test --settings=prompt_train.settings_test

shell:
	python manage.py shell

superuser:
	python manage.py createsuperuser

lint:
	ruff check .

format:
	ruff format .

docker-up:
	docker compose -f docker/docker-compose.dev.yml up --build -d

docker-down:
	docker compose -f docker/docker-compose.dev.yml down

docker-logs:
	docker compose -f docker/docker-compose.dev.yml logs -f