pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'prod'],
            description: 'Target deployment environment (dev = port 8080, prod = port 80)'
        )
    }

    environment {
        COMPOSE_FILE = "${params.ENVIRONMENT == 'prod' ? 'docker-compose.prod.yml' : 'docker-compose.dev.yml'}"
        PORT = "${params.ENVIRONMENT == 'prod' ? '80' : '8080'}"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "=== Stage 1: Checking out source code from Git ==="
                checkout scm
            }
        }

        stage('Test') {
            steps {
                echo "=== Stage 2: Running unit tests against isolated PostgreSQL test database ==="
                sh '''
                    # Start temporary isolated PostgreSQL database container
                    docker run -d --name jenkins_test_db_${BUILD_NUMBER} \
                        -e POSTGRES_DB=test_db \
                        -e POSTGRES_USER=test_user \
                        -e POSTGRES_PASSWORD=test_pass \
                        postgres:16-alpine

                    # Wait until the test database is ready to accept connections
                    for i in $(seq 1 15); do
                        if docker exec jenkins_test_db_${BUILD_NUMBER} pg_isready -U test_user -d test_db; then
                            break
                        fi
                        sleep 1
                    done

                    # Execute Django test suite in container attached to test db and sharing workspace
                    docker run --rm --network container:jenkins_test_db_${BUILD_NUMBER} \
                        --volumes-from jenkins_server \
                        -w "${WORKSPACE}" \
                        -e DB_ENGINE=django.db.backends.postgresql \
                        -e DB_NAME=test_db \
                        -e DB_USER=test_user \
                        -e DB_PASSWORD=test_pass \
                        -e DB_HOST=127.0.0.1 \
                        -e DB_PORT=5432 \
                        python:3.12-slim \
                        bash -c "pip install -q -r requirements.txt && python manage.py test"
                '''
            }
            post {
                always {
                    sh "docker rm -f jenkins_test_db_${BUILD_NUMBER} || true"
                }
            }
        }

        stage('Build') {
            steps {
                echo "=== Stage 3: Building Django and Nginx Docker images ==="
                sh '''
                    docker build -t inventory-web:latest -t inventory-web:${BUILD_NUMBER} .
                    docker build -t inventory-nginx:latest -t inventory-nginx:${BUILD_NUMBER} ./nginx
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo "=== Stage 4: Deploying services (${COMPOSE_FILE}) ==="
                sh '''
                    docker compose -f ${COMPOSE_FILE} up -d --build
                '''
            }
        }

        stage('Post-deploy') {
            steps {
                echo "=== Stage 5: Running migrations and verifying health check ==="
                sh '''
                    # 1. Run migrations inside web container
                    docker compose -f ${COMPOSE_FILE} exec -T web python manage.py migrate --noinput

                    # 2. Collect static files
                    docker compose -f ${COMPOSE_FILE} exec -T web python manage.py collectstatic --noinput

                    # 3. Automated health check verification
                    MAX_ATTEMPTS=15
                    SLEEP_SECONDS=2
                    HEALTH_URL="http://localhost:${PORT}/health/"

                    echo "Checking health check on ${HEALTH_URL}..."
                    SUCCESS=0
                    for i in $(seq 1 $MAX_ATTEMPTS); do
                        echo "  [Attempt $i of $MAX_ATTEMPTS] Querying /health/..."
                        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || true)
                        if [ "$HTTP_CODE" = "200" ]; then
                            echo "SUCCESS: Application returned HTTP 200 on ${HEALTH_URL}!"
                            SUCCESS=1
                            break
                        fi

                        CONTAINER_CODE=$(docker compose -f ${COMPOSE_FILE} exec -T web curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health/ || true)
                        if [ "$CONTAINER_CODE" = "200" ]; then
                            echo "SUCCESS: Application returned HTTP 200 inside web container!"
                            SUCCESS=1
                            break
                        fi

                        sleep $SLEEP_SECONDS
                    done

                    if [ "$SUCCESS" -ne 1 ]; then
                        echo "ERROR: Health check timed out without HTTP 200. Halting deployment."
                        exit 1
                    fi
                '''
            }
        }
    }
}
