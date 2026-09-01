"""Güncel GBP -> TRY kurunu çeker (Frankfurter API - ücretsiz, key gerektirmiyor,
Avrupa Merkez Bankası verisine dayanıyor)."""
import requests

FX_URL = "https://api.frankfurter.app/latest"


def gbp_to_try_rate() -> float:
    response = requests.get(FX_URL, params={"from": "GBP", "to": "TRY"}, timeout=15, allow_redirects=True)
    response.raise_for_status()
    return response.json()["rates"]["TRY"]
