# Imagen base
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para Chrome headless
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg2 fonts-liberation libappindicator3-1 \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 \
    libgdk-pixbuf2.0-0 libnspr4 libnss3 libx11-xcb1 libxcomposite1 \
    libxdamage1 libxrandr2 xdg-utils libu2f-udev libvulkan1 libxss1 \
    libpci3 libdrm2 --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome estable
RUN curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb && \
    apt install ./chrome.deb -y && \
    rm chrome.deb

# Instalar ChromeDriver (versión 138)
RUN wget https://storage.googleapis.com/chrome-for-testing-public/138.0.7204.92/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm -rf chromedriver-linux64*

# Variables de entorno para Selenium
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Crear directorio de la app
WORKDIR /app

# Copiar requerimientos y código
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponer el puerto
EXPOSE 8000

# Comando de inicio
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
