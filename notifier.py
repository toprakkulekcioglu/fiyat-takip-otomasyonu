"""E-posta (SMTP), WhatsApp (CallMeBot) ve Telegram ile fiyat düşüşü bildirimi gönderir.

Tüm hassas bilgiler (şifre, API key) ortam değişkenlerinden okunuyor - kod içine
gömülü değil. Yerelde test için .env dosyası kullanılabiliyor (git'e girmiyor,
.gitignore'da). GitHub Actions'ta bunlar Secrets olarak tanımlanacak (Adım 6).
"""
import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

import requests

from discount_detector import DiscountCheck


def load_dotenv(path: Path = Path(__file__).parent / ".env") -> None:
    """.env dosyasındaki KEY=VALUE satırlarını, zaten ortamda yoksa os.environ'a yükler."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def format_alert_message(product: dict, check: DiscountCheck) -> str:
    return (
        f"SSD Fiyat Düşüşü!\n\n"
        f"Ürün: {product['name']}\n"
        f"Site: {product['site']}\n"
        f"Önceki fiyat (medyan): {check.reference_median:.2f} TL\n"
        f"Yeni fiyat: {check.current_price:.2f} TL\n"
        f"İndirim: %{check.discount_pct * 100:.1f}\n"
        f"Link: {product['url']}"
    )


def send_email_alert(subject: str, body: str) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    sender = os.environ.get("NOTIFY_EMAIL_FROM", user)
    recipient = os.environ["NOTIFY_EMAIL_TO"]

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP(host, port, timeout=15) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(sender, [recipient], msg.as_string())


def send_whatsapp_alert(text: str) -> None:
    phone = os.environ["CALLMEBOT_PHONE"]
    apikey = os.environ["CALLMEBOT_APIKEY"]
    response = requests.get(
        "https://api.callmebot.com/whatsapp.php",
        params={"phone": phone, "text": text, "apikey": apikey},
        timeout=15,
    )
    response.raise_for_status()


def send_telegram_alert(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": text},
        timeout=15,
    )
    response.raise_for_status()


def notify_discount(product: dict, check: DiscountCheck) -> None:
    body = format_alert_message(product, check)
    subject = f"SSD Fiyat Düşüşü: {product['name'][:60]}"
    send_email_alert(subject, body)

    # CallMeBot şu an yeni kayıt kabul etmiyor ("bot dolu") - API key henüz yoksa
    # WhatsApp'ı sessizce atla, e-posta bildirimi yine de gitsin.
    if os.environ.get("CALLMEBOT_PHONE") and os.environ.get("CALLMEBOT_APIKEY"):
        send_whatsapp_alert(body)

    # Telegram, CallMeBot'a göre kapasite sorunu olmayan alternatif - ikisi de
    # ayarlıysa ikisine de gider, biri eksikse sessizce atlanır.
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        send_telegram_alert(body)
