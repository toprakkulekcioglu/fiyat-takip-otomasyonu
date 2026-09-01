"""Tüm scraper'ları çalıştırıp bulunan fiyatları geçmiş deposuna kaydeder.

GitHub Actions'ta zamanlanmış olarak bu script çalıştırılacak (Adım 7).
"""
from scrapers import amazon, incehesap, itopya, n11, pazarama, trendyol
from storage import save_snapshot

SCRAPERS = [amazon, trendyol, incehesap, itopya, n11, pazarama]

if __name__ == "__main__":
    total = 0
    for module in SCRAPERS:
        try:
            products = module.scrape_all()
        except Exception as e:
            print(f"{module.SITE}: HATA - {e}")
            continue
        saved = save_snapshot(products)
        total += saved
        print(f"{module.SITE}: {saved} fiyat kaydedildi")
    print(f"\nToplam: {total} fiyat kaydı eklendi")
