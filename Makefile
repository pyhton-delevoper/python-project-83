dev:
	poetry run flask --app page_analyzer:app --debug run

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

lint:
	poetry run flake8 page_analyzer

postgres:
	sudo service postgresql restart

db-reset:
	dropdb page_analyzer
	createdb page_analyzer

schema-load:
	psql page_analyzer < database.sql
