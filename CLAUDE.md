# CLAUDE.md

Bu depo iki bağımsız sistem içeriyor. Detaylı geçmiş için `docs/yapilanlar.md`
(baştan sona anlatım), `docs/sorunlar-ve-cozumler.md` (karşılaşılan engeller ve
çözümleri), `docs/ogrenilenler.md` (terim/kavram sözlüğü), `docs/dosya-yapisi.md`
(dosya haritası) - bu dosya sadece hızlı bağlam kazanmak için özet.

## Sistem 1: SSD/Harici Disk Fiyat Takibi (`core/`, tam otomatik)

**Ne yapıyor:** 6 Türkiye e-ticaret sitesini (Amazon.com.tr, Trendyol,
incehesap, itopya, n11, Pazarama) GitHub Actions ile her 10 dakikada bir
tarar, bir ürün son 45 günün medyanına göre gerçekten (%25+) ucuzladıysa
veya sabit bir hedef fiyata düştüyse e-posta + Telegram + WhatsApp ile
bildirim gönderir.

**Giriş noktası:** `core/check_and_notify.py` - GitHub Actions
(`.github/workflows/price-check.yml`) bunu çalıştırır.

**Akış:** `core/scrapers/*.py` (tara) → filtrele (kapasite doğru mu, aksesuar
mı, hariç tutulmuş mu - `core/excluded_products.py`) → `core/storage.py`'den
geçmişi oku → `core/discount_detector.py` ile medyan/hedef fiyat karşılaştır
→ gerçekse `core/notifier.py` ile bildir → `core/storage.py`'ye bugünün
fiyatını kaydet.

**Kategoriler:** `1tb` (NVMe şart, 6500 TL hedef), `2tb` (NVMe şart, 12000 TL
hedef), `2tb-harici` (taşınabilir SSD, 5000 TL hedef). Hepsiburada CAPTCHA
duvarına takıldığı için kapsam dışı (`core/scrapers/hepsiburada.py` referans
olarak duruyor, kullanılmıyor).

**Önemli kurallar:**
- Site engelleriyle karşılaşınca (CAPTCHA, bot koruması) ASLA bypass/aşma
  yöntemi denenmedi - o site listeden çıkarıldı. Bu prensip korunmalı.
- Fiyat için MEDYAN kullanılıyor, ORTALAMA değil (yapay zam-sahte indirim
  numarasına karşı dayanıklı olsun diye).
- Yanlış eşleşmeleri önlemek için sürekli yeni filtreler eklendi
  (`matches_capacity`, `is_accessory`, `is_external`, `is_nvme`, `is_ssd` -
  hepsi `core/scrapers/_price.py`'de). Yeni bir yanlış eşleşme fark edilirse
  aynı dosyaya benzer bir filtre eklenmeli.
- Hatalı/yanıltıcı tek bir ürün fark edilirse `core/excluded_products.py`'ye
  URL'sini ekle - kod değiştirmeye gerek yok.
- Hassas bilgiler (SMTP şifresi, API key'ler) hiçbir zaman koda yazılmaz -
  GitHub Secrets kullanılır, yerelde test için `.env` (git'e girmez).
- Repo **public** - GitHub Actions'ın ücretsiz dakika kotası private
  repolarda sınırlı, 10 dakikalık bir cron için yetmiyordu.

## Sistem 2: Laptop Fiyat Karşılaştırma Botu (`laptop-arama/`, isteğe bağlı)

**Ne yapıyor:** RTX 5070 Ti/5080/5090 (12GB+ VRAM) laptopların Türkiye
(Amazon.com.tr + n11) ve Avrupa (PriceRunner UK, 3 kategori) fiyatlarını
karşılaştırır - ama Sistem 1 gibi sürekli değil, sadece Telegram'dan
sorulduğunda (webhook ile anlık tetiklenir).

**Neden ayrı klasör:** Kullanıcı isteği - iki sistem birbirinden bağımsız
olsun, biri kapatılırsa/silinirse diğeri etkilenmesin.

**Mimari:** Telegram → webhook (anlık, POST isteği) → `laptop-arama/
webhook_app.py` (Flask, Render.com'da 7/24 çalışıyor) → arka planda
`search_laptops_tr.py` + `search_laptops.py` çalışır → `matcher.py` ile
eşleştirilir → `currency.py` ile güncel kur çekilir → `manis.py`'den
rastgele bir mani eklenir → sonuç Telegram'a gönderilir.

**Neden webhook, polling değil:** İlk kurulan sistem GitHub Actions ile
5 dakikada bir "yeni mesaj var mı" diye soruyordu (polling) - ama GitHub'ın
kendi zamanlayıcısı bu sıklıkta güvenilir çalışmadı (bazen saatlerce hiç
tetiklenmedi). Kullanıcı "anlık" cevap istediği için webhook mimarisine
geçildi - bunun için 7/24 açık bir sunucu (Render.com, ücretsiz katman)
gerekiyor. **Telegram bir bota aynı anda hem webhook hem polling
kullandırmıyor** - biri seçilince diğeri tamamen kapatılmalı.

**Deploy detayı:** Render'ın ücretsiz build ortamı `playwright install
--with-deps` için root yetkisi vermiyor (`su: Authentication failure`
hatası). Çözüm: `laptop-arama/Dockerfile`, Playwright'ın resmi Docker
imajını (`mcr.microsoft.com/playwright/python`) kullanıyor - Chromium'un
ihtiyaç duyduğu sistem kütüphaneleri zaten kurulu geliyor. Render'da
Environment/Language **Docker** olarak seçilmeli (Render dashboard'u
mevcut bir servisin runtime'ını sonradan değiştirmeyi desteklemiyor -
yanlış seçilirse servisi silip yeniden oluşturmak gerekiyor).

**Eşleştirme mantığı (`matcher.py`):** Marka + bilinen ürün serisi adı
(Stealth/Vector/Legion/ROG Strix vb.) aynıysa eşleşme kabul edilir; model
kodu da (örn. "A2XWHG") örtüşüyorsa "kesin", örtüşmüyorsa "yaklaşık" olarak
etiketlenir. Sadece model koduna güvenmek YANLIŞ eşleşmeler üretmişti
(farklı seri, tesadüfen aynı kod parçası) - bu yüzden marka+seri şartı
eklendi.

**Bilinen sınırlamalar:**
- Amazon.com.tr ve n11 arama sonuçları istekten isteğe değişkenlik
  gösterebiliyor (reklam/sıralama rotasyonu) - bazen eşleşme çıkar, bazen
  çıkmaz, bu normal.
- Render'ın ücretsiz katmanı 15 dakika hareketsizlikten sonra uykuya geçiyor
  - ilk mesajda ~30-50 saniyelik "uyanma" gecikmesi olabilir.
- Render'ın ücretsiz RAM'i (512MB) sınırda - Chromium için tam yeterli
  olmayabilir, sorun çıkarsa ilk bakılacak yer burası.

## Genel kod kuralları (her iki sistem için)

- Kod içi yorumlar **Türkçe**, değişken/fonksiyon isimleri **İngilizce**.
- Değişiklik yaptıktan sonra gerçek veriyle test et (mock değil) - hem yerelde
  hem mümkünse gerçek ortamda (GitHub Actions / Render) doğrula.
- Basitlik önce: gereksiz soyutlama, kullanılmayan esneklik ekleme. Ölü kod
  fark edilirse (örn. `collect_prices.py` silindiği gibi) kaldır.
- Git commit'lerinde Türkçe/İngilizce karışık mesaj kullanılıyor, sorun değil.
- `data/price_history.db` her GitHub Actions çalıştırmasında otomatik commit
  leniyor - yerelde çalışırken `git pull` yapmadan push etmeye çalışırsan
  çakışma alırsın, önce pull et.
