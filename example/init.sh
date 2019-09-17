#!/bin/bash
set -e
cd /docker-entrypoint-initdb.d/
psql --set API_PASSWORD=${API_PASSWORD:-changeme} -f setup.psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB"
