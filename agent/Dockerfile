FROM python:3.11-slim

# Environment settings for reliable containerized Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

# Install dependencies first (better build cache)
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY assistant ./assistant
COPY README.md ./
COPY env.example ./

# Use non-root user
USER appuser

# Default port used by the A2A server (matches PORT from env.example)
EXPOSE 10000

# Start the assistant A2A server
CMD ["python", "-m", "assistant.start_a2a"]


