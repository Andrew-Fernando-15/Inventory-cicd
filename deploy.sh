#!/usr/bin/env bash
# Automated deployment script for StockFlow CI/CD pipeline
# Usage: ./deploy.sh [dev|prod]

set -euo pipefail

ENVIRONMENT="${1:-dev}"

echo "====================================================="
echo " Starting Deployment: Environment = ${ENVIRONMENT}"
echo "====================================================="

if [ "$ENVIRONMENT" = "prod" ] || [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    PORT=80
else
    COMPOSE_FILE="docker-compose.dev.yml"
    PORT=8080
fi

echo "[1/4] Starting services with ${COMPOSE_FILE}..."
docker compose -f "$COMPOSE_FILE" up -d --build

echo "[2/4] Running database migrations inside web container..."
docker compose -f "$COMPOSE_FILE" exec -T web python manage.py migrate --noinput

echo "[3/4] Collecting static files inside web container..."
docker compose -f "$COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput

echo "[4/4] Verifying health check on /health/..."
MAX_ATTEMPTS=15
SLEEP_SECONDS=2
HEALTH_URL="http://localhost:${PORT}/health/"

for i in $(seq 1 $MAX_ATTEMPTS); do
    echo "  Checking ${HEALTH_URL} (Attempt $i of $MAX_ATTEMPTS)..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || true)

    if [ "$HTTP_CODE" = "200" ]; then
        echo "====================================================="
        echo " Deployment SUCCESS: Application is healthy (HTTP 200)!"
        echo "====================================================="
        exit 0
    fi

    CONTAINER_CODE=$(docker compose -f "$COMPOSE_FILE" exec -T web curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health/ || true)
    if [ "$CONTAINER_CODE" = "200" ]; then
        echo "====================================================="
        echo " Deployment SUCCESS: Application is healthy (HTTP 200 via container internal)!"
        echo "====================================================="
        exit 0
    fi

    sleep $SLEEP_SECONDS
done

echo "====================================================="
echo " Deployment FAILED: Health check timed out without HTTP 200."
echo "====================================================="
exit 1
