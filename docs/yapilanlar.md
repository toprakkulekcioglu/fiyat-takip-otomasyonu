# Yapılanlar — Baştan Sona Ne İnşa Ettik

Bu proje boyunca iki ayrı sistem kurduk. Bu dosya, ikisini de baştan sona,
neden/nasıl yapıldığını açıklayarak anlatıyor.

---

## Sistem 1: SSD / Harici Disk Fiyat Takip Botu (otomatik)

**Amaç:** Türkiye'deki e-ticaret sitelerinden SSD fiyatlarını sürekli izleyip,
bir ürün gerçekten ucuzladığında (satıcının "önce zam yap, sonra indirim
göster" numarasına kanmadan) otomatik haber vermek.

### 1. Hangi siteler taranacak (kapsam belirleme)

Başta hedef Amazon, Hepsiburada, Trendyol'du. Her sitenin **robots.txt**
dosyasına baktık (bir sitenin "buraları tarayabilirsin, buraları tarama" diye
yayınladığı kurallar dosyası) ve şunları bulduk:

- **Trendyol**: arama sayfası (`/sr?q=...`) tamamen yasaktı → çözüm: arama
  yerine sitenin kendi sabit kategori sayfalarını (`/1tb-ssd-y-s3288` gibi)
  kullandık.
- **Hepsiburada**: bir bot koruma sistemi (Akamai) var, otomatik/tekrarlı
  isteklerde CAPTCHA (resim doğrulama) sayfasına yönlendiriyordu. CAPTCHA
  çözmeyi/aşmayı reddettik (güvenlik kuralı), bu siteyi **tamamen kapsam
  dışı bıraktık**.
- Bunun yerine, senin önerinle **itopya.com** ve **incehesap.com** (daha
  küçük ama gerçek, güvenilir bilgisayar parçası satıcıları) eklendi.
- Hepsiburada tamamen düştüğü için **n11** ve **Pazarama** da eklendi.

Sonuçta **6 site**: Amazon.com.tr, Trendyol, incehesap, itopya, n11, Pazarama.

### 2. Scraper'lar (veri çekme kodu)

Her site için ayrı bir Python dosyası yazıldı (`core/scrapers/` klasöründe).
İki farklı teknik kullanıldı:

- **Playwright** (gerçek bir tarayıcıyı kod ile yöneten araç, ekranı
  görünmeden arka planda çalışıyor - "headless"): Amazon, Trendyol,
  incehesap, Pazarama için. Bunlar ya JavaScript ile veri yüklüyor ya da
  basit isteklere (`curl` gibi) direniyordu; gerçek bir tarayıcı gibi
  görünmek gerekiyordu.
- **Düz `requests` kütüphanesi**: itopya, n11 için - bunlar veriyi hazır
  HTML olarak gönderiyor, tarayıcıya gerek yok, daha hafif/hızlı.

Yol boyunca veri kalitesi sorunları çıktı ve düzeltildi:

- Bazı sitelerde "Son 10 Günün En Düşük Fiyatı" gibi rozet metinleri
  yanlışlıkla fiyat sanılıyordu.
- Kategori sayfalarına alakasız ürünler (bir anahtarlık, bir SSD muhafazası/
  kutusu, bir disk istasyonu) sızıyordu - bunlar "SSD" kelimesi geçtiği için
  yanlışlıkla yakalanıyordu.
- Bazen arama, yanlış kapasiteli ürünü (500GB'lık bir disk, "1TB" araması
  yapılmasına rağmen) döndürüyordu.

Bunları önlemek için ortak bir güvenlik filtresi kuruldu (`_price.py`
içinde): kapasitenin gerçekten üründe geçip geçmediğini kontrol eden, ve
disk olmayan aksesuarları eleyen fonksiyonlar.

### 3. Fiyat geçmişi deposu

Taranan her fiyat bir veritabanına kaydediliyor (`core/storage.py`,
`data/price_history.db`). **SQLite** kullanıldı (JSON değil) çünkü "son 45
günün fiyatları" gibi tarih aralığına göre sorgu yapmak SQLite'ta çok daha
hızlı ve pratik.

### 4. Sahte indirim tespiti

Bir ürünün güncel fiyatı, son 45 günün **medyan** (ortadaki değer)
fiyatıyla karşılaştırılıyor - **ortalama değil**. Neden: bir satıcı
indirimden hemen önce fiyatı yapay olarak yükseltirse, bu ortalamayı
belirgin şekilde yukarı çeker ama medyanı çok daha az etkiler. Testte
kanıtlandı: "önce zam yap sonra indirim göster" senaryosunda sistem
kanmadı, gerçek düşüşte ise doğru alarm verdi (`core/discount_detector.py`).

Sonradan iki tür ek alarm daha eklendi:
- **Sabit hedef fiyat**: 1TB SSD 6500 TL altına, 2TB 12000 TL altına, 2TB
  harici disk 5000 TL altına düşerse - medyan şartı beklemeden direkt
  bildirim gider.
- **NVMe filtresi**: sadece NVMe diskler takip ediliyor, SATA hariç.
- **2TB harici disk** diye yeni bir kategori eklendi (2.5" USB 3.x
  taşınabilir SSD'ler) - dahili SSD takibinin yanına, onu değiştirmeden.

### 5. Bildirimler

Gerçek bir indirim/hedef fiyat yakalandığında üç kanaldan bildirim
gidiyor (`core/notifier.py`):

- **E-posta (SMTP/Gmail)**: normal şifre değil, Gmail'in "Uygulama Şifresi"
  denen, sınırlı yetkili, ayrı bir şifre kullanıldı.
- **Telegram**: BotFather ile bir bot oluşturuldu, sen bota bir mesaj atarak
  "chat_id"ni (Telegram hesabının kimlik numarası) aktif hale getirdin.
- **WhatsApp (CallMeBot)**: ücretsiz bir servis - önce botları "dolu"
  çıktı, sonra yeni bir numarayla kayıt olundu, API key alındı.

Üçü de gerçek test mesajlarıyla doğrulandı.

### 6. GitHub reposu ve secrets

Proje `git` ile versiyon kontrolüne alındı, [github.com/toprakkulekcioglu/
fiyat-takip-otomasyonu](https://github.com/toprakkulekcioglu/fiyat-takip-otomasyonu)
adında bir repo açıldı (sonradan bu isme yeniden adlandırıldı, başta
ssd-fiyat-takip'ti).

Hassas bilgiler (e-posta şifresi, API key'ler) koda **hiç yazılmadı** -
bunun yerine **GitHub Secrets** kullanıldı: repo ayarlarında şifrelenmiş
olarak saklanan, sadece otomasyon çalışırken güvenli şekilde koda aktarılan
değerler.

Repo başta **private** açıldı, sonra **public** yapıldı - çünkü GitHub
Actions'ın (aşağıda anlatılıyor) ücretsiz çalışma dakikası private
repolarda ayda 2000 dakikayla sınırlı, ama public repolarda sınırsız.
Her 10 dakikada bir çalışan bir otomasyon için private kalsaydı kota çok
hızlı biterdi.

### 7. GitHub Actions ile otomasyon

`.github/workflows/price-check.yml` dosyası, GitHub'a "bu scripti her 10
dakikada bir, kendi sunucularında çalıştır" diyor (**cron** denen bir
zamanlama sistemiyle). Her çalıştırmada:

1. Geçici bir bulut bilgisayar açılıyor
2. Kod ve kütüphaneler (Playwright dahil) kuruluyor
3. `core/check_and_notify.py` çalışıyor - tüm siteleri tarar, geçmişle
   karşılaştırır, gerekirse bildirim gönderir
4. Güncellenen fiyat veritabanı otomatik olarak repoya geri "commit"leniyor
   (bir sonraki çalıştırma kaldığı yerden devam etsin diye)
5. Bilgisayar siliniyor

Bu yüzden **senin bilgisayarının açık olmasına hiç gerek yok** - her şey
GitHub'ın bulutunda, senden bağımsız dönüyor.

### 8. Repo düzenlemesi

Başta her şey kök dizinde dağınık duruyordu. Sonradan düzenlendi:

- `core/` - tüm çalışan otomasyon kodu (scraper'lar, veritabanı, bildirim,
  ana script)
- `data/` - biriken fiyat geçmişi
- `docs/` - yazılı notlar (bu dosya dahil)
- `scripts/` - manuel test/demo araçları (otomasyonun parçası değil)
- Kök dizine bir `README.md` eklendi (proje tanıtımı)
- Artık kullanılmayan `collect_prices.py` silindi (yerini `check_and_notify.py`
  aldı)

---

## Sistem 1 Genişletmesi: Kullanıcı Bazlı Ürün Takibi (`web/ssd-takip.html`)

**Amaç:** Sabit 1tb/2tb/2tb-harici kategorilerinin ÖTESİNDE, kullanıcının
istediği herhangi bir ürün linkini (desteklenen 6 siteden) yapıştırıp "bunu
benim için izle" diyebilmesi - Amazon/CamelCamelCamel'deki fiyat takip
özelliğine benzer, ama tek dosyalık, kurulum gerektirmeyen bir web sayfası
üzerinden.

### Her sitede tekil ürün sayfası okuma (`scrape_product`)

Var olan scraper'lar (`core/scrapers/*.py`) sadece KATEGORİ sayfalarını (çok
ürünlü liste kartları) okuyordu. Kullanıcının verdiği link tek bir ürünün
sayfası olduğu için her siteye `scrape_product(url)` fonksiyonu eklendi - ve
her sitenin ürün sayfası, kategori kartlarından TAMAMEN farklı bir HTML/veri
yapısı kullanıyordu, gerçek sayfalar tarayıcıyla tek tek incelenerek bulundu:

- **Amazon.com.tr**: `#productTitle` + `.a-price .a-offscreen` (kategori
  kartlarıyla aynı selector aile).
- **Trendyol**: DOM'daki fiyat metni yanıltıcı olabiliyor ("Trendyol Plus'a
  Özel sepette X TL" - ücretli üyelik gerektiren bir fiyat). Bunun yerine
  sayfaya gömülü `window["__envoy__SHARED_PROPS"]` JSON'undaki asıl satış
  fiyatı (`merchantListing.winnerVariant.price.sellingPrice`) okunuyor.
- **n11.com**: Kategori sayfası düz `requests` ile çalışıyordu ama ürün
  sayfasında fiyat Vue.js ile İSTEMCİ tarafında dolduruluyor (ham HTML'de
  `<ins></ins>` boş geliyor) - bu yüzden burada Playwright gerekiyor, kategori
  taramasından farklı.
- **itopya.com**: Fiyat `.product-price-warning-detail` içinde "Sepette X TL"
  formatında - kampanyalı ürünlerde asıl ödenecek fiyat bu.
- **incehesap.com**: Sayfaya gömülü bir Google Tag Manager
  `dataLayer.push({"event":"view_item", ...})` çağrısından okunuyor - kategori
  kartlarındaki `data-product` JSON'undan farklı ama aynı derecede güvenilir.
- **Pazarama**: Sayfaya gömülü bir Schema.org `<script type="application/
  ld+json">` (Product/Offer) bloğundan okunuyor - SEO için eklenen standart
  bir işaretleme, DOM metin ayrıştırmaya hiç gerek kalmadı.

İç içe süslü parantezli bu JSON'ları (Trendyol, incehesap) güvenilir
ayrıştırmak için `core/scrapers/_embedded_json.py` yazıldı - regex yerine
süslü parantez SAYACIYLA dengeli kapanışı buluyor (regex'in ".*?" ile "en
yakın kapanışı" bulması, iç içe objelerde yanlış yere kesebiliyordu).

### Link → site eşleştirme

`core/site_router.py` bir linkin host'una bakıp doğru `scrape_product`'a
yönlendiriyor; desteklenmeyen bir site linki gelirse kullanıcıya net bir
mesajla söyleniyor (bypass denenmiyor - proje prensibi burada da geçerli).

### Abonelikler NEDEN price_history.db'nin dışında ayrı bir dosyada

İlk planda abonelikler de `price_history.db`'ye bir tabloya eklenecekti, ama
bu dosyayı SADECE GitHub Actions (CI) yazıp git'e geri push ediyor. Kullanıcı
web sayfasından bir ürün eklediğinde bunu yazan Render'daki canlı sunucu -
aynı dosyaya CI'dan BAĞIMSIZ olarak paralel yazıp push etseydi, biri
diğerinin daha yeni verisini ezme riski vardı (git'te "kaybolan" satırlar).
Çözüm: abonelik listesi ayrı bir dosyada (`data/subscriptions.json`,
`core/subscriptions_store.py`) - bu dosyayı SADECE Render yazıyor, CI sadece
okuyor (her çalıştırmasında zaten taze bir git checkout'u alıyor). Tek dosya
= tek yazan kuralı, çakışma riski yok.

### Render'dan git'e push: GitHub REST API, `git push` değil

Render'ın Docker imajı build-time'da kopyalanmış bir kod anlık görüntüsü -
içinde çalışan bir git deposu (`.git` + kimlik doğrulama) olduğundan emin
olamadık. Bunun yerine `core/git_sync.py`, GitHub'ın REST **Contents API**'sini
kullanıyor: dosyayı base64'e çevirip doğrudan `PUT /repos/.../contents/...`
ile güncelliyor - yerel bir git deposuna hiç ihtiyaç duymuyor. Bunun için bir
GitHub Personal Access Token (`GITHUB_PAT` ortam değişkeni, Render'da
tanımlanması gerekiyor) lazım - tanımlı değilse (örn. yerelde geliştirirken)
push adımı sessizce atlanıyor, API yine de normal çalışıyor.

### Kapsam bilinçli olarak dar tutuldu

- **Kullanıcı hesabı/login YOK** - tek kişilik kişisel bir araç, sabit 3
  kategorinin bildirim mantığıyla aynı (tek Telegram/e-posta hedefi).
- **Fiyat gösterimi canlı taramıyor** - `GET /api/subscriptions` en son bilinen
  fiyatı `price_history.db`'den okuyor, her sayfa açılışında Playwright
  beklemek istemedik. Güncel fiyat, `check_and_notify.py`'nin periyodik
  taramasına eklenen abonelik kontrolüyle tazeleniyor (aynı medyan mantığı,
  `discount_detector.py`).
- **Arayüz** (`web/ssd-takip.html`) bir UI Designer agent'ına tasarlattırıldı
  - "Depo Nöbetçi" kimliği (grafit zemin, tek mavi vurgu rengi, Space
    Grotesk + JetBrains Mono), `laptop-arama/selanik-fiyat-panosu.html`'nin
    sıcak/gazete tarzından bilinçli olarak farklı. Aynı teknik iskelet: tek
    dosya, `fetch()` ile Render'daki backend'e bağlanma, ana ekrana eklenince
    gerçek bir uygulama gibi açılan PWA meta etiketleri.

---

## Sistem 2: Laptop Fiyat Karşılaştırma Botu (isteğe bağlı, elle tetiklenen)

**Amaç:** RTX 5070 Ti/5080/5090 (12GB+ ekran kartı belleği) laptopların
Türkiye ve yurtdışı (Avrupa) fiyatlarını karşılaştırmak - ama SSD sistemi
gibi sürekli otomatik değil, sadece Telegram'dan sorulduğunda çalışıyor.
Ayrı bir klasörde (`laptop-arama/`) tutuldu ki istenirse SSD sisteminden
bağımsız olarak kapatılabilsin/açılabilsin.

### 1. Yurtdışı fiyat kaynağı: PriceRunner

Araştırma sonucu **PriceRunner** (İngiltere merkezli, çok sayıda mağazayı
tek yerde karşılaştıran bir site) kullanıldı - hem robots.txt izin veriyor
hem de gerçek veri sunuyor. Üç kategori sayfası (5070 Ti, 5080, 5090 için)
birleştirilip tarandı.

### 2. Türkiye fiyat kaynağı

Amazon.com.tr ve n11.com üzerinden RTX 5070 Ti/5080/5090 laptop arandı.
İki kaynak kullanıldı çünkü tek bir sitenin arama sonuçları istekten
isteğe değişkenlik gösterebiliyor (reklam/sıralama rotasyonu). Ayrıca
arama sonuçlarına masaüstü ekran kartları (laptop değil) sızıyordu - bunu
"dizüstü/laptop/notebook" kelimesi geçme şartıyla filtreledik.

### 3. Model eşleştirme

En zor kısım buydu: Türkiye'de bulunan bir laptopla, yurtdışında bulunan
bir laptopun **aynı fiziksel ürün** olup olmadığını anlamak. İlk denemede
sadece "aynı model kodu" (örn. "A2XWHG") aranmıştı ama bu yanlış eşleşmeler
üretti (iki farklı ürün serisi, tesadüfen aynı kod parçasını paylaşıyordu).

Sonunda üç katmanlı bir kontrol kuruldu (`laptop-arama/matcher.py`):
1. Marka aynı mı (örn. "MSI")
2. Ürün serisi aynı mı (örn. "Vector", "Legion", "ROG Strix" - bilinen
   oyun laptop serileri listesi)
3. Model kodu da örtüşüyorsa **"kesin eşleşme"**, örtüşmüyorsa **"yaklaşık
   eşleşme"** olarak etiketleniyor - kullanıcıya hangisinin ne kadar
   güvenilir olduğu açıkça söyleniyor.

### 4. Güncel kur

Yurtdışı fiyatı İngiliz Sterlini (£) cinsinden geliyor. **Frankfurter API**
(ücretsiz, key gerektirmeyen, Avrupa Merkez Bankası verisine dayanan bir
döviz kuru servisi) ile anlık GBP→TL kuru çekilip TL karşılığı hesaplanıyor
(`laptop-arama/currency.py`).

### 5. Mani formatı

İstediğin gibi, her bot cevabının başına rastgele bir mani (4 dizelik halk
şiiri) ekleniyor - 18 tane orijinal mani yazılıp bir listeye konuldu
(`laptop-arama/manis.py`), her cevapta rastgele biri seçiliyor.

### 6. Telegram botu: önce "polling", sonra "webhook"

İlk kurulan sistem **polling** denen bir yöntemdi: GitHub Actions her 5
dakikada bir "yeni mesaj var mı?" diye Telegram'a soruyordu. Ama GitHub'ın
kendi zamanlama sistemi, bu kadar sık (5 dakikalık) görevleri güvenilir
çalıştırmıyor - test ettiğimizde saatlerce hiç tetiklenmediği görüldü.

Sen "anlık" cevap istediğin ve arkadaşına öyle söz verdiğin için, sisteme
**webhook** mimarisine geçirildi: Telegram artık bize sormuyor, mesaj
geldiği an **kendisi** bize haber veriyor (`laptop-arama/webhook_app.py`,
Flask ile yazılmış küçük bir web sunucusu). Bunun çalışabilmesi için 7/24
açık, dışarıdan erişilebilir bir sunucu gerekiyordu - GitHub Actions bunu
sağlayamıyor (görev bazlı, sürekli açık değil).

### 7. Render.com

Bu yüzden **Render.com** (ücretsiz, kod ver-çalıştır tarzı bir bulut
barındırma servisi) kullanılmaya başlandı. Kod oraya bağlandı, Telegram'a
"artık mesajları doğrudan bu adrese gönder" denildi (webhook kaydı). Eski
polling sistemi (`telegram_bot.py`, `laptop-bot.yml` workflow'u) tamamen
kaldırıldı çünkü Telegram bir bota aynı anda hem webhook hem polling
kullandırmıyor.

---

## Özet: Neyi ne için kullandık

| Araç/Teknoloji | Ne için kullandık |
|---|---|
| Python | Tüm kod |
| Playwright | JS ile render edilen / bot korumalı siteleri gerçek tarayıcı gibi açmak |
| requests + BeautifulSoup | Basit, JS gerektirmeyen siteleri taramak |
| SQLite | Fiyat geçmişini saklamak, tarih aralığı sorgusu yapmak |
| Git + GitHub | Kod versiyon kontrolü, proje deposu |
| GitHub Actions | Zamanlanmış otomatik çalıştırma (SSD taraması, her 10 dakikada bir) |
| GitHub Secrets | Şifre/API key'leri koda yazmadan güvenli saklamak |
| SMTP (Gmail) | E-posta bildirimi |
| Telegram Bot API | Telegram bildirimi/botu |
| CallMeBot | WhatsApp bildirimi |
| Frankfurter API | Güncel döviz kuru |
| Flask | Anlık cevap veren küçük web sunucusu (laptop botu) |
| Render.com | Flask sunucusunu 7/24 açık tutan ücretsiz barındırma |
