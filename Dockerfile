# APIx Platform - Smart India Hackathon 2026 - Team CodeCrew
FROM python:3.11-slim

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install essential OS packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project codebase and data
COPY apix/ apix/
COPY scripts/ scripts/
COPY data/ data/
COPY tests/ tests/
COPY .streamlit/ .streamlit/

# Ensure entrypoint script is executable
RUN chmod +x scripts/docker-entrypoint.sh

ENTRYPOINT ["/bin/bash", "scripts/docker-entrypoint.sh"]

EXPOSE 8000 8501

CMD ["python", "scripts/start_services.py"]
