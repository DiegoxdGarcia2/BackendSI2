# Usa una imagen base ligera de Python
FROM python:3.10.13-slim
# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia primero el archivo de dependencias para aprovechar el cache de Docker
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt
# Instala gunicorn para producción
RUN pip install gunicorn

# Copia el resto de los archivos de la aplicación al contenedor
COPY . .

# Expone el puerto 8000 para la aplicación FastAPI
EXPOSE 8000

# Ejecuta migraciones y luego arranca gunicorn
CMD ["/bin/sh", "-c", "python manage.py migrate && gunicorn cole.wsgi:application --bind 0.0.0.0:8000"]
