# Imagen base
FROM python:3.11-slim

# Crea el directorio de trabajo
WORKDIR /app

# Copia los archivos
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Puerto que usa Cloud Run
ENV PORT=8080
EXPOSE 8080

CMD ["python", "main.py"]
