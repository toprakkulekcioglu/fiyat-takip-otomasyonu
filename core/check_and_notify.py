"""Ana script: tüm siteleri tarar, her ürünü geçmiş medyanla karşılaştırır,
gerçek bir indirim varsa bildirim gönderir, sonra yeni fiyatları kaydeder.

GitHub Actions'ın periyodik olarak çalıştıracağı script budur (Adım 7).

Sıra önemli: önce geçmiş okunup karşılaştırma yapılıyor, SONRA bugünün fiyatı
kaydediliyor - yoksa medyan kendi güncel fiyatını da içine katardı.
"""
from discount_detector import check_discount
from notifier import load_dotenv, notify_discount
from scrapers import amazon, incehesap, itopya, n11, pazarama, trendyol
from storage import get_price_history, save_snapshot

load_dotenv()

SCRAPERS = [amazon, trendyol, incehesap, itopya, n11, pazarama]
LOOKBACK_DAYS = 45


def run() -> None:
    total_products = 0
    total_alerts = 0

    for module in SCRAPERS:
        try:
            products = module.scrape_all()
        except Exception as e:
            print(f"{module.SITE}: TARAMA HATASI - {e}")
            continue

        print(f"{module.SITE}: {len(products)} ürün bulundu")
        total_products += len(products)

        for product in products:
            history = get_price_history(product["site"], product["url"], days=LOOKBACK_DAYS)
            history_prices = [price for _, price in history]

            check = check_discount(history_prices, current_price=product["price"])
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
