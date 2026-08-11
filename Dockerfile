FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    gcc \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN grep -v "^python-magic-bin" requirements.txt > requirements.docker.txt \
    && pip install --no-cache-dir -r requirements.docker.txt --extra-index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir python-magic
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]