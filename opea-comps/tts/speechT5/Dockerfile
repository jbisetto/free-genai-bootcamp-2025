FROM --platform=linux/arm64 python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Clone the SpeechT5 repository
RUN git clone https://github.com/microsoft/SpeechT5.git /app/SpeechT5

# Install Python dependencies
RUN pip install --no-cache-dir torch torchaudio --extra-index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir transformers soundfile librosa numpy scipy fastapi uvicorn sentencepiece

# Add SpeechT5 to Python path instead of installing it
ENV PYTHONPATH="${PYTHONPATH}:/app/SpeechT5"

# Create service files
COPY service.py /app/

EXPOSE 8000

CMD ["python", "/app/service.py"]