FROM python:3.10-slim-bullseye

# تثبيت المتطلبات النظامية
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    git \
    && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxcomposite1 \
    libx11-xcb1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libgbm1 \
    libasound2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ الملفات
COPY requirements.txt .
COPY . .

# تثبيت متطلبات البايثون
RUN pip install --no-cache-dir -r requirements.txt

# تثبيت playwright والمتصفحات
RUN playwright install chromium
RUN playwright install --with-deps chromium

CMD ["python3", "main.py"]
