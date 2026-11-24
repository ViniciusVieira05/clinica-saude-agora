#!/usr/bin/env bash
# Publica a versão nova do sistema da clínica.
# Uso (na VPS):  bash /srv/saude_agora/deploy/atualizar.sh
set -euo pipefail
cd /srv/saude_agora
git pull
docker compose up -d --build
docker compose exec -T web python manage.py check --deploy
echo "Sistema atualizado."
