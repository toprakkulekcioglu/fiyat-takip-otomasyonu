# Playwright'ın resmi imajı - Chromium'un ihtiyaç duyduğu sistem kütüphaneleri
# zaten kurulu geliyor. Render'ın ücretsiz build ortamı "playwright install
# --with-deps" için gereken root yetkisini vermediği için bu yol seçildi.
FROM mcr.microsoft.com/playwright/python:v1.62.0-noble

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
CMD gunicorn --chdir laptop-arama webhook_app:app --bind 0.0.0.0:$PORT --timeout 120
