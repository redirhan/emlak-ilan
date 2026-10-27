---
name: emlak-ilan
description: Emlak İlan Kiti — emlak danışmanları için taşınmaz bilgilerinden (YAML) Sahibinden, Hepsiemlak ve Emlakjet ilan başlığı, açıklaması ve özellik listesi; Instagram reels planı ve ekran yazıları; Türkçe Carousel Üretici formatında carousel planı üretir ve ilanı Türk emlak ilanı kurallarına göre yayından ÖNCE denetler. EİDS yetki doğrulaması, sosyal medyada EİDS doğrulamalı ilan linki ve fiyat zorunluluğu, Taşınmaz Ticareti Hakkında Yönetmelik m.14/2-i zorunlu bilgileri (yetki belgesi no, unvan, ada-parsel, imar-iskân, tapu), toplam fiyat (peşinat değil), hizmet bedeli sınırları, gösterme ücreti yasağı, yanıltıcı ifade ve iddia-veri çelişkisi kontrolü; indirim ve yapay zekâ görseli için Reklam Etiketi Kontrolü girdisi yazar. Her kural kaynak, tarih ve güven düzeyiyle; her çıktı "Bu bir hukuki görüş değildir; bilgilendirme amaçlıdır" der. Kullan; "emlak ilanı yaz", "sahibinden ilanı", "satılık daire ilanı", "kiralık ofis ilanı", "arsa ilanı", "EİDS", "emlak reels", "ilan uygun mu".
---

# Emlak İlan Kiti

Taşınmaz bilgilerini alır, üç portal için ilan metnini ve Instagram planını yazar, ilanı yayından önce kurallara göre
denetler. Planı ve son metni sen (Claude) gözden geçirirsin; kuralları ve tutarlılığı script denetler.

**Her çıktının başında ve sonunda şu cümle yer alır: "Bu bir hukuki görüş değildir; bilgilendirme amaçlıdır."**
Bu bir kontrol listesidir. Hukuki tavsiye vermez, kesin "yasal" ya da "yasadışı" hükmü kurmaz.

## Sınırlar (her zaman)

- **Yerel kal.** İlan yayınlama, portala ya da Instagram'a giriş, hesap açma, ücretli API yok. Paylaşımı kullanıcı yapar.
- **Tarayıcı açma.** Chrome/Chromium hiçbir koşulda başlatılmaz; portal panellerine bakılmaz.
- **Uydurma yok.** Ada/parsel, yetki belge no, iskân, emsal, mesafe, enerji sınıfı yalnız kullanıcıdan gelir. Bilinmeyen
  alana "bilinmiyor" yazılır; script bunu DÜZELT sayar. Metne girdide olmayan bir özellik (manzara, site, kredi) ekleme.
- **EİDS iddiası yalnız doğrulama varken.** `eids.yetki_dogrulandi: evet` ve ilan linki yoksa hiçbir metinde "EİDS
  doğrulamalı" yazmaz; script yer tutucu koyar.
- **Müşterinin işine karışma.** Fiyatlama, sözleşme, vergi ya da tapu işlemi hakkında görüş verme; emin olunmayan konuda
  "UZMANA SOR" de (avukat ya da ticaret il müdürlüğü).

## Dosyalar

```
SKILL.md                 bu dosya
rules/kurallar.yaml      42 kural: id, koşul, düzeltme, kaynak (belge + madde + URL + belge tarihi + okunma tarihi),
                         güven (yüksek / orta / düşük), belirsizlik; EİDS takvimi; ceza aralıkları; kırmızı bayrak sözlüğü
scripts/ilan.py          üretici + denetleyici (Python 3.8+, yalnız standart kütüphane)
scripts/mini_yaml.py     PyYAML yoksa kullanılan küçük YAML okuyucu
examples/                3 kurgusal ilan + tüm çıktıları (satılık daire, kiralık ofis, bilerek uyumsuz arsa)
tests/                   birim testleri
```

## Akış

`S=<skill klasörü>/scripts`

1. **Kontrol:** `python3 $S/ilan.py doctor`
2. **Bilgiyi topla.** Eksikse sor, tahmin etme:
   - ilan türü (satılık/kiralık), emlak tipi (konut/iş yeri/arsa), **toplam** fiyat ya da aylık kira (TL)
   - il, ilçe, mahalle, **ada, parsel** (açık adres değil)
   - m² (brüt/net), oda/bölüm, banyo, tuvalet, balkon ve odaların yaklaşık m²'si, kat, kat sayısı, bina yaşı, cephe,
     manzara, ısıtma, apartman/site/plaza, donatılar; arsada imar durumu, emsal, gabari, hisse, ekili/dikili ürün
   - tapu cinsi, iskân, ipotek/haciz, fiili kullanım (boş/kiracılı), enerji kimlik belgesi sınıfı
   - en yakın duraklar ve sosyal mekânlara yaklaşık mesafe
   - işletme unvanı (yetki belgesindeki gibi), **yetki belgesi no**, telefon, Instagram hesabı
   - yazılı yetkilendirme sözleşmesi var mı, yetki bitiş tarihi; **EİDS ilan yayınlama izni geldi mi**, ilan no ve link
   - hizmet bedeli ilanda yazılacak mı; fiyat değiştiyse önceki fiyat, son 10 günün en düşüğü, değişim tarihi
   - görseller bu taşınmazdan mı; yapay zekâ kullanıldı mı (sanal mobilya, gökyüzü, render); temsili görsel var mı
   - bir içerik üretici para/hediye karşılığı mı paylaşacak
3. **Girdi dosyasını yaz.** `python3 $S/ilan.py sablon --tur satilik-daire > ilan.yaml` (`kiralik-ofis`, `arsa`).
   Doldur. Örnekler: `examples/*/ilan.yaml`.
4. **Üret ve denetle.**
   ```bash
   python3 $S/ilan.py uret ilan.yaml --cikti ilan_cikti/
   ```
   Çıktı: `ilanlar.md` (3 portal: başlık + açıklama + özellik listesi + form alanları), `instagram.md` (reels çekim
   planı, kalıcı fiyat + EİDS rozeti, son kart, kapak, açıklama, story), `carousel_plan.yaml`, gerekirse
   `reklam_kontrol.yaml` (+ Reklam Etiketi Kontrolü kuruluysa `reklam_rapor.md`), `rapor.md`, `rapor.json`.
   Çıkış kodu 1 = en az bir DÜZELT var; metinler "TASLAK — YAYINLAMAYIN" başlığıyla ve `[GEREKLİ]` yer tutucularıyla yazılır.
   Yalnız rapor için: `python3 $S/ilan.py kontrol ilan.yaml --cikti rapor.md`.
5. **Metni gözden geçir.** `ilanlar.md`'yi oku. Script metni yalnız girilen alanlardan kurar; cümleleri akıcı hale
   getirebilirsin ama: yeni iddia ekleme, rapordaki "Metne alınmayan vurgular"ı geri koyma, zorunlu bilgiler bloğunu
   ve fiyat satırını silme. Değiştirdiğin metni girdiye geri yaz (`vurgular`, `ek_aciklama`, `basliklar.<portal>`)
   ve `uret`'i yeniden çalıştır; son kontrol script'in olsun.
6. **Carousel (isteğe bağlı).** Türkçe Carousel Üretici kuruluysa:
   `carousel.py kontrol carousel_plan.yaml && carousel.py render carousel_plan.yaml --cikti carousel/`, sonra
   `onizleme.jpg` ve her PNG'yi Read ile aç; fiyat, ilan no, yetki belge no, ada/parsel slaytta okunuyor mu bak.
7. **Kullanıcıya sun.** Sırayla:
   - ilk satır: "Bu bir hukuki görüş değildir; bilgilendirme amaçlıdır."
   - sonuç (YAYINA HAZIR DEĞİL / UZMANA DANIŞIN / KONTROL LİSTESİNİ TAMAMLAYIN / BELİRGİN BİR SORUN BULUNMADI)
   - DÜZELT ve UYARI maddeleri: bulgu + ne yapmalı + dayanak (madde no + güven)
   - kopyalanacak dosyalar (`ilanlar.md`, `instagram.md`) ve metne alınmayan ifadeler
   - ilgili belirsizlikler (aşağıda)
   - son satır: aynı uyarı + "Mevzuat değişebilir; yayından önce Resmî Gazete ve Ticaret Bakanlığı duyurularını kontrol edin."

## Temel kurallar (özet; tamamı ve kaynaklar rules/kurallar.yaml'da)

| Konu | Kural | Dayanak | Güven |
|---|---|---|---|
| EİDS | İlan, taşınmaz sahibinin e-Devlet'teki ilan yayınlama izni olmadan hiçbir kanalda yayınlanmaz | Yön. 12(2)(ç) (RG 32295); Bakanlık 17.09.2024, 22.08.2026 | yüksek |
| Sosyal medya | EİDS doğrulamalı ilan linki + ilan fiyatı zorunlu; görseller doğrulanmış taşınmaza ait | Bakanlık duyurusu 22.08.2026 | yüksek |
| Zorunlu bilgiler | Yetki belgesi no, belgedeki unvan, il/ilçe/mahalle, ada/parsel (adres yok), iletişim, varsa enerji kimlik bilgisi | Yön. 14(2)(i) | yüksek |
| 15/3 bilgileri | İmar-iskân, tapu cinsi, m², yaş, kullanım, kat-cephe-manzara, durak ve sosyal mesafe, oda sayısı ve m², yapı tipi-donatı, arazide hisse-emsal-gabari-ürün, ipotek/haciz | Yön. 14(2)(i) → 15(3) | orta |
| Fiyat | Toplam bedel (peşinat değil); TL; yem fiyat yok; fiyat artışı haklı sebebe dayanmalı | Yön. 12(1), 12(3), 14(2)(b) | yüksek / orta |
| Hizmet bedeli | Satışta toplam %4 + KDV, kirada 1 aylık kira + KDV; gösterme ücreti alınmaz | Yön. 20, 19(4) | yüksek |
| Yetki | Yazılı yetkilendirme sözleşmesi; yetki bitince ya da satılınca 3 gün içinde ilan kalkar | Yön. 14(2)(h)(j), 15(1) | yüksek |
| Yanıltıcı | Garanti/kesin getiri/"imar gelecek" yok; iddia girdiyle çelişmez; hisseli tapu açık yazılır | Yön. 12(1), 14(2)(b)(ç) | orta / yüksek |
| İndirim, YZ | Belgeli "fiyat düştü" (son 10 günün en düşüğü) ve yapay zekâ görsel beyanı → Reklam Etiketi Kontrolü | Ticari Reklam Yön. 14, 18(8) (RG 33297) | orta |

## Belirsizlikler (kullanıcıya dürüstçe söyle)

1. **EİDS tarihleri çelişkili.** Kimlik doğrulama 01.11.2023 (kesin). Yetki doğrulama kiralıkta 01.01.2025, satılık iş
   yerinde 07.04.2025 (tek ikincil kaynak), satılık konutta 01.02.2026 (ülke geneli mi, yalnız İzmir-Antalya-Sivas
   pilotu mu belirsiz) ve 15.02.2026 (AA'ya göre ülke geneli). Satılık arsa için tarih bulunamadı. **Kodlanan:** bugün
   her ilan türü ve her kanal için EİDS şart (Bakanlık 22.08.2026: "elektronik ortamda verilen tüm taşınmaz ilanları").
2. **Ceza tutarları.** Notlardaki "100 bin TL'ye kadar" ve "158.460 TL" ikisi de eksik. Emlak işletmesine 6585 s. Kanun
   18(1)(i): kanunda 10.000-300.000 TL; 2026 değeri hesapla 28.620-858.620 TL (Bakanlık tablosu bulunamadı; alt sınır
   Ekim 2026'daki 28.620 TL cezayla birebir tutuyor). 100.000 TL Bakanlığın işletme başına uyguladığı tutar; 158.460 TL
   platformlara uygulanan 6563 s. Kanunun 2024 üst sınırı. Aynı yıl tekrarında iki katı; yetki belgesi iptali mümkün.
3. **15(3) bilgileri ilanda zorunlu mu?** 15(3) sözleşmenin asgari içeriğini sayar; 14(2)(i) ilanlarda "15 inci maddenin
   üçüncü fıkrasında belirtilen diğer bilgilere" yer verilmesini ister. Daha sıkı okuma kodlandı (DÜZELT).
4. **Sosyal medyada link nerede?** Bakanlık yerini belirtmiyor. Kit linki açıklamaya, fiyatı açıklama + kalıcı rozet +
   son karta koyar; Instagram'da link tıklanmadığı için profil/hikâye bağlantısı da önerilir.
5. **İndirim kuralı (m.14) aracıya uygulanır mı?** Net değil; daha sıkı yorumla uygulanır.
6. **Döviz fiyat.** 32 sayılı Karar sözleşme bedelini düzenler; ilan metnine doğrudan hüküm bulunamadı (UYARI).
7. **Portal kuralları doğrulanamadı.** Sahibinden/Hepsiemlak/Emlakjet başlık sınırları ve açıklama kuralları giriş
   gerektirdiği için okunamadı; başlık sınırları bilerek kısa (50/60) tutuldu (güven: düşük).

## Bakım

- Kural ekle/değiştir: `rules/kurallar.yaml` (her kurala kaynak + belge tarihi + okunma tarihi + güven şart), sonra
  `python3 scripts/ilan.py kurallari-dogrula` ve `python3 -m unittest discover -s tests`.
- Kaynaklar 27.10.2026'da okundu. Yeni Resmî Gazete değişikliği, Bakanlık duyurusu ya da yıllık yeniden değerleme
  oranı (Kasım) çıkınca `surum`, `kural_tarihi`, `cezalar` ve `eids_takvim` alanlarını güncelle, CHANGELOG'a yaz.
