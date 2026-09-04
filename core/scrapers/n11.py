"""n11.com kategori sayfalarından SSD ürünlerini çeker (sunucu tarafında render ediliyor, JS gerekmiyor)."""
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scrapers._browser import fetch_rendered_html
from scrapers._price import MIN_PLAUSIBLE_PRICE, is_nvme, is_ssd, parse_try

SITE = "n11.com"
BASE_URL = "https://www.n11.com"
URLS = {
    "1tb": "https://www.n11.com/bilgisayar/bilgisayar-bilesenleri/hard-disk?q=1+tb+nvme+ssd",
    "2tb": "https://www.n11.com/bilgisayar/bilgisayar-bilesenleri/hard-disk?q=2+tb+ssd",
    "2tb-harici": "https://www.n11.com/bilgisayar/yedekleme-urunleri/tasinabilir-disk?q=2tb+ssd",
}
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def scrape(capacity: str) -> list[dict]:
    url = URLS[capacity]
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    products = []
    for card in soup.select("a.product-item[href]"):
        name_el = card.select_one("h2.product-item-title")
        price_el = card.select_one("h3.price-currency")
        if not name_el or not price_el:
            continue
        name = name_el.get_text(strip=True)
        if capacity in ("1tb", "2tb") and not is_nvme(name):
            continue
        if capacity == "2tb-harici" and not is_ssd(name):
            continue
        price = parse_try(price_el.get_text())
        if price is None or price < MIN_PLAUSIBLE_PRICE:
            continue
        products.append({
            "site": SITE,
            "name": name,
            "price": price,
            "url": urljoin(BASE_URL, card.get("href")),
            "capacity": capacity,
        })
    return products


def scrape_all() -> list[dict]:
    results = []
    for capacity in URLS:
        results.extend(scrape(capacity))
        time.sleep(2)
    return results


def scrape_product(url: str) -> dict | None:
    """Kullanıcının verdiği tekil bir ürün linkinden ad+fiyat çeker.

    Kategori sayfalarının aksine (düz `requests` yeterli), ürün sayfasında fiyat
    Vue.js ile İSTEMCİ tarafında dolduruluyor (ham HTML'de <ins></ins> boş geliyor)
    - bu yüzden burada Playwright (fetch_rendered_html) gerekiyor.
    """
    html = fetch_rendered_html(url, wait_selector=".newPrice ins")
    soup = BeautifulSoup(html, "html.parser")

    name_el = soup.select_one("h1")
    price_el = soup.select_one(".newPrice ins")
    if not name_el or not price_el:
        return None
    price = parse_try(price_el.get_text())
    if price is None:
        return None
    return {"name": name_el.get_text(strip=True), "price": price}


if __name__ == "__main__":
    for p in scrape_all():
        print(p)
