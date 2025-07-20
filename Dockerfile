FROM python:3.11-slim

# Instalar solo las dependencias necesarias para ejecutar Chromium con Playwright
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    supervisor \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    libxss1 \
    libpci3 \
    libdrm2 \
    libappindicator3-1 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Crear usuario sin privilegios
RUN useradd -m appuser

# Directorio de trabajo
WORKDIR /app

# Copiar dependencias e instalar Python requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Instalar solo los navegadores, SIN dependencias del sistema (que ya pusimos antes)
USER appuser
RUN playwright install chromium

# Volver a root para copiar archivos y ajustar permisos
USER root
COPY . .
RUN chown -R appuser:appuser /app

# Variables de entorno
ENV DJANGO_SETTINGS_MODULE=bicyclesscraping.settings
ENV PYTHONUNBUFFERED=1

# Recolectar estáticos
RUN python manage.py collectstatic --noinput

# Usuario final
USER appuser

# Puerto de exposición
EXPOSE 8000

# Comando final
CMD ["gunicorn", "bicyclesscraping.wsgi:application", "--bind", "0.0.0.0:8000"]

