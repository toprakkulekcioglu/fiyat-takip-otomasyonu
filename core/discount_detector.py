"""Sahte indirim tespiti: güncel fiyatı, geçmiş medyan fiyatla karşılaştırır.

Neden medyan, ortalama değil: bir satıcı "indirimden" hemen önce fiyatı yapay
olarak yükseltirse (örn. birkaç gün için), bu birkaç günlük yapay zam ORTALAMAYI
belirgin şekilde yukarı çeker - ama medyanı çok daha az etkiler, çünkü medyan
"ortadaki değer"dir, uç noktalardan (bu durumda kısa süreli yapay zam) etkilenmez.
Geçmişin çoğunluğu normal fiyat seviyesindeyse, medyan de o seviyede kalır.

Sınır (limitasyon): yapay zam, bakılan pencerenin (30-60 gün) BÜYÜK BİR KISMINI
kaplayacak kadar uzun sürdürülürse medyan de yukarı kayar ve bu tespit yöntemi
bunu yakalayamaz. Bu, medyan tabanlı her yaklaşımın doğal sınırıdır (AB'nin
Omnibus Direktifi'nin "son 30 günün en düşük fiyatı" kuralı da aynı sınıra sahip).
"""
import statistics
from dataclasses import dataclass


@dataclass
class DiscountCheck:
    is_genuine_discount: bool
    current_price: float
    reference_median: float
    discount_pct: float  # medyana göre gerçek indirim yüzdesi (pozitif = ucuzlama)
    reason: str


def check_discount(
    history_prices: list[float],
    current_price: float,
    threshold: float = 0.25,
    min_data_points: int = 5,
    price_ceiling: float | None = None,
) -> DiscountCheck:
    """history_prices: son 30-60 günlük geçmiş fiyatlar (current_price HARİÇ).
    threshold: 0.25 = medyanın en az %25 altına inmeli.
    min_data_points: yeterli geçmiş yoksa (yeni eklenen ürün gibi) tetiklenmez.
    price_ceiling: verilirse, güncel fiyat bu değerin altına düştüğünde - geçmiş
        yetersiz olsa bile - medyan şartı aranmadan direkt tetiklenir (hedef fiyat
        alarmı). Medyan şartı hâlâ ayrıca çalışır, ikisinden biri yeterlidir.
    """
    if price_ceiling is not None and current_price <= price_ceiling:
        reference_median = statistics.median(history_prices) if history_prices else current_price
        return DiscountCheck(
            is_genuine_discount=True,
            current_price=current_price,
            reference_median=reference_median,
            discount_pct=(reference_median - current_price) / reference_median if reference_median else 0.0,
            reason=f"Hedef fiyata ulaşıldı: {current_price:.2f} TL (eşik: {price_ceiling:.2f} TL)",
        )

    if len(history_prices) < min_data_points:
        return DiscountCheck(
            is_genuine_discount=False,
            current_price=current_price,
            reference_median=0.0,
            discount_pct=0.0,
            reason=f"Yetersiz geçmiş ({len(history_prices)}/{min_data_points} kayıt) - karşılaştırma yapılamadı",
        )

    reference_median = statistics.median(history_prices)
    discount_pct = (reference_median - current_price) / reference_median

    if discount_pct >= threshold:
        reason = (
            f"Gerçek indirim: {reference_median:.2f} TL medyana göre "
            f"%{discount_pct * 100:.1f} ucuz"
        )
        is_genuine = True
    else:
        reason = (
            f"İndirim eşiği aşılmadı: medyan {reference_median:.2f} TL, "
            f"güncel fiyat sadece %{discount_pct * 100:.1f} altında "
            f"(eşik: %{threshold * 100:.0f})"
        )
        is_genuine = False

    return DiscountCheck(
        is_genuine_discount=is_genuine,
        current_price=current_price,
        reference_median=reference_median,
        discount_pct=discount_pct,
        reason=reason,
    )


if __name__ == "__main__":
    import random

    random.seed(42)

    print("=== Senaryo A: Gerçek düşüş ===")
    print("45 günlük geçmiş boyunca fiyat ~8000 TL civarında dalgalanıyor, sonra")
    print("gerçekten 5800 TL'ye düşüyor (yapay zam yok).\n")
    history_a = [8000 + random.uniform(-150, 150) for _ in range(45)]
    result_a = check_discount(history_a, current_price=5800.0)
    print(f"  Medyan: {result_a.reference_median:.2f} TL")
    print(f"  Güncel fiyat: {result_a.current_price:.2f} TL")
    print(f"  Gerçek indirim mi? {result_a.is_genuine_discount}")
    print(f"  Sebep: {result_a.reason}")

    print("\n=== Senaryo B: Önce yapay zam, sonra sahte indirim ===")
    print("45 günün 40'ında fiyat ~8000 TL, son 5 gününde satıcı fiyatı 10800 TL'ye")
    print("yükseltiyor, sonra '%23 indirim' diyerek 8300 TL'ye 'düşürüyor'")
    print("(8300 TL, 10800'e göre gerçekten %23 ucuz görünüyor ama 8000 TL'lik")
    print("gerçek normal fiyatın hâlâ ÜSTÜNDE).\n")
    history_b = [8000 + random.uniform(-150, 150) for _ in range(40)]
    history_b += [10800 + random.uniform(-100, 100) for _ in range(5)]
    fake_discount_price = 8300.0
    naive_pct_vs_yesterday = (history_b[-1] - fake_discount_price) / history_b[-1]
    result_b = check_discount(history_b, current_price=fake_discount_price)
    print(f"  Dünkü fiyata göre görünen indirim: %{naive_pct_vs_yesterday * 100:.1f} (yanıltıcı)")
    print(f"  45 günlük medyan: {result_b.reference_median:.2f} TL")
    print(f"  Güncel fiyat: {result_b.current_price:.2f} TL")
    print(f"  Gerçek indirim mi? {result_b.is_genuine_discount}")
    print(f"  Sebep: {result_b.reason}")
