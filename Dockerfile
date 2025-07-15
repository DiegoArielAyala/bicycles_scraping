FROM python:3.11-slim

# Instalar dependencias necesarias para navegador
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
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

# Directorio de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Chromium + dependencias internas
RUN playwright install --with-deps

# Copiar código de la app
COPY . .

# Variables de entorno
ENV DJANGO_SETTINGS_MODULE=bicyclesscraping.settings
ENV PYTHONUNBUFFERED=1

RUN python manage.py collectstatic --noinput

# Exponer puerto
EXPOSE 8000

# Comando principal
CMD ["gunicorn", "bicyclesscraping.wsgi:application", "--bind", "0.0.0.0:8000"]

