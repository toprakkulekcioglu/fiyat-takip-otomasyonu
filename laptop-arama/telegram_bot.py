"""Telegram'dan bu bota (sen veya arkadaşın) herhangi bir mesaj atıldığında,
Türkiye'de VE yurtdışında (PriceRunner UK üzerinden Avrupa) satılan, eşleşen RTX
5070 Ti laptopları bulup fiyatlarını (güncel kurla) karşılaştırıp geri gönderen "bot".

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

from currency import gbp_to_try_rate
from manis import rastgele_mani
from matcher import match
from notifier import load_dotenv
from search_laptops import search as search_global
from search_laptops_tr import search as search_tr

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


def format_results(pairs: list[dict], rate: float) -> str:
    lines = [rastgele_mani(), ""]

    if not pairs:
        lines.append(
            "Şu an Türkiye ve yurtdışı kataloglarında eşleştirilebilen 12GB+ "
            "RTX 50 serisi (5070 Ti/5080/5090) laptop bulunamadı - bu GPU'lar "
            "çok yeni, kataloglar henüz örtüşmüyor olabilir."
        )
        return "\n".join(lines)

    for pair in pairs:
        tr = pair["tr"]
        glb = pair["global"]
        try_equivalent = glb["price_gbp"] * rate
        etiket = (
            "(kesin eşleşme - aynı model kodu)"
            if pair["confidence"] == "high"
            else "(yaklaşık eşleşme - aynı seri, yapılandırma farklı olabilir, almadan önce kontrol et)"
        )
        lines.append(f"{tr['name']}  {etiket}")
        lines.append(f"Türkiye: {tr['price_try']:,.2f} TL")
        lines.append(f"{tr['url']}")
        lines.append(
            f"Yurtdışı: £{glb['price_gbp']:,.2f} (~{try_equivalent:,.2f} TL, güncel kur: {rate:.2f})"
        )
        lines.append(f"{glb['url']}")
        lines.append("")

    return "\n".join(lines)


def run() -> None:
    updates = get_updates()
    if not updates:
        print("Yeni mesaj yok.")
        return

    last_id = None
    triggered_for = []
    for update in updates:
        last_id = update["update_id"]
        message = update.get("message")
        if not message:
            continue

        chat_id = str(message["chat"]["id"])
        if chat_id not in ALLOWED_CHAT_IDS:
            print(f"Tanınmayan chat_id ({chat_id}) - yok sayıldı.")
            continue

        print(f"Sorgu alındı ({chat_id}): {message.get('text', '')!r}")
        send_message(chat_id, "İstek gönderildi, aranıyor...")
        triggered_for.append(chat_id)

    if last_id is not None:
        save_offset(last_id)

    if not triggered_for:
        return

    tr_laptops = search_tr()
    global_laptops = search_global()
    pairs = match(tr_laptops, global_laptops)
    rate = gbp_to_try_rate()
    result_text = format_results(pairs, rate)

    for chat_id in triggered_for:
        send_message(chat_id, result_text)


if __name__ == "__main__":
    run()
