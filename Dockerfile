# Dockerfile for Render deployment with Java JDK 21
FROM python:3.11-slim

# Install dependencies first
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    apt-transport-https \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Java JDK 21 using Adoptium (with fallback)
RUN mkdir -p /etc/apt/keyrings && \
    (wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor -o /etc/apt/keyrings/adoptium.gpg 2>/dev/null || \
     wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | apt-key add - 2>/dev/null || true) && \
    (echo "deb [signed-by=/etc/apt/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print $2}' /etc/os-release) main" | tee /etc/apt/sources.list.d/adoptium.list > /dev/null || \
     echo "deb https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print $2}' /etc/os-release) main" | tee /etc/apt/sources.list.d/adoptium.list > /dev/null) && \
    apt-get update && \
    (apt-get install -y --no-install-recommends temurin-21-jdk || \
     apt-get install -y --no-install-recommends openjdk-21-jdk) && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME (auto-detect)
RUN JAVA_PATH=$(find /usr/lib/jvm -maxdepth 2 -name "java" -type f 2>/dev/null | head -1) && \
    if [ -n "$JAVA_PATH" ]; then \
      JAVA_HOME_DIR=$(dirname $(dirname $(dirname "$JAVA_PATH"))); \
      echo "JAVA_HOME=$JAVA_HOME_DIR" >> /etc/environment; \
    elif [ -d "/usr/lib/jvm/temurin-21-jdk-amd64" ]; then \
      echo "JAVA_HOME=/usr/lib/jvm/temurin-21-jdk-amd64" >> /etc/environment; \
    elif [ -d "/usr/lib/jvm/java-21-openjdk-amd64" ]; then \
      echo "JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64" >> /etc/environment; \
    fi

ENV JAVA_HOME=/usr/lib/jvm/temurin-21-jdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Verify Java installation
RUN java -version

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
