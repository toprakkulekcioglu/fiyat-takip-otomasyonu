"""Pazarama SSD kategori sayfalarından ürünleri çeker (JS render gerekiyor, Playwright kullanılıyor).

Not: Pazarama robots.txt'i /arama ve /search'ü tamamen yasaklıyor ama kategori
sayfalarını yasaklamıyor. Kapasiteye özel garanti bir filtre URL'si bulunamadığı
için kategoriler çekilip ürün adında "1 TB"/"2 TB" geçenler koda göre filtreleniyor.

scrape_all() her kategori sayfasını TEK SEFER çekip sonra kapasitelere ayırıyor -
scrape(capacity) ayrı ayrı çağrılırsa (örn. test amaçlı) aynı sayfa birden fazla
kez çekilebilir, ama normal akışta (check_and_notify.py) sadece scrape_all() kullanılıyor.
"""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers._browser import fetch_rendered_html
from scrapers._price import MIN_PLAUSIBLE_PRICE, is_nvme, parse_try

SITE = "Pazarama"
BASE_URL = "https://www.pazarama.com"
CATEGORY_URL = "https://www.pazarama.com/ssd-k-K04051"
HARICI_URL = "https://www.pazarama.com/tasinabilir-diskler-k-K04241?ft=&urun-tipi=tasinabilir-ssd"

CAPACITY_PATTERNS = {
    "1tb": re.compile(r"\b1\s*[.,]?\s*tb\b", re.IGNORECASE),
    "2tb": re.compile(r"\b2\s*[.,]?\s*tb\b", re.IGNORECASE),
}


def _scrape_page(url: str) -> list[dict]:
    html = fetch_rendered_html(url, wait_selector='div[data-testid="listing-product-card-grid"]')
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
    if capacity == "2tb-harici":
        products = [p for p in _scrape_page(HARICI_URL) if CAPACITY_PATTERNS["2tb"].search(p["name"])]
    else:
        products = [p for p in _scrape_page(CATEGORY_URL) if CAPACITY_PATTERNS[capacity].search(p["name"])]
        if capacity in ("1tb", "2tb"):
            products = [p for p in products if is_nvme(p["name"])]

    for p in products:
        p["capacity"] = capacity
    return products


def scrape_all() -> list[dict]:
    results = []

    for p in _scrape_page(CATEGORY_URL):
        if not is_nvme(p["name"]):
            continue
        if CAPACITY_PATTERNS["1tb"].search(p["name"]):
            results.append({**p, "capacity": "1tb"})
        elif CAPACITY_PATTERNS["2tb"].search(p["name"]):
            results.append({**p, "capacity": "2tb"})

    for p in _scrape_page(HARICI_URL):
        if CAPACITY_PATTERNS["2tb"].search(p["name"]):
            results.append({**p, "capacity": "2tb-harici"})

    return results


if __name__ == "__main__":
    for p in scrape_all():
        print(p)
