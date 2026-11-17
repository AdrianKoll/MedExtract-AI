#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear
test -s /app/staticfiles/extractor/app.css

exec "$@"
