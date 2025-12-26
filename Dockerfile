FROM mcr.microsoft.com/playwright/python:latest

# Directorio de trabajo
WORKDIR /app

# Copiar dependencias e instalar Python requirements
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \ 
    pip install --no-cache-dir -r requirements.txt

# Volver a root para copiar archivos y ajustar permisos
USER root
COPY . .
RUN chown -R pwuser:pwuser /app

# Variables de entorno
ENV DJANGO_SETTINGS_MODULE=bicyclesscraping.settings
ENV PYTHONUNBUFFERED=1

# Recolectar estáticos
RUN python manage.py collectstatic --noinput

# Usuario final
USER pwuser

# Puerto de exposición
EXPOSE 8000

# Comando final
CMD ["gunicorn", "bicyclesscraping.wsgi:application", "--bind", "0.0.0.0:8000"]

