"""Her scraper'ı çalıştırıp terminal çıktısıyla gerçek veri çektiğini doğrulamak için.

Not: hepsiburada.py bilerek burada değil - Akamai bot koruması otomatik istekleri
CAPTCHA sayfasına yönlendiriyor, bypass yapmadığımız için MVP'den çıkarıldı.
Detay için scrapers/hepsiburada.py içindeki not'a bak.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scrapers import amazon, incehesap, itopya, n11, pazarama, trendyol

SCRAPERS = [amazon, trendyol, incehesap, itopya, n11, pazarama]

if __name__ == "__main__":
    for module in SCRAPERS:
        print(f"\n=== {module.SITE} ===")
        try:
            products = module.scrape_all()
        except Exception as e:
            print(f"HATA: {e}")
            continue
        print(f"{len(products)} ürün bulundu")
        for p in products[:5]:
            print(f"  {p['name'][:60]:<60} {p['price']:>10.2f} TL  {p['url']}")
