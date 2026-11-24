#!/bin/sh
# Executado quando o contêiner liga: atualiza o banco, junta os arquivos estáticos e sobe o Gunicorn.
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60 \
    --access-logfile -
