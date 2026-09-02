"""Hatalı/yanıltıcı olduğu tespit edilip elle listeden çıkarılan ürünler.

Buraya bir ürün eklemek için: URL'yi EXCLUDED_URLS'e ekle, kısa bir sebep yaz.
check_and_notify.py bu listedeki URL'lere sahip ürünleri tarama sonuçlarından
otomatik olarak eliyor - bir daha bildirime/geçmişe girmiyorlar.
"""

EXCLUDED_URLS = {
    # Başlıkta hem "500gb" hem "1 tb" birlikte geçiyor - yanıltıcı/hatalı girilmiş
    # bir liste sayfası, iki farklı gün yanlış "indirim" bildirimine sebep oldu.
    "https://www.n11.com/urun/msi-ssd-spatium-m452-pcie-40-nvme-m2-500gb-1-tb-136150844",
}
