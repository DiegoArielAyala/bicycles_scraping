# Imagen base
FROM python:3.11-slim

# Instalar dependencias del sistema para Chromium y Playwright
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

# Instalar Google Chrome estable
RUN curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb && \
    apt install ./chrome.deb -y && \
    rm chrome.deb

# Variables de entorno para Playwright y Chrome
ENV CHROME_BIN=/usr/bin/google-chrome

# Crear directorio de la app
WORKDIR /app

# Copiar requirements y código
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Instalar navegadores de Playwright
RUN python -m playwright install --with-deps

# Exponer puerto para Django
EXPOSE 8000

# Comando para correr Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]