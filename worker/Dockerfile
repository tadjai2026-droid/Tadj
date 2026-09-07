FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 HF_HOME=/models
RUN apt-get update && apt-get install -y python3 python3-pip git ffmpeg libgl1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY main.py .
EXPOSE 9000
CMD ["python3","-m","uvicorn","main:app","--host","0.0.0.0","--port","9000"]
