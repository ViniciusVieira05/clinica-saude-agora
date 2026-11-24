#!/usr/bin/env bash
# Publica a versão nova: baixa do GitHub, instala, migra, coleta estáticos e reinicia.
# Uso (na VPS):  sudo -u saudeagora bash /srv/saude_agora/deploy/atualizar.sh
set -euo pipefail
cd /srv/saude_agora
git pull
.venv/bin/pip install -r requirements/prod.txt --quiet
export DJANGO_SETTINGS_MODULE=config.settings.prod
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py check --deploy
echo "Pronto. Agora rode: sudo systemctl restart saude_agora"
