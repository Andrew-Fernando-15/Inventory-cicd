FROM jenkins/jenkins:lts-jdk17

USER root

# Install system dependencies for Docker APT repository
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Set up Docker official GPG key and repository
RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker CLI and Docker Compose plugin
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker-ce-cli \
    docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

# Install only the required Jenkins plugins
# 1. git: connect to and clone Git repositories
# 2. workflow-aggregator: core Jenkins pipeline engine
# 3. pipeline-stage-view: visual stage visualization in the UI
RUN jenkins-plugin-cli --plugins \
    git \
    workflow-aggregator \
    pipeline-stage-view

# Pre-configure security and admin account
COPY security.groovy /usr/share/jenkins/ref/init.groovy.d/security.groovy

USER jenkins
