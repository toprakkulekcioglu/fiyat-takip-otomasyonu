"""Telegram'dan bu bota (sen veya arkadaşın) herhangi bir mesaj atıldığında RTX
5070 Ti laptop fiyatlarını arayıp mesajı atana geri gönderen "bot".

Sürekli açık bir sunucu DEĞİL - GitHub Actions sık aralıklarla (örn. her 5 dakikada
bir) bu script'i çalıştırıp Telegram'a "yeni mesaj var mı?" diye soruyor (polling).
Gerçek zamanlı değil ama birkaç dakika içinde cevap gelir - 7/24 açık bir sunucu
kurmadan (ki bu ücretsiz/basit değil) yapılabilecek en pratik yöntem bu.

Güvenlik: sadece LAPTOP_TELEGRAM_ALLOWED_CHAT_IDS listesindeki kişilere cevap
verir - botun linkini/kullanıcı adını bulan başka biri yazarsa sessizce yok
sayılır. Bir Telegram kullanıcısının chat_id'si hangi bota yazdığından bağımsız
sabittir - aynı hesap farklı botlara aynı chat_id ile görünür.
"""
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from notifier import load_dotenv
from search_laptops import search

load_dotenv()

BOT_TOKEN = os.environ["LAPTOP_TELEGRAM_BOT_TOKEN"]
ALLOWED_CHAT_IDS = {
    cid.strip() for cid in os.environ["LAPTOP_TELEGRAM_ALLOWED_CHAT_IDS"].split(",") if cid.strip()
}
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET_FILE = Path(__file__).parent / "last_update_id.txt"


def get_updates() -> list[dict]:
    offset = int(OFFSET_FILE.read_text().strip()) + 1 if OFFSET_FILE.exists() else 0
    response = requests.get(f"{API_BASE}/getUpdates", params={"offset": offset}, timeout=15)
    response.raise_for_status()
    return response.json().get("result", [])


def save_offset(update_id: int) -> None:
    OFFSET_FILE.write_text(str(update_id))


def send_message(chat_id: str, text: str) -> None:
    requests.post(f"{API_BASE}/sendMessage", data={"chat_id": chat_id, "text": text}, timeout=20)


def format_results(laptops: list[dict]) -> str:
    if not laptops:
        return "Şu an RTX 5070 Ti laptop bulunamadı (kaynak geçici olarak erişilemez olabilir)."
    lines = ["RTX 5070 Ti laptop fiyatları - Avrupa (PriceRunner UK), ucuzdan pahalıya:"]
    for laptop in laptops[:10]:
        lines.append(f"\n£{laptop['price_gbp']:,.2f}  ({laptop['stores']})  {laptop['name']}\n{laptop['url']}")
    return "\n".join(lines)


def run() -> None:
    updates = get_updates()
    if not updates:
        print("Yeni mesaj yok.")
        return

    last_id = None
    for update in updates:
        last_id = update["update_id"]
        message = update.get("message")
        if not message:
            continue

        chat_id = str(message["chat"]["id"])
        if chat_id not in ALLOWED_CHAT_IDS:
            print(f"Tanınmayan chat_id ({chat_id}) - yok sayıldı.")
            continue

        print(f"Sorgu alındı: {message.get('text', '')!r}")
        send_message(chat_id, "Aranıyor, birkaç saniye sürebilir...")
        laptops = search()
        send_message(chat_id, format_results(laptops))

    if last_id is not None:
        save_offset(last_id)


if __name__ == "__main__":
    run()
