# #!/bin/bash
# python manage.py migrate --noinput
# python manage.py collectstatic --noinput
# gunicorn TelegramBot.wsgi:application &
# python telegram_bot.py

#!/usr/bin/env bash
set -o errexit

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Start the web server and bind to Render's provided port
gunicorn TelegramBot.wsgi:application --bind 0.0.0.0:$PORT
