#!/bin/bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn TelegramBot.wsgi:application &
python telegram_bot.py
