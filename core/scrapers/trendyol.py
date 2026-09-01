"""Trendyol kategori sayfalarından SSD ürünlerini çeker (JS render gerekiyor, Playwright kullanılıyor).

Not: Trendyol robots.txt, arama sonucu sayfalarını (/sr, ?q=) yasaklıyor.
Bu yüzden arama yerine sabit kategori/landing sayfaları kullanılıyor.

"2tb-harici" için kapasiteye özel bir landing sayfası bulunamadı - genel "taşınabilir
SSD" kategorisi çekilip ürün adına göre 2TB filtreleniyor (Pazarama'daki gibi).
"""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers._browser import fetch_rendered_html
from scrapers._price import MIN_PLAUSIBLE_PRICE, is_nvme, is_ssd, parse_try

SITE = "Trendyol"
BASE_URL = "https://www.trendyol.com"
URLS = {
    "1tb": "https://www.trendyol.com/1tb-ssd-y-s3288",
    "2tb": "https://www.trendyol.com/2-tb-ssd-y-s88912",
    "2tb-harici": "https://www.trendyol.com/tasinabilir-ssd-x-c108110",
}
CAPACITY_2TB_PATTERN = re.compile(r"\b2\s*[.,]?\s*tb\b", re.IGNORECASE)


def _fetch_cards(url: str) -> list[dict]:
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
        })
    return products


def scrape(capacity: str) -> list[dict]:
    products = _fetch_cards(URLS[capacity])

    if capacity in ("1tb", "2tb"):
        products = [p for p in products if is_nvme(p["name"])]
    elif capacity == "2tb-harici":
        products = [p for p in products if is_ssd(p["name"]) and CAPACITY_2TB_PATTERN.search(p["name"])]

    for p in products:
        p["capacity"] = capacity
    return products


def scrape_all() -> list[dict]:
    results = []
    for capacity in URLS:
        results.extend(scrape(capacity))
    return results


if __name__ == "__main__":
    for p in scrape_all():
        print(p)
