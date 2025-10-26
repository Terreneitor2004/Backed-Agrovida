# Imagen base oficial de Python
FROM python:3.11-slim

WORKDIR /app

# Copiar requisitos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Variables para Flask
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

# Gunicorn ejecutará el servicio Flask
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
