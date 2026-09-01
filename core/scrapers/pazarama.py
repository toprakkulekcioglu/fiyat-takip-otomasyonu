"""Pazarama SSD kategori sayfasından ürünleri çeker (JS render gerekiyor, Playwright kullanılıyor).

Not: Pazarama robots.txt'i /arama ve /search'ü tamamen yasaklıyor ama kategori
sayfasını (/ssd-k-K04051) yasaklamıyor. Kategoride kapasiteye özel garanti bir filtre
URL'si bulunamadığı için genel SSD kategorisi çekilip ürün adında "1 TB"/"2 TB"
geçenler koda göre filtreleniyor.
"""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers._browser import fetch_rendered_html
from scrapers._price import MIN_PLAUSIBLE_PRICE, parse_try

SITE = "Pazarama"
BASE_URL = "https://www.pazarama.com"
CATEGORY_URL = "https://www.pazarama.com/ssd-k-K04051"

CAPACITY_PATTERNS = {
    "1tb": re.compile(r"\b1\s*[.,]?\s*tb\b", re.IGNORECASE),
    "2tb": re.compile(r"\b2\s*[.,]?\s*tb\b", re.IGNORECASE),
}


def _scrape_category() -> list[dict]:
    html = fetch_rendered_html(CATEGORY_URL, wait_selector='div[data-testid="listing-product-card-grid"]')
    soup = BeautifulSoup(html, "html.parser")

    products = []
    for card in soup.select('div[data-testid="listing-product-card-grid"]'):
        link_el = card.select_one("a[title][href]")
        price_el = card.select_one(
            'div[data-testid="base-product-card-price-container"] p[class*="text-gray-400"]'
        )
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
        })
    return products


def scrape(capacity: str) -> list[dict]:
    pattern = CAPACITY_PATTERNS[capacity]
    products = [p for p in _scrape_category() if pattern.search(p["name"])]
    for p in products:
        p["capacity"] = capacity
    return products


def scrape_all() -> list[dict]:
    all_products = _scrape_category()
    results = []
    for capacity, pattern in CAPACITY_PATTERNS.items():
        for p in all_products:
            if pattern.search(p["name"]):
                results.append({**p, "capacity": capacity})
    return results


if __name__ == "__main__":
    for p in scrape_all():
        print(p)
