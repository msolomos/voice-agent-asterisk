FROM python:3.11-slim

# Εγκατάσταση system dependencies για PyAudio
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    portaudio19-dev \
    alsa-utils \
    libasound2-dev \
    pulseaudio \
    ffmpeg \
    sox \
    libsox-fmt-all \
    python3-dev \
    python3-pip \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Δημιουργία working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Εγκατάσταση Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "voice_agent.py"]