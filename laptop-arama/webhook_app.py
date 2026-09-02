"""Telegram webhook ile ÇALIŞAN, anlık cevap veren laptop karşılaştırma botu.

polling yapan telegram_bot.py'nin yerine geçiyor - bu, Render.com gibi 7/24 açık
bir sunucuda sürekli çalışan bir web servisi. Telegram, mesaj geldiği an bu
servise kendisi POST isteği atıyor (biz sormuyoruz, o bize söylüyor) - bu yüzden
gerçekten anlık.

Önemli: Telegram bir bot için AYNI ANDA hem webhook hem polling (getUpdates)
kullanmana izin vermiyor. Bu devreye girince eski GitHub Actions polling
workflow'u devre dışı bırakıldı.
"""
import os
import sys
import threading
from pathlib import Path

import requests
from flask import Flask, request

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

app = Flask(__name__)


TELEGRAM_MAX_LEN = 4096  # Telegram'ın tek mesaj için karakter sınırı


def send_message(chat_id: str, text: str) -> None:
    """Telegram API'sinin CEVABINI kontrol ediyor - HTTP isteği başarılı görünse
    bile Telegram mesajı reddetmiş olabilir (örn. 4096 karakter sınırı aşılınca),
    bu kontrol olmadan hata sessizce yutuluyordu."""
    response = requests.post(f"{API_BASE}/sendMessage", data={"chat_id": chat_id, "text": text}, timeout=20)
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram mesaji reddetti: {data}")


def send_long_message(chat_id: str, text: str) -> None:
    """4096 karakteri aşan mesajları, ürün bloklarını (boş satırla ayrılmış)
    bölmeden birden fazla mesaja parçalayıp gönderir."""
    if len(text) <= TELEGRAM_MAX_LEN:
        send_message(chat_id, text)
        return

    blocks = text.split("\n\n")
    chunk = ""
    for block in blocks:
        candidate = f"{chunk}\n\n{block}" if chunk else block
        if len(candidate) > TELEGRAM_MAX_LEN:
            if chunk:
                send_message(chat_id, chunk)
            chunk = block
        else:
            chunk = candidate
    if chunk:
        send_message(chat_id, chunk)


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


def handle_query(chat_id: str) -> None:
    """Arka planda çalışır - Telegram'ı (ve kullanıcıyı) bekletmemek için ayrı thread'de."""
    try:
        tr_laptops = search_tr()
        print(f"TR taramasi: {len(tr_laptops)} urun bulundu", flush=True)
        global_laptops = search_global()
        print(f"Global tarama: {len(global_laptops)} urun bulundu", flush=True)
        pairs = match(tr_laptops, global_laptops)
        print(f"Eslesme: {len(pairs)}", flush=True)

        print("Kur cekiliyor...", flush=True)
        rate = gbp_to_try_rate()
        print(f"Kur alindi: {rate}", flush=True)

        text = format_results(pairs, rate)
        print(f"Mesaj hazir ({len(text)} karakter), gonderiliyor...", flush=True)
        send_long_message(chat_id, text)
        print("Mesaj gonderildi.", flush=True)
    except Exception as e:
        print(f"HANDLE_QUERY HATASI: {type(e).__name__}: {e}", flush=True)
        try:
            send_message(chat_id, f"Bir hata oldu, tekrar dener misin? ({e})")
        except Exception as e2:
            print(f"HATA MESAJI DA GONDERILEMEDI: {type(e2).__name__}: {e2}", flush=True)


@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message")
    if not message:
        return "ok", 200

    chat_id = str(message["chat"]["id"])
    if chat_id not in ALLOWED_CHAT_IDS:
        print(f"Tanınmayan chat_id ({chat_id}) - yok sayıldı.")
        return "ok", 200

    print(f"Sorgu alındı ({chat_id}): {message.get('text', '')!r}")
    try:
        send_message(chat_id, "İstek gönderildi, aranıyor...")
    except Exception as e:
        print(f"ACK MESAJI GONDERILEMEDI: {type(e).__name__}: {e}", flush=True)
    threading.Thread(target=handle_query, args=(chat_id,), daemon=True).start()
    return "ok", 200


@app.route("/", methods=["GET"])
def health():
    return "Laptop bot ayakta.", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
