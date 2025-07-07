# Imagen base
FROM python:3.11-slim

# Instalar dependencias del sistema para Playwright/Chromium
RUN apt-get update && apt-get install -y \
    curl \
    libgbm1 \
    libasound2 \
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
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    libxss1 \
    libpci3 \
    libdrm2 \
    fonts-liberation \
    libappindicator3-1 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Crear directorio de la app
WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar navegadores de Playwright
RUN playwright install chromium

# Copiar el resto del código
COPY . .

# Definir variables de entorno necesarias para producción
ENV DJANGO_SETTINGS_MODULE=bicyclesscraping.settings
ENV PYTHONUNBUFFERED=1

# Ejecutar collectstatic en build time
RUN python manage.py collectstatic --noinput

# Exponer el puerto para Django
EXPOSE 8000

# Comando para correr el servidor de Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
