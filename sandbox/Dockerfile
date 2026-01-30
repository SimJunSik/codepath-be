# Minimal Python sandbox image for secure code execution
FROM python:3.12-slim-bookworm

# Security: Create non-root user
RUN groupadd -r sandbox && useradd -r -g sandbox -d /home/sandbox -s /sbin/nologin sandbox

# Security: Remove potentially dangerous packages
RUN apt-get update && apt-get purge -y --auto-remove \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create workspace with restricted permissions
WORKDIR /workspace
RUN chown sandbox:sandbox /workspace

# Security: Remove write permissions from system directories
RUN chmod -R 555 /usr /bin /sbin 2>/dev/null || true

# Switch to non-root user
USER sandbox

# Set Python to unbuffered mode for immediate output
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Disable importing from user site packages
ENV PYTHONNOUSERSITE=1

# Entry point - execute Python code passed as argument
ENTRYPOINT ["python", "-c"]
