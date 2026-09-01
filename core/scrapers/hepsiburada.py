"""Hepsiburada arama sonuçlarından SSD ürünlerini çeker (JS render gerekiyor, Playwright kullanılıyor).

DURUM: Test edildi, ÇALIŞMIYOR. Headless Playwright ile istek atıldığında Akamai
bot koruması "Hepsiburada | Güvenlik" CAPTCHA/blok sayfasına yönlendiriyor. CAPTCHA
çözme veya parmak izi sahteciliği gibi bir bypass yapılmadığı için bu scraper
test_scrapers.py'a dahil edilmedi. Kod referans/gelecekte tekrar denemek için duruyor.
"""
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers._browser import fetch_rendered_html
from scrapers._price import MIN_PLAUSIBLE_PRICE, parse_try

SITE = "Hepsiburada"
BASE_URL = "https://www.hepsiburada.com"
URLS = {
    "1tb": "https://www.hepsiburada.com/ara?q=1tb+ssd",
    "2tb": "https://www.hepsiburada.com/ara?q=2tb+ssd",
}


def scrape(capacity: str) -> list[dict]:
    url = URLS[capacity]
    html = fetch_rendered_html(url, wait_selector='li[class*="productListContent"]')
    soup = BeautifulSoup(html, "html.parser")

    products = []
    for card in soup.select('li[class*="productListContent"]'):
        link_el = card.select_one("a[title][href]")
        price_el = card.select_one('div[data-test-id^="final-price"]')
        if not link_el or not price_el:
            continue
        price = parse_try(price_el.get_text())
        if price is None or price < MIN_PLAUSIBLE_PRICE:
            continue
        products.append({
            "site": SITE,
            "name": link_el.get("title", "").strip(),
            "price": price,
            "url": urljoin(BASE_URL, link_el.get("href")),
            "capacity": capacity,
        })
    return products


def scrape_all() -> list[dict]:
    results = []
    for capacity in URLS:
        results.extend(scrape(capacity))
    return results


if __name__ == "__main__":
    for p in scrape_all():
        print(p)
