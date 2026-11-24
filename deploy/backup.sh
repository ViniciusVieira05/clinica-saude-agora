#!/usr/bin/env bash
# Backup diário do banco e das fotos da clínica. Agendado no cron (ver deploy/LEIA-ME.md).
set -euo pipefail

DESTINO=/var/backups/saude_agora
DATA=$(date +%Y-%m-%d_%H%M)
mkdir -p "$DESTINO"

sudo -u postgres pg_dump --format=custom saude_agora > "$DESTINO/banco_$DATA.dump"
tar -czf "$DESTINO/media_$DATA.tar.gz" -C /srv/saude_agora media

# Guarda só os últimos 30 dias
find "$DESTINO" -type f -mtime +30 -delete
echo "Backup concluído: $DATA"
