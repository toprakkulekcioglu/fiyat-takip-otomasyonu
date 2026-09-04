"""Bir ürün linkinin hangi siteye ait olduğunu bulup doğru scraper modülünü döner.
Kullanıcı takibe almak istediği bir link verdiğinde (subscription_api.py) hangi
`scrape_product(url)` fonksiyonunun çağrılacağını belirlemek için kullanılıyor.
"""
from types import ModuleType
from urllib.parse import urlparse

from scrapers import amazon, incehesap, itopya, n11, pazarama, trendyol

_HOST_TO_MODULE: dict[str, ModuleType] = {
    "amazon.com.tr": amazon,
    "www.amazon.com.tr": amazon,
    "trendyol.com": trendyol,
    "www.trendyol.com": trendyol,
    "n11.com": n11,
    "www.n11.com": n11,
    "itopya.com": itopya,
    "www.itopya.com": itopya,
    "incehesap.com": incehesap,
    "www.incehesap.com": incehesap,
    "pazarama.com": pazarama,
    "www.pazarama.com": pazarama,
}


def find_scraper(url: str) -> ModuleType | None:
    """Linkin host'una göre destekleyen scraper modülünü döner, desteklenmiyorsa None."""
    host = urlparse(url).netloc.lower()
    return _HOST_TO_MODULE.get(host)
