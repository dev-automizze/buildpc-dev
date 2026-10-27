.PHONY: setup backend backend-lan frontend test migrate makemigrations check export import

HOST ?= 127.0.0.1

setup:
	./scripts/setup.sh

backend:
	cd backend && ./venv/bin/python manage.py runserver $(HOST):8088

backend-lan:
	cd backend && ./venv/bin/python manage.py runserver 0.0.0.0:8088

frontend:
	cd frontend && npm run dev

test:
	cd backend && ./venv/bin/python manage.py test --settings=pc_engine.settings_test

migrate:
	cd backend && ./venv/bin/python manage.py migrate

makemigrations:
	cd backend && ./venv/bin/python manage.py makemigrations

check:
	cd backend && ./venv/bin/python manage.py check

export:
	cd backend && ./venv/bin/python manage.py export_components

import:
	cd backend && ./venv/bin/python manage.py import_components exports --all
