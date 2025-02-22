FROM python:3.11.9-slim

WORKDIR /app
RUN apt-get update && apt-get upgrade -y && apt-get install build-essential -y && apt-get install libreoffice && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --upgrade pip

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
