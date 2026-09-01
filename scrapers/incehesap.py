"""incehesap.com kategori sayfalarından SSD ürünlerini çeker.

Sayfa sunucu tarafında render ediliyor ve her ürün kartında hazır bir JSON
(data-product attribute) var - metin ayrıştırmaya gerek yok, direkt parse ediliyor.

Not: Site Cloudflare'in otomatik ("Just a moment...") JS doğrulamasını kullanıyor.
Bu, düz `requests` isteklerini 403 ile engelliyor ama interaktif bir CAPTCHA değil -
gerçek bir tarayıcı motoru (Playwright) birkaç saniyede otomatik geçiyor, bu yüzden
diğer JS-render gerektiren sitelerle aynı yöntem kullanılıyor.
"""
import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers._browser import fetch_rendered_html
from scrapers._price import MIN_PLAUSIBLE_PRICE

SITE = "incehesap.com"
BASE_URL = "https://www.incehesap.com"
URLS = {
    "1tb": "https://www.incehesap.com/ssd-harddisk-fiyatlari/ozellik-15480/",
    "2tb": "https://www.incehesap.com/ssd-harddisk-fiyatlari/ozellik-60381/",
}


def scrape(capacity: str) -> list[dict]:
    url = URLS[capacity]
    html = fetch_rendered_html(url, wait_selector="a.product[data-product]", timeout_ms=25000)
    soup = BeautifulSoup(html, "html.parser")

    products = []
    for card in soup.select("a.product[data-product]"):
        href = card.get("href")
        raw = card.get("data-product")
        if not href or not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        price = data.get("price")
        name = data.get("name")
        if not name or price is None or data.get("category") != "SSD Depolama":
            continue
        price = float(price)
        if price < MIN_PLAUSIBLE_PRICE:
            continue
        products.append({
            "site": SITE,
            "name": name,
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
