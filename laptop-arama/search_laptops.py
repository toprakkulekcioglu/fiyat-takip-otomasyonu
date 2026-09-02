"""Avrupa'daki (PriceRunner UK üzerinden - çok mağazalı fiyat karşılaştırması)
12GB+ VRAM'li RTX 50 serisi laptop fiyatlarını (5070 Ti, 5080, 5090) ANLIK olarak
çeker. Otomasyonun (core/) parçası DEĞİL - zamanlanmış çalışmıyor, sadece elle/bot
tetiklemesiyle güncel veri getirir.

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

from scrapers._browser import fetch_multiple_rendered_html

# 12GB+ VRAM'li RTX 50 serisi mobil GPU'lar: 5070 Ti (12GB), 5080 (16GB), 5090 (24GB).
# Taban 5070 (8GB) ve altı dahil değil.
CATEGORY_URLS = [
    "https://www.pricerunner.com/sp/laptop-5070-ti.html",
    "https://www.pricerunner.com/sp/rtx-5080-laptop.html",
    "https://www.pricerunner.com/sp/5090-laptop.html",
]

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


def _parse_category(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    results = []
    for anchor in soup.select('a[href*="/pl/"]'):
        href = anchor.get("href")
        name = anchor.get("title") or anchor.get("aria-label")
        if not href or not name:
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

        results.append({
            "name": name,
            "price_gbp": price,
            "stores": stores,
            "url": "https://www.pricerunner.com" + href,
        })
    return results


def search() -> list[dict]:
    # 3 kategori için ayrı ayrı tarayıcı açıp kapatmak yerine tek bir Chromium
    # örneğiyle sırayla çekiyoruz - düşük bellekli sunucularda (Render) daha
    # güvenilir çalışıyor.
    requests_list = [(url, 'a[href*="/pl/"]') for url in CATEGORY_URLS]
    htmls = fetch_multiple_rendered_html(requests_list, timeout_ms=45000)

    seen_urls = set()
    results = []
    for category_url, html in zip(CATEGORY_URLS, htmls):
        if isinstance(html, Exception):
            print(f"  {category_url}: HATA - {html}", flush=True)
            continue
        found = _parse_category(html)
        print(f"  {category_url}: {len(found)} urun", flush=True)
        for laptop in found:
            if laptop["url"] in seen_urls:
                continue
            seen_urls.add(laptop["url"])
            results.append(laptop)

    results.sort(key=lambda r: r["price_gbp"])
    return results


if __name__ == "__main__":
    laptops = search()
    print(f"{len(laptops)} sonuç bulundu (PriceRunner UK, 12GB+ RTX 50 serisi laptoplar, fiyata göre sıralı)\n")
    for laptop in laptops:
        print(f"£{laptop['price_gbp']:>9,.2f}  ({laptop['stores']:>10})  {laptop['name']}")
        print(f"           {laptop['url']}")
