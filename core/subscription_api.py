"""Web sayfasının (web/ssd-takip.html) kullandığı REST API.

Kullanıcı bir ürün linki verip takibe alabiliyor, takip listesini görebiliyor,
bir ürünü listeden çıkarabiliyor. Flask Blueprint olarak yazıldı ki
laptop-arama/webhook_app.py'nin zaten 7/24 açık olan Render servisine route
olarak eklenebilsin - bunun için ayrı bir servis açmaya gerek kalmıyor.

Fiyat gösterimi (`GET /api/subscriptions`) her seferinde YENİDEN TARAMA
yapmıyor, en son bilinen fiyatı `price_history`'den okuyor - canlı tarama
Playwright yüzünden saniyeler sürebiliyor, sayfa her açıldığında bunu
bekletmek istemedik. Güncel fiyat, `check_and_notify.py`'nin periyodik
taramasıyla (Adım: check_and_notify.py'ye eklenen abonelik kontrolü) tazeleniyor.
"""
from flask import Blueprint, jsonify, request

import git_sync
from site_router import find_scraper
from storage import get_latest_price
from subscriptions_store import DEFAULT_PATH, add_subscription, deactivate_subscription, get_active_subscriptions

subscription_api = Blueprint("subscription_api", __name__)

UNSUPPORTED_SITE_MESSAGE = (
    "Bu siteyi desteklemiyorum. Şu an sadece Amazon.com.tr, Trendyol, n11.com, "
    "itopya.com, incehesap.com ve Pazarama ürün linkleri çalışıyor."
)


def _cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    return response


@subscription_api.route("/api/track", methods=["POST", "OPTIONS"])
def track():
    if request.method == "OPTIONS":
        return _cors(jsonify({}))

    body = request.get_json(silent=True) or {}
    url = (body.get("url") or "").strip()
    if not url:
        return _cors(jsonify({"error": "Link boş olamaz."})), 400

    scraper = find_scraper(url)
    if scraper is None:
        return _cors(jsonify({"error": UNSUPPORTED_SITE_MESSAGE})), 400

    try:
        result = scraper.scrape_product(url)
    except Exception as e:
        print(f"[subscription_api] TARAMA HATASI ({scraper.SITE}): {type(e).__name__}: {e}", flush=True)
        return _cors(jsonify({
            "error": "Ürün sayfası taranırken bir hata oldu, birkaç saniye sonra tekrar dener misin?"
        })), 502

    if result is None:
        return _cors(jsonify({
            "error": "Bu sayfadan ürün adı/fiyatı okunamadı - link doğrudan bir ürün sayfasına mı gidiyor?"
        })), 502

    subscription_id = add_subscription(site=scraper.SITE, url=url, name=result["name"])
    git_sync.push_file(
        DEFAULT_PATH, "data/subscriptions.json",
        f"Yeni takip: {result['name'][:60]}",
    )

    return _cors(jsonify({
        "id": subscription_id,
        "name": result["name"],
        "price": result["price"],
        "site": scraper.SITE,
        "url": url,
    }))


@subscription_api.route("/api/subscriptions", methods=["GET"])
def list_subscriptions():
    items = []
    for sub in get_active_subscriptions():
        items.append({
            "id": sub["id"],
            "name": sub["name"],
            "price": get_latest_price(sub["site"], sub["url"]),
            "site": sub["site"],
            "url": sub["url"],
            "added_at": sub["added_at"],
        })
    return _cors(jsonify(items))


@subscription_api.route("/api/subscriptions/<int:subscription_id>", methods=["DELETE", "OPTIONS"])
def remove_subscription(subscription_id: int):
    if request.method == "OPTIONS":
        return _cors(jsonify({}))
    ok = deactivate_subscription(subscription_id)
    if ok:
        git_sync.push_file(
            DEFAULT_PATH, "data/subscriptions.json",
            f"Takip bırakıldı: id={subscription_id}",
        )
    return _cors(jsonify({"ok": ok}))
