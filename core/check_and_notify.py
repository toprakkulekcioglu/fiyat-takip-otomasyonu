"""Ana script: tüm siteleri tarar, her ürünü geçmiş medyanla karşılaştırır,
gerçek bir indirim varsa bildirim gönderir, sonra yeni fiyatları kaydeder.

GitHub Actions'ın periyodik olarak çalıştıracağı script budur (Adım 7).

Sıra önemli: önce geçmiş okunup karşılaştırma yapılıyor, SONRA bugünün fiyatı
kaydediliyor - yoksa medyan kendi güncel fiyatını da içine katardı.
"""
from discount_detector import check_discount
from excluded_products import EXCLUDED_URLS
from notifier import load_dotenv, notify_discount
from scrapers import amazon, incehesap, itopya, n11, pazarama, trendyol
from scrapers._price import is_accessory, is_external, matches_capacity
from site_router import find_scraper
from storage import get_price_history, save_snapshot
from subscriptions_store import SUBSCRIPTION_CAPACITY, get_active_subscriptions

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
            if p["url"] in EXCLUDED_URLS:
                return False
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

    total_products, total_alerts = check_subscriptions(total_products, total_alerts)

    print(f"\nToplam {total_products} ürün tarandı, {total_alerts} bildirim gönderildi.")


def check_subscriptions(total_products: int, total_alerts: int) -> tuple[int, int]:
    """Kullanıcının web sayfasından (web/ssd-takip.html) takibe aldığı ürünleri
    kontrol eder - sabit 3 kategoriden bağımsız, kullanıcı bazlı ek liste.
    Aynı medyan mantığını (`discount_detector.py`) kullanıyor, hedef fiyat
    (price_ceiling) yok çünkü bu ürünler için kullanıcı bir hedef belirlemedi."""
    for sub in get_active_subscriptions():
        scraper = find_scraper(sub["url"])
        if scraper is None:
            continue
        try:
            result = scraper.scrape_product(sub["url"])
        except Exception as e:
            print(f"  ABONELİK TARAMA HATASI ({sub['name'][:60]}): {e}")
            continue
        if result is None:
            continue

        total_products += 1
        history = get_price_history(sub["site"], sub["url"], days=LOOKBACK_DAYS)
        history_prices = [price for _, price in history]

        check = check_discount(history_prices, current_price=result["price"])
        if check.is_genuine_discount:
            print(f"  ABONELİK İNDİRİMİ: {sub['name'][:60]} -> {check.reason}")
            product = {"site": sub["site"], "name": result["name"], "url": sub["url"]}
            try:
                notify_discount(product, check)
                total_alerts += 1
            except Exception as e:
                print(f"  BİLDİRİM HATASI: {e}")

        save_snapshot([{
            "site": sub["site"],
            "capacity": SUBSCRIPTION_CAPACITY,
            "name": result["name"],
            "url": sub["url"],
            "price": result["price"],
        }])

    return total_products, total_alerts


if __name__ == "__main__":
    run()
