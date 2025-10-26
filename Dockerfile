# Usa la imagen oficial de Python
FROM python:3.10-slim

# Establece el puerto que Cloud Run espera
ENV PORT 8080

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requisitos e instala las librerías
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código de tu API (main.py)
COPY . .

# Comando para ejecutar tu servidor de Flask usando Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]