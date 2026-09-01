"""Türkiye ve yurtdışı (İngiltere/PriceRunner) laptop listelerini aynı fiziksel
modele göre eşleştirir.

Yöntem: üreticiler aynı laptop modelini farklı ülkelerde genelde aynı temel model
kodu ile satar (örn. "A2XWHG-082TR" / "A2XWHG-403UK" - sadece ülke soneki farklı).
Ama bu kod tek başına GÜVENİLİR DEĞİL - testte "MSI Stealth 18" ile "MSI Vector 16"
(iki farklı ürün serisi, farklı ekran boyutu) sırf kod parçası çakıştığı için
yanlışlıkla eşleşti. Bu yüzden EK olarak ürün serisi adının da (Stealth/Vector/
Raider gibi) her iki isimde aynı olması şart koşuluyor - marka + model kodu +
seri adı üçü birden tutmayınca eşleşme kabul edilmiyor.

Bu yine de tahmin bazlı bir eşleştirme - garanti değil, sonuçlar gösterilirken
bunun otomatik/yaklaşık bir eşleştirme olduğu belirtilmeli.
"""
import re

_CODE_PATTERN = re.compile(r"\b(?=[A-Z0-9]{5,}\b)(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*[0-9])[A-Z0-9]{5,}\b")

# Bilinen oyun/iş istasyonu laptop serisi isimleri - marka+kod eşleşse bile seri
# adı da eşleşmezse muhtemelen farklı bir üründür.
_KNOWN_SERIES = (
    "stealth", "vector", "raider", "titan", "katana", "sword", "cyborg",  # MSI
    "strix", "zephyrus", "tuf", "scar", "flow",  # ASUS
    "legion", "loq",  # Lenovo
    "omen", "victus",  # HP
    "nitro", "predator", "helios", "triton",  # Acer
    "blade",  # Razer
    "alienware",  # Dell
)


def _brand(name: str) -> str:
    return name.strip().split()[0].lower() if name.strip() else ""


def _series(name: str) -> str | None:
    lowered = name.lower()
    for series in _KNOWN_SERIES:
        if series in lowered:
            return series
    return None


def _model_codes(name: str) -> set[str]:
    upper = name.upper()
    codes = set()
    for match in _CODE_PATTERN.finditer(upper):
        code = match.group(0)
        # "RTX5070TI" gibi GPU adını model kodu sanmamak için filtrele.
        if "5070" in code or "RTX" in code:
            continue
        codes.add(code)
    return codes


def match(tr_laptops: list[dict], global_laptops: list[dict]) -> list[dict]:
    """Her eşleşen çift için {'tr': ..., 'global': ...} döner."""
    pairs = []
    used_global = set()

    for tr in tr_laptops:
        tr_brand = _brand(tr["name"])
        tr_series = _series(tr["name"])
        tr_codes = _model_codes(tr["name"])
        if not tr_codes or not tr_series:
            continue

        for idx, glb in enumerate(global_laptops):
            if idx in used_global:
                continue
            if _brand(glb["name"]) != tr_brand or _series(glb["name"]) != tr_series:
                continue
            glb_codes = _model_codes(glb["name"])
            if not glb_codes:
                continue

            # Kodlardan biri diğerinin öneki ise (bölge soneki farkı) eşleşme kabul edilir.
            if any(
                a == b or a.startswith(b) or b.startswith(a)
                for a in tr_codes for b in glb_codes
                if len(a) >= 5 and len(b) >= 5
            ):
                pairs.append({"tr": tr, "global": glb})
                used_global.add(idx)
                break

    return pairs
