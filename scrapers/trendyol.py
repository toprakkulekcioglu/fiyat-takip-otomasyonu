"""Trendyol kategori sayfalarından SSD ürünlerini çeker (JS render gerekiyor, Playwright kullanılıyor).

Not: Trendyol robots.txt, arama sonucu sayfalarını (/sr, ?q=) yasaklıyor.
Bu yüzden arama yerine sabit kategori/landing sayfaları kullanılıyor.
"""
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers._browser import fetch_rendered_html
from scrapers._price import MIN_PLAUSIBLE_PRICE, parse_try

SITE = "Trendyol"
BASE_URL = "https://www.trendyol.com"
URLS = {
    "1tb": "https://www.trendyol.com/1tb-ssd-y-s3288",
    "2tb": "https://www.trendyol.com/2-tb-ssd-y-s88912",
}


def scrape(capacity: str) -> list[dict]:
    url = URLS[capacity]
    html = fetch_rendered_html(url, wait_selector='a.product-card[data-testid="product-card"]')
    soup = BeautifulSoup(html, "html.parser")

    products = []
    for card in soup.select('a.product-card[data-testid="product-card"]'):
        href = card.get("href")
        name_el = card.select_one('img[data-testid="image-img"]')
        price_el = card.select_one('div[data-testid="price-section"]')
        if not href or not name_el or not price_el:
            continue
        price = parse_try(price_el.get_text())
        if price is None or price < MIN_PLAUSIBLE_PRICE:
            continue
        products.append({
            "site": SITE,
            "name": name_el.get("alt", "").strip(),
            "price": price,
            "url": urljoin(BASE_URL, href),
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
