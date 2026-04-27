FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
EXPOSE 5003
CMD ["gunicorn", "-w", "4", "--threads", "4", "-b", "0.0.0.0:5003", "src.backend.app:app"]
