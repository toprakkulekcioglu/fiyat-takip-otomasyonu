"""Selanik'te (Yunanistan) satılan SSD/harici disk fiyatlarını Skroutz.gr'den
çekip, Sistem 1'in (core/) Türkiye'de zaten sürekli takip ettiği fiyatlarla
karşılaştırır. Otomasyonun (core/check_and_notify.py) parçası değil, sadece
bot/web tetiklemesiyle çalışır - aynı core/ verisini SADECE OKUYOR, hiçbir
şey yazmıyor (Sistem 1'in kendi tabanına dokunmuyoruz).

Kapasite anahtarları ("1tb", "2tb", "2tb-harici") core/check_and_notify.py'deki
ile birebir aynı - böylece Türkiye tarafı için storage.get_current_min_price()
doğru veriyi bulabiliyor.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _skroutz_cards import parse_cards
from scrapers._browser import fetch_multiple_rendered_html
from storage import get_current_min_price

CATEGORY_URLS = {
    "1tb": "https://www.skroutz.gr/c/88/ssd-sklhroi-diskoi/f/909634_916680/1TB-NVMe.html",
    "2tb": "https://www.skroutz.gr/c/88/ssd-sklhroi-diskoi/f/909635_916680/2TB-NVMe.html",
    "2tb-harici": "https://www.skroutz.gr/c/87/eksoterikoi-sklhroi-diskoi/f/5987_660210/SSD-2TB.html",
}

CAPACITY_LABELS = {
    "1tb": "1TB NVMe SSD",
    "2tb": "2TB NVMe SSD",
    "2tb-harici": "2TB Harici/Taşınabilir SSD",
}


def compare_all() -> list[dict]:
    """Her kapasite için Selanik'teki (Skroutz) en ucuz fiyatı Türkiye'deki
    (Sistem 1'in son 24 saatte bulduğu) en ucuz fiyatla eşleştirir. Selanik
    tarafında sonuç bulunamazsa "greek" None olur - o zaman karşılaştırma
    yapılamaz, sadece Türkiye fiyatı (varsa) gösterilebilir."""
    capacities = list(CATEGORY_URLS)
    requests_list = [(CATEGORY_URLS[c], "li.card[data-skuid]") for c in capacities]
    htmls = fetch_multiple_rendered_html(requests_list, timeout_ms=45000)

    results = []
    for capacity, html in zip(capacities, htmls):
        greek = None
        if isinstance(html, Exception):
            print(f"  {CATEGORY_URLS[capacity]}: HATA - {html}", flush=True)
        else:
            cards = parse_cards(html)
            print(f"  {CATEGORY_URLS[capacity]}: {len(cards)} urun", flush=True)
            if cards:
                greek = min(cards, key=lambda c: c["price_eur"])

        results.append({
            "capacity": capacity,
            "label": CAPACITY_LABELS[capacity],
            "greek": greek,
            "tr_price_try": get_current_min_price(capacity, hours=24),
        })

    return results


if __name__ == "__main__":
    for row in compare_all():
        print(f"\n=== {row['label']} ===")
        if row["greek"]:
            print(f"  Selanik: {row['greek']['price_eur']:,.2f} EUR - {row['greek']['name']}")
        else:
            print("  Selanik: bulunamadı")
        if row["tr_price_try"] is not None:
            print(f"  Türkiye (en ucuz, son 24 saat): {row['tr_price_try']:,.2f} TL")
        else:
            print("  Türkiye: veri yok")
