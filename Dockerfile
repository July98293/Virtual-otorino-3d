FROM python:3.11-slim

# system deps for trimesh/shapely
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run uvicorn to serve FastAPI (backend + frontend)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
