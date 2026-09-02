"""Türkiye'de satılan, 12GB+ VRAM'li RTX 50 serisi laptopları (5070 Ti, 5080,
5090) Amazon.com.tr + n11.com üzerinden anlık çeker. Diğer laptop-arama
script'leri gibi otomasyonun (core/) parçası değil, sadece elle/bot
tetiklemesiyle çalışır.

İki kaynak kullanılıyor çünkü tek bir sitenin arama sonuçları istekten isteğe
değişkenlik gösterebiliyor (reklam/sıralama rotasyonu) - bu da yurtdışı
kataloğuyla örtüşme ihtimalini gereksiz yere düşürüyor. İkisi de TEK bir
Chromium örneğiyle çekiliyor (düşük bellekli sunucularda daha güvenilir).
"""
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from scrapers._browser import fetch_multiple_rendered_html
from scrapers._price import parse_try

AMAZON_URL = "https://www.amazon.com.tr/s?k=rtx+5070+ti+5080+5090+laptop"
N11_URL = "https://www.n11.com/bilgisayar/dizustu-bilgisayar?q=rtx+5070+ti+5080+5090"
N11_BASE = "https://www.n11.com"

# Taban 5070 (8GB) hariç: "5070 ti" ya da düz "5080"/"5090" (bunlar zaten 12GB+).
_GPU_PATTERN = re.compile(r"5070\s?ti|5080|5090", re.IGNORECASE)
# Arama, masaüstü ekran kartlarını da (laptop değil) döndürebiliyor - bunları eleriz.
_LAPTOP_INDICATOR = re.compile(r"dizüstü|laptop|notebook", re.IGNORECASE)
_DESKTOP_CARD_INDICATOR = re.compile(r"ekran kart[ıi]|\bvga\b", re.IGNORECASE)


def _is_laptop(name: str) -> bool:
    return bool(_LAPTOP_INDICATOR.search(name)) and not _DESKTOP_CARD_INDICATOR.search(name)


def _parse_amazon(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for card in soup.select('div[data-component-type="s-search-result"]'):
        asin = card.get("data-asin")
        name_el = card.select_one("h2 span")
        price_el = card.select_one(".a-price .a-offscreen")
        if not asin or not name_el or not price_el:
            continue
        name = name_el.get_text(strip=True)
        if not _GPU_PATTERN.search(name) or not _is_laptop(name):
            continue
        price = parse_try(price_el.get_text())
        if price is None:
            continue
        results.append({"name": name, "price_try": price, "url": f"https://www.amazon.com.tr/dp/{asin}"})
    return results


def _parse_n11(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for card in soup.select("a.product-item[href]"):
        name_el = card.select_one("h2.product-item-title")
        price_el = card.select_one("h3.price-currency")
        if not name_el or not price_el:
            continue
        name = name_el.get_text(strip=True)
        if not _GPU_PATTERN.search(name) or not _is_laptop(name):
            continue
        price = parse_try(price_el.get_text())
        if price is None:
            continue
        results.append({"name": name, "price_try": price, "url": urljoin(N11_BASE, card.get("href"))})
    return results


def search() -> list[dict]:
    requests_list = [
        (AMAZON_URL, 'div[data-component-type="s-search-result"]'),
        (N11_URL, "a.product-item[href]"),
    ]
    htmls = fetch_multiple_rendered_html(requests_list, timeout_ms=45000)

    results = []
    for (url, _), html, parser, name in zip(
        requests_list, htmls, (_parse_amazon, _parse_n11), ("amazon", "n11")
    ):
        if isinstance(html, Exception):
            print(f"  {name}: HATA - {html}", flush=True)
            continue
        found = parser(html)
        print(f"  {name}: {len(found)} urun", flush=True)
        results.extend(found)

    results.sort(key=lambda r: r["price_try"])
    return results


if __name__ == "__main__":
    for laptop in search():
        print(f"{laptop['price_try']:>10,.2f} TL  {laptop['name'][:80]}")
        print(f"           {laptop['url']}")
