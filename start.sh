#!/bin/bash
# python manage.py migrate --noinput
# python manage.py collectstatic --noinput
# gunicorn TelegramBot.wsgi:application &
# python telegram_bot.py

#!/usr/bin/env bash
set -o errexit

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Start Django app on Render's required port
gunicorn TelegramBot.wsgi:application --bind 0.0.0.0:$PORT
