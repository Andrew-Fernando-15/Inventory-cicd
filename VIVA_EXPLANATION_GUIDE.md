# DevOps Final Practical Exam - Viva and Oral Defense Guide

This guide contains plain-language explanations of every file, technology, and pipeline stage in this project, along with answers to expected examiner questions.

---

## 1. Quick Project Elevator Pitch (Say this when asked "Tell me about your project")

> "This project is a containerized Django Inventory and Billing web application with an automated end-to-end CI/CD pipeline managed by Jenkins.
> The application uses a multi-tier microservices architecture: an Nginx reverse proxy that handles incoming traffic and serves static files, a Gunicorn WSGI server running Django application logic, and a PostgreSQL database with persistent volume storage.
> Whenever a developer commits code to GitHub, Jenkins automatically detects the change, runs automated unit tests in an isolated container, builds new Docker images, deploys the stack using Docker Compose, runs database migrations, and verifies system health through a retry check on the `/health/` endpoint. If any test or health check fails, the pipeline stops immediately to prevent deploying defective code."

---

## 2. Explanation of Every Core File in the Project

### Application and Web Server Files
- `inventory_project/settings.py`:
  - Contains Django configuration. It dynamically checks environment variables (`DEBUG`, `SECRET_KEY`, `POSTGRES_DB`, etc.). If environment variables are absent (such as running quick tests on a local host without Docker), it safely defaults to SQLite so developer tests never crash.
- `inventory/models.py`:
  - Defines the database schema: `Product` (stock quantities, pricing, SKU), `Invoice` (customer details, timestamps, total amount, and the newly added `notes` field), and `InvoiceItem` (line items linking products to invoices with automatic stock deduction).
- `inventory/views.py`:
  - Contains view controllers for managing products, generating invoices, displaying invoice summaries, and the `/health/` endpoint which performs a real SQL query (`connection.cursor().execute("SELECT 1")`) to verify database responsiveness.
- `Dockerfile`:
  - Builds the Django application container using `python:3.12-slim` for a minimal attack surface and reduced image size. It installs dependencies from `requirements.txt` and starts Gunicorn as the WSGI server on port 8000.
- `nginx/default.conf` & `nginx/Dockerfile`:
  - Configures Nginx as the reverse proxy. Nginx listens on port 80, directly serves static assets from `/static/` (avoiding Python overhead), and forwards all dynamic requests (`/`, `/products/`, `/invoices/`, `/health/`) to `web:8000`.

### Orchestration and Environment Files
- `docker-compose.dev.yml`:
  - Development configuration. Exposes Nginx on host port 8080, runs with `DEBUG=True`, and uses the named volume `inventory_postgres_dev_data` to keep development data separate.
- `docker-compose.prod.yml`:
  - Production configuration. Exposes Nginx on host port 80 (standard HTTP), runs with `DEBUG=False`, sets `restart: always` for container resilience, and uses the named volume `inventory_postgres_prod_data`.
- `.env.dev` & `.env.prod`:
  - Key-value configuration files separating development credentials from production credentials. Kept out of version control in production setups.
- `deploy.sh` & `deploy.ps1`:
  - Standalone deployment helper scripts that run `docker compose up -d`, execute `migrate` and `collectstatic` inside the container, and loop up to 15 times querying the `/health/` endpoint.

### CI/CD and Automation Files
- `jenkins-runner/Dockerfile`:
  - Extends the official `jenkins/jenkins:lts` image by installing Docker CLI, the Docker Compose plugin, and pre-installing essential Jenkins plugins (`git`, `workflow-aggregator`, `pipeline-stage-view`).
- `jenkins-runner/security.groovy`:
  - An initialization script that automatically creates the Jenkins administrator user (`admin` / `admin123`) and disables the initial setup wizard on container startup.
- `docker-compose.jenkins.yml`:
  - Runs the Jenkins container on host port 8085. Crucially, it mounts `/var/run/docker.sock` from the host, giving Jenkins access to control the host Docker daemon.
- `Jenkinsfile`:
  - Declarative pipeline script with 5 distinct stages (`Checkout`, `Test`, `Build`, `Deploy`, `Post-deploy`) and a build parameter `ENVIRONMENT` (`dev` or `prod`).

---

## 3. Explanation of Each Pipeline Stage

```text
+-------------------+--------------------------------------------------------------------------------+
| Stage Name        | Exact Action & Purpose                                                         |
+-------------------+--------------------------------------------------------------------------------+
| 1. Checkout       | Clones the repository at the latest commit from GitHub into the Jenkins        |
|                   | workspace.                                                                     |
+-------------------+--------------------------------------------------------------------------------+
| 2. Test           | Launches an isolated Python container to run "python manage.py test".          |
|                   | Tests Django models, business logic (stock deduction), and health endpoints.   |
|                   | If any test fails, Jenkins marks the stage FAILED and exits immediately.       |
|                   | No deployment or Docker build is executed.                                     |
+-------------------+--------------------------------------------------------------------------------+
| 3. Build          | Builds the Docker images for Django (inventory-ci-cd-web) and Nginx           |
|                   | (inventory-ci-cd-nginx) using "docker compose build".                          |
+-------------------+--------------------------------------------------------------------------------+
| 4. Deploy         | Runs "docker compose -f <compose_file> up -d" using the selected parameter    |
|                   | (docker-compose.dev.yml or docker-compose.prod.yml). Recreates containers with  |
|                   | the newly built images.                                                        |
+-------------------+--------------------------------------------------------------------------------+
| 5. Post-deploy    | Executes "python manage.py migrate --noinput" inside the web container to      |
|                   | apply schema migrations. Then runs a retry loop checking the "/health/"       |
|                   | endpoint up to 15 times until HTTP 200 is confirmed.                          |
+-------------------+--------------------------------------------------------------------------------+
```

---

## 4. Top Examiner Questions and Model Answers

### Q1: Why do you need Nginx? Why not expose Gunicorn directly to the user?
**Answer:**
"Gunicorn is a WSGI application server designed to execute Python code, not handle raw internet traffic. Nginx serves two critical purposes:
1. Performance: Nginx serves static files (CSS, JS, images) directly from disk via a shared volume without consuming Python/Gunicorn worker processes.
2. Security and Buffering: Nginx buffers slow clients, protects against slowloris attacks, terminates SSL/TLS, and acts as a reverse proxy, insulating application workers."

### Q2: How does Jenkins talk to Docker when Jenkins itself is running inside a Docker container?
**Answer:**
"We use Docker-outside-of-Docker (DooD) via a volume mount: `-v /var/run/docker.sock:/var/run/docker.sock`.
The Jenkins container has the Docker client CLI installed, but instead of running a nested Docker daemon inside the container, it communicates through the Unix socket directly with the host machine's Docker daemon. Containers spawned by Jenkins run side-by-side on the host Docker engine."

### Q3: Why did you use SCM Polling instead of GitHub Webhooks?
**Answer:**
"GitHub Webhooks require GitHub servers to make an inbound HTTP POST request to Jenkins. Because our Jenkins instance is running on a private local network behind NAT and firewalls, GitHub cannot reach `http://localhost:8085` directly without a public tunnel (like ngrok or Cloudflare Tunnel).
SCM Polling (`* * * * *`) initiates an outbound check from Jenkins to GitHub every minute, which works reliably across private networks without exposing internal ports."

### Q4: How do you prevent deploying broken code?
**Answer:**
"The `Test` stage runs before the `Build` and `Deploy` stages. In our pipeline, we demonstrated this by introducing a deliberate assertion failure in `inventory/tests.py`. The test step failed, Jenkins aborted the pipeline with exit code 1, and the `Build`, `Deploy`, and `Post-deploy` stages were completely skipped. The running application was untouched."

### Q5: What happened during your Live Model Demo?
**Answer:**
"We added a new `notes` field to the `Invoice` model in `inventory/models.py`, generated the migration `0002_invoice_notes.py`, updated the HTML forms, and committed the changes to Git.
Jenkins detected the commit automatically, validated all tests, built new container images, deployed the updated container, applied the database migration automatically via `manage.py migrate` in the `Post-deploy` stage, and verified health. The field was immediately visible and functional on the live web app with zero manual intervention."

### Q6: What does the `/health/` endpoint verify?
**Answer:**
"It doesn't just return a static string. It actively tests two things:
1. Web server responsiveness: Confirms Django and Gunicorn are accepting requests.
2. Database connectivity: Executes `SELECT 1` on the PostgreSQL database connection. If the database is down or unreachable, it catches the exception and returns an HTTP 503 error, causing the pipeline post-deploy health check to fail."

---

## 5. Summary Checklist of Demonstration Steps for the Examiner

1. Show the running containers:
   - Run `docker ps` to display `jenkins_server`, `inventory_dev_nginx`, `inventory_dev_web`, and `inventory_dev_db`.
2. Open Jenkins in the browser:
   - Navigate to `http://localhost:8085/`.
   - Log in with `admin` / `admin123`.
   - Open the `Inventory-CI-CD` job and show the Pipeline Stage View with all 5 stages green.
3. Show the Live Application:
   - Open `http://localhost:8080/products/` and show the summary cards, stock badges, and product management.
   - Open `http://localhost:8080/invoices/create/` and show the `notes` textarea field added during the live demo.
4. Show Health Check Output:
   - Open `http://localhost:8080/health/` and show the JSON response:
     `{"status": "healthy", "database": "connected", "service": "inventory_and_billing"}`.
5. Show Test Suite:
   - Run `docker exec inventory_dev_web python manage.py test` to show 9 passing tests.
