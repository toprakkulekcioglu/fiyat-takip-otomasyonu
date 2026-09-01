"""Türk Lirası fiyat metinlerini (örn. '16.396,49 TL', '8.399 TL') float'a çevirir."""
import re

# 1TB/2TB SSD'lerin gerçekçi olarak bu fiyatın altına inmeyeceği varsayımıyla, kategori/arama
# sayfalarına sızan alakasız ürünleri (aksesuar, disk kutusu vb.) elemek için kullanılıyor.
MIN_PLAUSIBLE_PRICE = 2000.0


def parse_try(text: str) -> float | None:
    if not text:
        return None
    match = re.search(r"[\d.,]+", text)
    if not match:
        return None
    number = match.group(0).strip(".,")
    if "," in number:
        number = number.replace(".", "").replace(",", ".")
    else:
        number = number.replace(".", "")
    try:
        return float(number)
    except ValueError:
        return None
