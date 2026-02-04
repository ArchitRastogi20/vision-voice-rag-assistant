FROM ubuntu:24.04

# Install base dependencies
RUN apt-get update && \
    apt-get install -y \
      python3 python3-venv python3-pip wget ca-certificates libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt /app/requirements.txt

# Set up virtual environment
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

# Install Piper library inside venv
RUN /opt/venv/bin/pip install --no-cache-dir piper-tts

# Copy application code & models
COPY main.py /app/main.py
COPY models /app/models

ENV PATH="/opt/venv/bin:$PATH"

# Expose port for FastAPI
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
