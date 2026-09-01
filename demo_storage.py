"""storage.py'nin zaman içinde biriken geçmişle nasıl davrandığını gösteren demo.

Gerçek bir ürün için 45 günlük simüle edilmiş fiyat geçmişi ekler (günde bir kayıt),
sonra get_price_history/get_latest_price gibi sorguların sonucunu yazdırır. Ayrı bir
demo veritabanı dosyası kullanır - gerçek price_history.db'ye karışmaz.
"""
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from storage import get_latest_price, get_price_history, get_tracked_products, save_snapshot

DEMO_DB = Path(__file__).parent / "data" / "demo_price_history.db"
DEMO_DB.unlink(missing_ok=True)

SITE = "DemoSite"
URL = "https://demo.example/kingston-nv3-1tb"
NAME = "Kingston NV3 1TB Demo SSD"

random.seed(42)

print("45 günlük simüle fiyat geçmişi ekleniyor (günde 1 kayıt)...")
today = datetime.now(timezone.utc)
base_price = 8000.0
for days_ago in range(45, 0, -1):
    # Normal dalgalanma + günlük 43'te yapay zam, günlük 40'ta "sahte indirim" senaryosu
    if days_ago > 42:
        price = base_price
    elif days_ago == 41:
        price = base_price * 1.35  # yapay zam
    elif 30 < days_ago < 41:
        price = base_price * 1.35 + random.uniform(-100, 100)
    else:
        price = base_price + random.uniform(-150, 150)

    scraped_at = today - timedelta(days=days_ago)
    save_snapshot(
        [{"site": SITE, "capacity": "1tb", "name": NAME, "url": URL, "price": round(price, 2)}],
        db_path=DEMO_DB,
        scraped_at=scraped_at,
    )

print("Bugünün fiyatı da ekleniyor (gerçek bir düşüş senaryosu)...")
save_snapshot(
    [{"site": SITE, "capacity": "1tb", "name": NAME, "url": URL, "price": 5800.0}],
    db_path=DEMO_DB,
    scraped_at=today,
)

print("\n--- get_tracked_products() ---")
for site, url, name in get_tracked_products(DEMO_DB):
    print(f"  {site} | {name} | {url}")

print("\n--- get_price_history(gün=60) ilk ve son 3 kayıt ---")
history = get_price_history(SITE, URL, days=60, db_path=DEMO_DB)
print(f"Toplam {len(history)} kayıt")
for scraped_at, price in history[:3]:
    print(f"  {scraped_at[:10]}  {price:>10.2f} TL")
print("  ...")
for scraped_at, price in history[-3:]:
    print(f"  {scraped_at[:10]}  {price:>10.2f} TL")

print("\n--- get_price_history(gün=15) - sadece son 15 gün ---")
recent = get_price_history(SITE, URL, days=15, db_path=DEMO_DB)
print(f"Toplam {len(recent)} kayıt (45 günlük geçmişten sadece son 15 gün döndü)")

print("\n--- get_latest_price() ---")
print(f"Son fiyat: {get_latest_price(SITE, URL, db_path=DEMO_DB)} TL")
