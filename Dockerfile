# Imagen base oficial de Python
FROM python:3.11-slim

# Crear y establecer el directorio de trabajo
WORKDIR /app

# Copiar archivos de requisitos y proyecto
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Establecer variables de entorno para Flask
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Exponer el puerto en el contenedor
EXPOSE 8080

# Comando para ejecutar el servidor con Gunicorn (más estable que flask run)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
