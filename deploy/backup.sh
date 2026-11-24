#!/usr/bin/env bash
# Backup diário do banco e das fotos da clínica (guarda 30 dias).
# Agendar no cron:  0 3 * * * bash /srv/saude_agora/deploy/backup.sh >> /var/log/saude_agora_backup.log 2>&1
set -euo pipefail
cd /srv/saude_agora
source <(grep -E '^(DB_NAME|DB_USER)=' .env)

DESTINO=/var/backups/saude_agora
DATA=$(date +%Y-%m-%d_%H%M)
mkdir -p "$DESTINO"

docker compose exec -T db pg_dump -U "$DB_USER" --format=custom "$DB_NAME" > "$DESTINO/banco_$DATA.dump"
tar -czf "$DESTINO/media_$DATA.tar.gz" media

find "$DESTINO" -type f -mtime +30 -delete
echo "Backup concluído: $DATA"
