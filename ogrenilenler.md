# Öğrenilenler

Bu proje boyunca sorduğun sorulardan çıkan, terimsel/kavramsal anlam taşıyan konuların
kısa açıklamaları. Kronolojik sırayla, hangi soru/durumdan çıktığı da belirtilerek.

## robots.txt
Bir sitenin, hangi otomatik programların (arama motoru botları, scraper'lar) hangi
sayfalarına girebileceğini beyan ettiği metin dosyası (`site.com/robots.txt`).
Hukuken bağlayıcı değil ama saygı gösterilmesi beklenen bir "izin listesi" - bir
kapıdaki "lütfen çalmadan girmeyin" yazısı gibi düşünebilirsin, kilit değil.
*Nereden çıktı: Trendyol/Hepsiburada'nın arama sayfalarını taramadan önce kontrol ederken.*

## Bot tespiti / CAPTCHA / Akamai / Cloudflare
Siteler, gerçek bir insan mı yoksa otomatik bir program mı olduğunu anlamak için
çeşitli sistemler kullanır (Akamai, Cloudflare gibi şirketlerin ürünleri). Bunlar
tarayıcı parmak izi, istek hızı, JavaScript çalıştırıp çalıştıramama gibi sinyallere
bakar. CAPTCHA, bunun en bilinen şekli (resim seçme, bulmaca çözme).
*Nereden çıktı: "baypass neden yapmıyorsun" sorusu, Hepsiburada'nın CAPTCHA duvarı.*

## Headless tarayıcı / Playwright
"Headless" = ekranı olmayan, görsel arayüz göstermeden çalışan tarayıcı. Playwright,
böyle bir tarayıcıyı (Chromium/Firefox) kod ile yönetmeni sağlayan bir araç - bir
sayfayı gerçek bir kullanıcı gibi açıp JavaScript'in çalışmasını bekleyebiliyor.
*Nereden çıktı: Amazon/Trendyol'un `curl` ile açılmayıp gerçek tarayıcıda açılması.*

## SPA (Single Page Application) / sunucu tarafında render (SSR)
Bazı siteler (Trendyol, Pazarama gibi) ilk yüklenen HTML'de neredeyse hiç veri
içermez - sayfa açıldıktan sonra JavaScript, veriyi ayrıca bir API'den çekip ekliyor
(SPA). Bazıları ise (itopya, n11) veriyi doğrudan HTML içinde, sunucu tarafında
hazırlayıp gönderiyor (SSR). Fark, scraper'ın düz `requests` ile mi yoksa gerçek
tarayıcıyla mı (Playwright) çekilmesi gerektiğini belirliyor.
*Nereden çıktı: Trendyol'un ilk HTML'inde ürün verisi bulunamaması.*

## Pazaryeri vs. doğrudan satıcı
Amazon/Trendyol/Hepsiburada birer **pazaryeri** - aynı ürünü onlarca farklı satıcı
farklı fiyata satabilir. itopya/incehesap ise **doğrudan satıcı** - ürünü kendileri
satıyor, tek bir fiyat var. Bu, fiyat takibi için doğrudan satıcıyı daha "temiz" bir
veri kaynağı yapıyor (hangi satıcı belirsizliği yok).
*Nereden çıktı: "itopya ve incehesapı ilk defa duyuyorum, ne tür site" sorusu.*

## Resmi API'lerin gerçek amacı (Affiliate API vs Seller API)
Amazon'un Product Advertising API'si **affiliate** (tanıtım ortaklığı) için - amaç
sana veri vermek değil, senin üzerinden satış yapmasını sağlamak; bu yüzden aktif
satış geçmişi şart koşuyor. Trendyol/Hepsiburada'nın API'leri ise **seller
(satıcı)** API'si - kendi mağazanı yönetmen için, alıcı olarak ürün sorgulaman için
değil. "Resmi API" her zaman "herkese açık, istediğini sorgula" anlamına gelmiyor.
*Nereden çıktı: "resmi api kullanmak için ne gerekiyorsa ben yapayım" sorusu.*

## Uygulama Şifresi (App Password)
Google/Microsoft gibi servislerin, 2 adımlı doğrulama açıkken normal şifren yerine
üçüncü parti uygulamalara (örneğin bir Python scriptine) verdiğin, sınırlı yetkili,
ayrı bir şifre. Ana hesap şifrenden bağımsız üretilir/iptal edilir - sızsa bile
hesabına tam giriş yapılamaz, sadece o uygulamanın yetkisi (örn. sadece mail
gönderme) kötüye kullanılabilir.
*Nereden çıktı: SMTP şifresi sorulurken, "güvenlik açığı yok değil mi" sorusu.*

## API key
Bir servisin (CallMeBot, Telegram gibi) "bu isteği kim yapıyor" diye tanımak için
kullandığı, sana özel verilen bir kod/anahtar. Şifre gibi davranılmalı (paylaşılmamalı)
ama genelde şifreden daha dar yetkili ve iptal/yenilemesi daha kolaydır.
*Nereden çıktı: "api key lazım mı" sorusu.*

## Polling (getUpdates) vs. Webhook
Telegram botunun sana gelen mesajları öğrenmesinin iki yolu var: **polling** - botun
kendisi düzenli olarak sunucuya "yeni mesaj var mı?" diye sorması (`getUpdates` API'si
bunu yapıyor, bizim chat_id'yi bulmak için kullandığımız yöntem); **webhook** - sunucunun
yeni mesaj geldiğinde bota otomatik haber vermesi. Botun sana "cevap" yazmaması normaldi
çünkü hiç kod çalıştırmıyordu, sadece mesajları biriktiriyordu.
*Nereden çıktı: "yazıyorum ama yanıt yok" sorusu.*

## Medyan vs. ortalama
Ortalama, tüm değerleri toplayıp sayıya bölmek - tek bir aşırı değer (yapay zam gibi)
onu kolayca çeker. Medyan, değerleri sıraya dizip ortadakini almak - birkaç günlük
yapay zam, verinin çoğunluğu normal seviyedeyse medyanı neredeyse hiç etkilemez. Bu
yüzden "gerçek indirim mi, sahte mi" sorusunda medyan tercih edildi.
*Nereden çıktı: Adım 4, sahte indirim tespit mantığı tasarlanırken.*

## GitHub Secrets
Bir GitHub reposuna, kod içine yazmadan şifre/API key gibi hassas bilgi eklemenin
yolu. Şifrelenmiş saklanır, workflow çalışırken ortam değişkeni olarak enjekte edilir,
loglarda bile otomatik olarak maskelenir (`***` gösterilir). Repo public olsa bile
secret değerleri görünmez.
*Nereden çıktı: Adım 6, GitHub'a eklenecek 9 secret listelenirken.*

## GitHub Actions - "dakika" kotası ve public/private fark
GitHub Actions'ta her workflow çalıştırması "dakika" tüketir. **Private** repolarda
ayda sınırlı ücretsiz kota var (2000 dk); **public** repolarda standart runner'larda
bu tamamen sınırsız ve ücretsiz. Bu yüzden repoyu public yaptık.
*Nereden çıktı: "5 dakikada bir olsa yetmez mi tokenı" sorusu.*

## GitHub Actions bulutta çalışır, senin bilgisayarında değil
Workflow tetiklendiğinde GitHub, kendi sunucularında geçici bir sanal makine
(Ubuntu) ayağa kaldırıp scripti orada çalıştırıyor, sonra o makineyi siliyor. Senin
bilgisayarınla hiçbir bağlantısı yok - PC kapalı, uykuda, internetsiz olsa bile
zamanlanmış görev çalışmaya devam eder.
*Nereden çıktı: "pcmin açık olmasına gerek var mı" sorusu.*
