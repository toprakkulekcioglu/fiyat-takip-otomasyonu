"""Ana script: tüm siteleri tarar, her ürünü geçmiş medyanla karşılaştırır,
gerçek bir indirim varsa bildirim gönderir, sonra yeni fiyatları kaydeder.

GitHub Actions'ın periyodik olarak çalıştıracağı script budur (Adım 7).

Sıra önemli: önce geçmiş okunup karşılaştırma yapılıyor, SONRA bugünün fiyatı
kaydediliyor - yoksa medyan kendi güncel fiyatını da içine katardı.
"""
from discount_detector import check_discount
from notifier import load_dotenv, notify_discount
from scrapers import amazon, incehesap, itopya, n11, pazarama, trendyol
from scrapers._price import is_accessory, is_external, matches_capacity
from storage import get_price_history, save_snapshot

load_dotenv()

SCRAPERS = [amazon, trendyol, incehesap, itopya, n11, pazarama]
LOOKBACK_DAYS = 45

# Kategoriye göre "hedef fiyat" alarmı - medyan şartından bağımsız, bu fiyata
# ulaşılınca direkt bildirim gider. Kullanıcının kendi belirlediği "bu fiyata
# gelirse alırım" seviyeleri.
PRICE_CEILINGS = {
    "1tb": 6500.0,
    "2tb": 12000.0,
    "2tb-harici": 5000.0,
}


def run() -> None:
    total_products = 0
    total_alerts = 0

    for module in SCRAPERS:
        try:
            products = module.scrape_all()
        except Exception as e:
            print(f"{module.SITE}: TARAMA HATASI - {e}")
            continue

        def is_valid(p: dict) -> bool:
            if not matches_capacity(p["name"], p["capacity"]) or is_accessory(p["name"]):
                return False
            if p["capacity"] in ("1tb", "2tb") and is_external(p["name"]):
                return False
            return True

        products = [p for p in products if is_valid(p)]

        print(f"{module.SITE}: {len(products)} ürün bulundu")
        total_products += len(products)

        for product in products:
            history = get_price_history(product["site"], product["url"], days=LOOKBACK_DAYS)
            history_prices = [price for _, price in history]

            price_ceiling = PRICE_CEILINGS.get(product["capacity"])
            check = check_discount(history_prices, current_price=product["price"], price_ceiling=price_ceiling)
            if check.is_genuine_discount:
                print(f"  INDIRIM: {product['name'][:60]} -> {check.reason}")
                try:
                    notify_discount(product, check)
                    total_alerts += 1
                except Exception as e:
                    print(f"  BILDIRIM HATASI: {e}")

        save_snapshot(products)

    print(f"\nToplam {total_products} ürün tarandı, {total_alerts} bildirim gönderildi.")


if __name__ == "__main__":
    run()
