"""Her bot cevabının başına eklenen, rastgele seçilen mani havuzu."""
import random

MANILER = [
    "Bahçede gülüm biter\nDalları yola gider\nSen bekle biraz canım\nFiyatlar şimdi gelir",
    "Yüksek dağın başında\nKar tanesi var yağar\nLaptop dedin be kardeş\nCüzdanım hafif ağlar",
    "Elmayı dalda kopardım\nTadına bir bakayım\nSen otur biraz keyifle\nEn ucuzu bulayım",
    "Çeşmenin suyu berrak\nİçtim de gitti sızı\nYurtdışı Türkiye derken\nKarşılaştırdım hepsini",
    "Bulut gökte yürüyor\nGölgesi yerde kalır\nEkran kartı beğendin mi\nHesap şimdi çıkar bil",
    "Fındığı kırdım ikiye\nİçi tatlı çıkıyor\nSen fiyat sorduğun anda\nSistem hemen çalışıyor",
    "Tarlada başak sarı\nRüzgarda dalgalanır\nPound'u liraya çevirdim\nBak şimdi ne kadar",
    "Kırlangıç uçtu gitti\nYuvasını yapmaya\nBen de koştum baktım durdum\nEn iyi fiyatı bulmaya",
    "Nar tanesi kırmızı\nTadı biraz ekşidir\nKur bugün böyle çıktı\nYarın belki değişir",
    "Yaylada tütün eker\nKöylü emek harcar\nSana da emek verdim\nİşte listeler hazır",
    "Deniz mavi mavidir\nDalgası kıyıya vurur\nAra sıra sabret biraz\nVeri toplanıp durur",
    "Ceviz ağacı gölge\nAltında serin olur\nHer iki ülke fiyatı\nYan yana burda durur",
    "Kuşlar dalda öter\nSabah erken uyanır\nSen sordun ben aradım\nİşte cevap sana yakın",
    "Gökte yıldız sayılmaz\nHer biri bir ışıktır\nHer laptop bir fiyat\nHepsi burda yazılıdır",
    "Pınarın suyu soğuk\nİçince ferahlarsın\nListeyi okuyunca\nHangisi ucuz görürsün",
    "Buğday tarlası altın\nHasat vakti yaklaşır\nSenin de bu alışverişin\nBiraz sabırla açılır",
    "Karanfil kokusu tatlı\nBahçede açar durur\nİki ülkenin fiyatı\nAlt alta burda durur",
    "Ay doğar dağın ardından\nIşığı yola vurur\nAradığın o laptop\nAşağıda yazılıdır",
]


def rastgele_mani() -> str:
    return random.choice(MANILER)
