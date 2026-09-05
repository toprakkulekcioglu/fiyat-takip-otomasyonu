"""Telegram webhook ile ÇALIŞAN, anlık cevap veren laptop arama botu.

Render.com gibi 7/24 açık bir sunucuda sürekli çalışan bir web servisi.
Telegram, mesaj geldiği an bu servise kendisi POST isteği atıyor (biz
sormuyoruz, o bize söylüyor) - bu yüzden gerçekten anlık.

Önemli: Telegram bir bot için AYNI ANDA hem webhook hem polling (getUpdates)
kullanmana izin vermiyor.

Anahtar kelimeyle dallanma:
- "ryzen" geçen mesaj  -> Selanik (Yunanistan), Ryzen AI 9 365+ işlemcili laptoplar
- "teşekkür" geçen mesaj -> Selanik (Yunanistan), RTX 5070 Ti/5080/5090 laptoplar
- Diğer her şey -> kısa bir yönlendirme mesajı

Not: Eski sistem (Türkiye vs. yurtdışı/İngiltere PriceRunner karşılaştırması,
search_laptops.py + search_laptops_tr.py + matcher.py) SİLİNMEDİ, kod olarak
duruyor ama bu bota bağlı DEĞİL - devre dışı. İstenirse tekrar bir anahtar
kelimeye bağlanıp aktif edilebilir.
"""
import os
import sys
import threading
import uuid
from pathlib import Path

import requests
from flask import Flask, jsonify, request

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from currency import eur_to_try_rate
from manis import rastgele_mani
from notifier import load_dotenv
from search_laptops_greece import search_by_cpu as greece_search_by_cpu
from search_laptops_greece import search_by_gpu as greece_search_by_gpu
from subscription_api import subscription_api

load_dotenv()

BOT_TOKEN = os.environ["LAPTOP_TELEGRAM_BOT_TOKEN"]
ALLOWED_CHAT_IDS = {
    cid.strip() for cid in os.environ["LAPTOP_TELEGRAM_ALLOWED_CHAT_IDS"].split(",") if cid.strip()
}
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)
# SSD/harici disk takip sisteminin web sayfası (web/ssd-takip.html) için
# /api/track, /api/subscriptions route'ları - ayrı bir Render servisi açmamak
# için bu zaten 7/24 açık olan servise ekleniyor, bkz. core/subscription_api.py.
app.register_blueprint(subscription_api)


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


MAX_RESULTS = 5  # En ucuzdan bu kadarı önerilsin - tam liste yerine


def format_greece_results(laptops: list[dict], rate: float, baslik: str) -> str:
    lines = [rastgele_mani(), "", baslik, ""]

    if not laptops:
        lines.append("Şu an bu kritere uyan bir laptop bulunamadı.")
        return "\n".join(lines)

    for laptop in laptops[:MAX_RESULTS]:
        try_equivalent = laptop["price_eur"] * rate
        lines.append(laptop["name"])
        lines.append(f"{laptop['price_eur']:,.2f} EUR  (~{try_equivalent:,.2f} TL, güncel kur: {rate:.2f})")
        lines.append(laptop["url"])
        lines.append("")

    if len(laptops) > MAX_RESULTS:
        lines.append(f"(Toplam {len(laptops)} sonuç bulundu, en ucuz {MAX_RESULTS} tanesi gösterildi.)")

    return "\n".join(lines)


_search_lock = threading.Lock()


def handle_greece_query(chat_id: str, search_fn, baslik: str) -> None:
    """Arka planda çalışır - Telegram'ı (ve kullanıcıyı) bekletmemek için ayrı thread'de.

    Aynı anda sadece BİR arama çalışabilir (_search_lock) - Render'ın 512MB'lık
    ücretsiz sunucusunda, art arda gelen birden fazla sorgu her biri kendi
    Chromium'unu açarsa bellek yetersizliğinden süreç çöküyordu (birden fazla
    tarayıcı aynı anda RAM'i tüketiyordu). Kilit boştaysa sorgu sıraya girip
    bekliyor, kullanıcı da bunu bir mesajla öğreniyor."""
    if not _search_lock.acquire(blocking=False):
        print(f"Baska bir arama surerken yeni sorgu geldi ({chat_id}) - bekletiliyor.", flush=True)
        try:
            send_message(chat_id, "Şu anda başka bir arama sürüyor, senin sıran gelince otomatik başlayacak...")
        except Exception as e:
            print(f"BEKLEME MESAJI GONDERILEMEDI: {type(e).__name__}: {e}", flush=True)
        _search_lock.acquire()  # sırada bekle

    try:
        laptops = search_fn()
        print(f"Selanik taramasi: {len(laptops)} urun bulundu", flush=True)

        print("Kur cekiliyor...", flush=True)
        rate = eur_to_try_rate()
        print(f"Kur alindi: {rate}", flush=True)

        text = format_greece_results(laptops, rate, baslik)
        print(f"Mesaj hazir ({len(text)} karakter), gonderiliyor...", flush=True)
        send_long_message(chat_id, text)
        print("Mesaj gonderildi.", flush=True)
    except Exception as e:
        print(f"HANDLE_QUERY HATASI: {type(e).__name__}: {e}", flush=True)
        try:
            send_message(chat_id, f"Bir hata oldu, tekrar dener misin? ({e})")
        except Exception as e2:
            print(f"HATA MESAJI DA GONDERILEMEDI: {type(e2).__name__}: {e2}", flush=True)
    finally:
        _search_lock.release()


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

    text = message.get("text", "")
    print(f"Sorgu alındı ({chat_id}): {text!r}")
    lowered = text.lower()

    if "ryzen" in lowered:
        search_fn, baslik = greece_search_by_cpu, "Selanik - Ryzen AI 9 365+ işlemcili laptoplar"
    elif "teşekkür" in lowered or "tesekkur" in lowered:
        search_fn, baslik = greece_search_by_gpu, "Selanik - RTX 5070 Ti/5080/5090 laptoplar"
    else:
        try:
            send_message(
                chat_id,
                "Ne aramamı istediğini anlamadım.\n\n"
                "'ryzen' yaz: Ryzen AI 9 365+ işlemcili laptoplar (Selanik)\n"
                "'teşekkür' yaz: RTX 5070 Ti/5080/5090 laptoplar (Selanik)",
            )
        except Exception as e:
            print(f"YONLENDIRME MESAJI GONDERILEMEDI: {type(e).__name__}: {e}", flush=True)
        return "ok", 200

    try:
        send_message(chat_id, "İstek gönderildi, aranıyor... (genelde 2-3 dakika sürüyor)")
    except Exception as e:
        print(f"ACK MESAJI GONDERILEMEDI: {type(e).__name__}: {e}", flush=True)
    threading.Thread(target=handle_greece_query, args=(chat_id, search_fn, baslik), daemon=True).start()
    return "ok", 200


_jobs: dict[str, dict] = {}  # job_id -> {"status": "running"|"done"|"error", "data": ...}


def _run_web_search(job_id: str, search_fn, baslik: str) -> None:
    with _search_lock:
        try:
            laptops = search_fn()
            print(f"[web] Selanik taramasi: {len(laptops)} urun bulundu", flush=True)
            rate = eur_to_try_rate()
            _jobs[job_id] = {
                "status": "done",
                "data": {
                    "baslik": baslik,
                    "rate": rate,
                    "total": len(laptops),
                    "laptops": [
                        {**laptop, "price_try": round(laptop["price_eur"] * rate, 2)}
                        for laptop in laptops[:MAX_RESULTS]
                    ],
                },
            }
        except Exception as e:
            print(f"[web] ARAMA HATASI: {type(e).__name__}: {e}", flush=True)
            _jobs[job_id] = {"status": "error", "data": str(e)}


def _cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/api/search", methods=["POST", "OPTIONS"])
def api_search():
    if request.method == "OPTIONS":
        return _cors(app.make_default_options_response())

    body = request.get_json(silent=True) or {}
    kind = body.get("type")
    if kind == "cpu":
        search_fn, baslik = greece_search_by_cpu, "Ryzen AI 9 365+ işlemcili laptoplar (Selanik)"
    elif kind == "gpu":
        search_fn, baslik = greece_search_by_gpu, "RTX 5070 Ti/5080/5090 laptoplar (Selanik)"
    else:
        return _cors(jsonify({"error": "type 'cpu' veya 'gpu' olmalı"})), 400

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "data": None}
    threading.Thread(target=_run_web_search, args=(job_id, search_fn, baslik), daemon=True).start()
    return _cors(jsonify({"job_id": job_id}))


@app.route("/api/result/<job_id>", methods=["GET"])
def api_result(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        return _cors(jsonify({"status": "not_found"})), 404
    return _cors(jsonify(job))


@app.route("/", methods=["GET"])
def health():
    return "Laptop bot ayakta.", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
