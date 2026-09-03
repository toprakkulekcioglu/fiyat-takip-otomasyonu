"""Güncel döviz kurlarını çeker (Frankfurter API - ücretsiz, key gerektirmiyor,
Avrupa Merkez Bankası verisine dayanıyor)."""
import requests

FX_URL = "https://api.frankfurter.app/latest"


def _rate(from_currency: str, to_currency: str) -> float:
    response = requests.get(
        FX_URL, params={"from": from_currency, "to": to_currency}, timeout=15, allow_redirects=True
    )
    response.raise_for_status()
    return response.json()["rates"][to_currency]


def gbp_to_try_rate() -> float:
    return _rate("GBP", "TRY")


def eur_to_try_rate() -> float:
    return _rate("EUR", "TRY")
