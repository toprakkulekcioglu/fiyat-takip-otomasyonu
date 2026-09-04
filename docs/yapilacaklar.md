# Yapılacaklar / Değerlendirilen Fikirler

Bu dosya, henüz **karara bağlanmamış veya başlanmamış** fikirleri tutar - yapılmış
işler için `yapilanlar.md`'ye bak. Buradaki maddeler ileride "hadi bunu yapalım"
denirse doğrudan bu plandan devam edilebilsin diye yazıldı.

## Kullanıcı bazlı, link ile ürün takibi

**Durum: Yapıldı** (`web/ssd-takip.html` + `core/subscription_api.py` vb.) -
detaylar için `yapilanlar.md` → "Sistem 1 Genişletmesi" bölümüne bak.

**Hâlâ eksik/opsiyonel olan tek şey - Telegram komut arayüzü:** Şu an takibe
alma/çıkarma SADECE web sayfası üzerinden yapılabiliyor. İlk planda "Telegram'a
link at, bot cevap versin" seçeneği de konuşulmuştu ama kapsamı dar tutmak için
yapılmadı. İstenirse `laptop-arama/webhook_app.py`'deki `telegram-webhook`
route'una benzer bir mantıkla, mevcut SSD Telegram botuna (`TELEGRAM_BOT_TOKEN`)
webhook bağlanıp link mesajlarını `core/site_router.py` + `scrape_product` +
`core/subscriptions_store.py` üzerinden işleyecek bir uç eklenebilir - backend
(`site_router`, `scrape_product`, `subscriptions_store`, `git_sync`) zaten hazır,
sadece yeni bir Telegram-özel giriş noktası yazılması yeterli.

## Dışarıdan gereken tek şey (hâlâ senin yapman gereken bir adım)

Render'daki servisin yeni abonelikleri git'e geri yazabilmesi için bir GitHub
Personal Access Token lazım (`core/git_sync.py`, `GITHUB_PAT` ortam değişkeni).
Bu token oluşturulup Render'a eklenmeden web sayfası ÇALIŞIR ama eklenen
ürünler GitHub Actions'ın periyodik taramasına yansımaz (bildirim gitmez,
fiyat güncellenmez) - token eklenene kadar özellik "yarım" kalır. Tam adımlar
için konuşma geçmişindeki mesaja bak (Ayarlar → Developer settings → Personal
access tokens, "Contents: Read and write" izniyle, sadece bu repo için).
