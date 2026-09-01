"""Avrupa'daki (PriceRunner UK üzerinden - çok mağazalı fiyat karşılaştırması)
RTX 5070 Ti laptop fiyatlarını ANLIK olarak çeker. Otomasyonun (core/) parçası
DEĞİL - zamanlanmış çalışmıyor, sadece elle çalıştırıldığında güncel veri getirir.

Not: PriceRunner sadece fiyat + mağaza sayısı veriyor; "incelik" ve "DCI-P3/Adobe
RGB %90+ ekran" gibi spec'ler burada listelenmiyor (fiyat karşılaştırma sitelerinde
bu detay olmuyor, üretici sayfası/inceleme sitesi gerekir). Bu script sadece fiyat
tarafını otomatikleştiriyor - spec uygunluğu sonuçlara bakılırken ayrıca
değerlendirilmeli.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from bs4 import BeautifulSoup

from scrapers._browser import fetch_rendered_html

CATEGORY_URL = "https://www.pricerunner.com/sp/laptop-5070-ti.html"

PRICE_PATTERN = re.compile(r"£([\d,]+\.\d{2}|[\d,]+)")
STORES_PATTERN = re.compile(r"(\d+\+?)\s*stores?")


def _find_card(anchor):
    """Fiyat/mağaza bilgisini içeren en dar ata elementi bulur (ürün kartının kendisi)."""
    node = anchor
    for _ in range(8):
        if node.parent is None:
            break
        node = node.parent
        text = node.get_text(" ", strip=True)
        if "£" in text and "store" in text.lower():
            return node
    return None


def search() -> list[dict]:
    html = fetch_rendered_html(CATEGORY_URL, wait_selector='a[href*="/pl/"]', timeout_ms=25000)
    soup = BeautifulSoup(html, "html.parser")

    results = []
    seen_urls = set()
    for anchor in soup.select('a[href*="/pl/"]'):
        href = anchor.get("href")
        name = anchor.get("title") or anchor.get("aria-label")
        if not href or not name or href in seen_urls:
            continue

        card = _find_card(anchor)
        if card is None:
            continue
        card_text = card.get_text(" ", strip=True)

        price_match = PRICE_PATTERN.search(card_text)
        if not price_match:
            continue
        price = float(price_match.group(1).replace(",", ""))

        stores_match = STORES_PATTERN.search(card_text)
        stores = stores_match.group(0) if stores_match else "?"

        seen_urls.add(href)
        results.append({
            "name": name,
            "price_gbp": price,
            "stores": stores,
            "url": "https://www.pricerunner.com" + href,
        })

    results.sort(key=lambda r: r["price_gbp"])
    return results


if __name__ == "__main__":
    laptops = search()
    print(f"{len(laptops)} sonuç bulundu (PriceRunner UK, RTX 5070 Ti laptoplar, fiyata göre sıralı)\n")
    for laptop in laptops:
        print(f"£{laptop['price_gbp']:>9,.2f}  ({laptop['stores']:>10})  {laptop['name']}")
        print(f"           {laptop['url']}")
