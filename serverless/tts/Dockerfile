
FROM nvidia/cuda:12.9.0-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


# ============================================================
# SYSTEM DEPENDENCIES
# ============================================================

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3.12-dev \
    git \
    ca-certificates \
    ffmpeg \
    libsox-dev \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# PYTORCH
# ============================================================

RUN python3 -m pip install --no-cache-dir --break-system-packages \
    torch==2.8.0 \
    torchaudio==2.8.0 \
    --index-url https://download.pytorch.org/whl/cu129

# ============================================================
# FISH SPEECH DEPENDENCIES
# ============================================================

RUN python3 -m pip install --no-cache-dir --break-system-packages \
    hydra-core \
    numpy \
    pyrootutils \
    soundfile \
    loguru \
    natsort \
    lightning \
    rich \
    descript-audiotools \
    descript-audio-codec \
    "transformers<=4.57.3" \
    loralib \
    click \
    runpod \
    huggingface_hub


# ============================================================
# WORKSPACE
# ============================================================

WORKDIR /app

# ============================================================
# SERVERLESS HANDLER
# ============================================================

# adapt path here
COPY Dockerfile_seb_test_s2/handler.py /app/handler.py

# ============================================================
# START SERVERLESS WORKER
# ============================================================

CMD ["python3", "/app/handler.py"]