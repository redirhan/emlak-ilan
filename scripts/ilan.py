#!/usr/bin/env python3
"""Emlak İlan Kiti (MIT, Redirhan Labs).

Taşınmaz bilgilerini (YAML/JSON) alır; Sahibinden, Hepsiemlak ve Emlakjet için başlık + açıklama + özellik listesi,
Instagram reels çekim planı + ekran yazıları + açıklama, Türkçe Carousel Üretici formatında carousel planı ve
Türk emlak ilanı kurallarına göre (EİDS, Taşınmaz Ticareti Hakkında Yönetmelik m.12, 14, 15, 19, 20) madde numaralı
bir kontrol raporu yazar. İndirim, yapay zekâ görseli ya da iş birliği varsa Reklam Etiketi Kontrolü için girdi üretir.

Bu bir hukuki görüş değildir; bilgilendirme amaçlıdır.

Yerel çalışır: ağ yok, hesap yok, ücretli API yok, tarayıcı yok. Yalnız Python 3.8+ standart kütüphanesi
(PyYAML varsa kullanılır, yoksa dahili okuyucu).

Kullanım:
  python3 ilan.py doctor
  python3 ilan.py sablon --tur satilik-daire > ilan.yaml      # satilik-daire | kiralik-ofis | arsa
  python3 ilan.py kontrol ilan.yaml [--cikti rapor.md] [--json rapor.json]
  python3 ilan.py uret ilan.yaml --cikti ilan_cikti/            # metinler + plan + rapor
  python3 ilan.py kurallari-dogrula
Çıkış kodu: 0 = DÜZELT yok, 1 = en az bir DÜZELT, 2 = girdi hatası.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
DEFAULT_RULES = SKILL_DIR / "rules" / "kurallar.yaml"
DISCLAIMER = "Bu bir hukuki görüş değildir; bilgilendirme amaçlıdır."
PLATFORMS = ("sahibinden", "hepsiemlak", "emlakjet")

DURUM_ETIKET = {
    "DUZELT": "DÜZELT", "UZMANA_SOR": "UZMANA SOR", "UYARI": "UYARI", "MANUEL": "GÖZLE KONTROL",
    "BILGI": "BİLGİ", "GECTI": "GEÇTİ", "UYGULANMAZ": "UYGULANMAZ",
}
DURUM_SIRA = ["DUZELT", "UZMANA_SOR", "UYARI", "MANUEL", "BILGI", "GECTI", "UYGULANMAZ"]
KATEGORI_AD = {
    "eids": "EİDS ve sosyal medya", "yetki": "Yetki belgesi ve yetkilendirme",
    "zorunlu": "Zorunlu ilan bilgileri (m.14/2-i)", "fiyat": "Fiyat", "komisyon": "Hizmet bedeli",
    "yaniltici": "Yanıltıcı ifade", "gorsel": "Görseller", "sosyal": "Yayın sonrası", "reklam": "Reklam etiketi",
    "platform": "Platform biçimi", "ceza": "Ceza bilgisi",
}
GUVEN_AD = {"yuksek": "yüksek", "orta": "orta", "dusuk": "düşük"}
CHECK_IDS = [
    "EIDS-01", "EIDS-02", "EIDS-03", "EIDS-04", "YTK-01", "YTK-02", "YTK-03", "YTK-04",
    "ZRN-01", "ZRN-02", "ZRN-03", "ZRN-04", "ZRN-05", "ZRN-06", "ZRN-07", "ZRN-08", "ZRN-09", "ZRN-10",
    "ZRN-11", "ZRN-12", "ZRN-13", "ZRN-14", "FYT-01", "FYT-02", "FYT-03", "FYT-04", "FYT-05", "FYT-06",
    "FYT-07", "KMS-01", "KMS-02", "YNL-01", "YNL-02", "YNL-03", "YNL-04", "GRS-01", "GRS-02", "SM-01",
    "REK-01", "PLT-01", "PLT-02", "CZA-01",
]

ALT_TIP_AD = {
    "daire": "Daire", "villa": "Villa", "mustakil": "Müstakil Ev", "rezidans": "Rezidans", "yazlik": "Yazlık",
    "ofis": "Ofis", "dukkan": "Dükkân", "depo": "Depo", "buro": "Büro", "isyeri": "İş Yeri",
    "arsa": "Arsa", "tarla": "Tarla", "bag_bahce": "Bağ-Bahçe", "zeytinlik": "Zeytinlik",
}
TAPU_AD = {
    "kat_mulkiyeti": "Kat mülkiyetli", "kat_irtifaki": "Kat irtifaklı", "hisseli": "Hisseli tapu",
    "mustakil": "Müstakil tapu", "arsa": "Arsa tapulu", "tarla": "Tarla tapulu", "tapusuz": "Tapu kaydı yok",
}
YAPI_GEN = {"apartman": "apartmanın", "site": "site içindeki binanın", "mustakil": "müstakil binanın", "plaza": "plazanın",
            "is_hani": "iş hanının", "is_merkezi": "iş merkezinin", "diger": "binanın"}
YAPI_AD = {"apartman": "apartman", "site": "site", "mustakil": "müstakil bina", "plaza": "plaza",
           "is_hani": "iş hanı", "is_merkezi": "iş merkezi", "diger": "bina"}
KULLANIM_AD = {"bos": "Boş", "kiracili": "Kiracılı", "mal_sahibi": "Mal sahibi oturuyor"}
YZ_BEYAN = {
    "sanal_mobilya": "Fotoğraflardaki mobilyalar yapay zekâ ile yerleştirilmiştir; taşınmaz boş teslim edilir.",
    "gokyuzu": "Bazı fotoğraflarda gökyüzü yapay zekâ ile düzenlenmiştir.",
    "render": "Bazı görseller yapay zekâ ile üretilmiş temsili görsellerdir.",
    "diger": "Bazı görseller yapay zekâ ile düzenlenmiştir.",
}
YZ_KISA = {"sanal_mobilya": "Mobilyalar yapay zekâ ile yerleştirildi", "gokyuzu": "Gökyüzü yapay zekâ ile düzenlendi",
           "render": "Yapay zekâ ile üretilmiş temsili görsel", "diger": "Yapay zekâ ile düzenlendi"}
YZ_YANILTICI = {"yapi_degisikligi", "manzara", "manzara_ekleme", "havuz", "genisletme"}
YZ_SERBEST = {"isik_renk"}


# ---------------------------------------------------------------- yardımcılar
def load_data(path):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        return json.loads(text)
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except ImportError:
        sys.path.insert(0, str(HERE))
        import mini_yaml  # type: ignore
        return mini_yaml.loads(text)


def tr_lower(s):
    return str(s).replace("I", "ı").replace("İ", "i").lower()


def tr_upper(s):
    return str(s).replace("i", "İ").replace("ı", "I").upper()


def tr_cap(s):
    s = str(s)
    return tr_upper(s[:1]) + s[1:] if s else s


def fold(s):
    return tr_lower(s).replace("â", "a").replace("î", "i").replace("û", "u")


def yes(v):
    return fold(v) in ("evet", "true", "var", "yes", "1") if v is not None and v != "" else False


def no(v):
    return fold(v) in ("hayir", "hayır", "false", "yok", "no", "0") if v is not None and v != "" else False


def filled(v):
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != "" and fold(v.strip()) not in ("bilinmiyor", "?", "todo")
    return True


def unknown(v):
    return isinstance(v, str) and fold(v.strip()) == "bilinmiyor"


def num(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("TL", "").replace("₺", "").replace(" ", "")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", s):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def tl(n):
    v = num(n)
    if v is None:
        return ""
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v)):,}".replace(",", ".") + " TL"
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"


def ival(v):
    n = num(v)
    return int(n) if n is not None and abs(n - round(n)) < 1e-9 else n


def parse_date(s):
    if not s:
        return None
    try:
        return _dt.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def ek_de(word):
    """Özel isme bulunma eki: Caferağa'da, Kadıköy'de, Etimesgut'ta."""
    w = str(word).strip()
    if not w:
        return w
    low = fold(w)
    vowels = [c for c in low if c in "aeıioöuü"]
    last = vowels[-1] if vowels else "e"
    suf = "da" if last in "aıou" else "de"
    if low[-1] in "fstkçşhp":
        suf = "t" + suf[1:]
    return f"{w}'{suf}"


def clean_mahalle(m):
    m = str(m or "").strip()
    return re.sub(r"\s+(mahallesi|mah\.?|mh\.?)$", "", m, flags=re.I).strip()


def match_terms(text, terms):
    f = fold(text)
    hits = []
    for t in terms or []:
        t = str(t)
        if t.startswith("r:"):
            m = re.search(t[2:], f, flags=re.I)
            if m:
                hits.append(m.group(0).strip()[:40])
        elif t.endswith("$"):
            if re.search(r"(?<!\w)" + re.escape(fold(t[:-1])) + r"(?!\w)", f):
                hits.append(t[:-1])
        elif fold(t) in f:
            hits.append(t)
    return hits


def g(d, path, default=None):
    cur = d
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return default if cur is None else cur


# ---------------------------------------------------------------- kurallar
class Rules:
    def __init__(self, path=DEFAULT_RULES):
        self.path = Path(path)
        self.data = load_data(self.path)
        self.by_id = {r["id"]: r for r in self.data.get("kurallar", [])}
        self.lex = self.data.get("sozluk", {}) or {}
        self.esik = self.data.get("esikler", {}) or {}
        self.platform = self.data.get("platformlar", {}) or {}

    def validate(self):
        errs = []
        seen = set()
        ids = {k["id"] for k in self.data.get("kaynaklar", [])}
        for r in self.data.get("kurallar", []):
            rid = r.get("id", "?")
            if rid in seen:
                errs.append(f"{rid}: tekrar eden id")
            seen.add(rid)
            for f in ("baslik", "kategori", "siddet", "kosul", "duzeltme", "guven"):
                if not r.get(f):
                    errs.append(f"{rid}: '{f}' eksik")
            if r.get("siddet") not in ("DUZELT", "UYARI", "UZMANA_SOR", "MANUEL", "BILGI"):
                errs.append(f"{rid}: geçersiz siddet {r.get('siddet')}")
            if r.get("guven") not in GUVEN_AD:
                errs.append(f"{rid}: geçersiz guven {r.get('guven')}")
            if r.get("kategori") not in KATEGORI_AD:
                errs.append(f"{rid}: bilinmeyen kategori {r.get('kategori')}")
            ks = r.get("kaynak") or []
            if not ks:
                errs.append(f"{rid}: kaynak yok")
            for k in ks:
                for f in ("belge", "madde", "url", "tarih", "okunma"):
                    if not k.get(f):
                        errs.append(f"{rid}: kaynakta '{f}' eksik")
                if not str(k.get("url", "")).startswith("https://"):
                    errs.append(f"{rid}: kaynak url https değil")
                for f in ("tarih", "okunma"):
                    if k.get(f) and not parse_date(k.get(f)):
                        errs.append(f"{rid}: kaynak {f} YYYY-AA-GG değil")
        for cid in CHECK_IDS:
            if cid not in self.by_id:
                errs.append(f"{cid}: kodda var, kural dosyasında yok")
        for rid in self.by_id:
            if rid not in CHECK_IDS:
                errs.append(f"{rid}: kural dosyasında var, kodda karşılığı yok")
        for c in self.data.get("cezalar", []):
            for k in c.get("kaynak", []):
                if k not in ids:
                    errs.append(f"cezalar: bilinmeyen kaynak {k}")
        for e in self.data.get("eids_takvim", []):
            if e.get("kaynak") not in ids:
                errs.append(f"eids_takvim: bilinmeyen kaynak {e.get('kaynak')}")
        for p in PLATFORMS:
            if p not in self.platform:
                errs.append(f"platformlar: {p} yok")
        for k in self.data.get("kaynaklar", []):
            for f in ("id", "belge", "url", "tarih", "okunma"):
                if not k.get(f):
                    errs.append(f"kaynaklar/{k.get('id', '?')}: '{f}' eksik")
        return errs


# ---------------------------------------------------------------- ilan modeli
class Ilan:
    def __init__(self, d, tarih):
        self.d = d or {}
        self.tarih = tarih
        self.eksik_girdi = []
        self.tur = fold(self.get("ilan_turu", "satilik")).replace("ı", "i")
        if self.tur not in ("satilik", "kiralik"):
            raise ValueError("ilan_turu: satilik ya da kiralik olmalı")
        self.tip = fold(self.get("emlak_tipi", "konut")).replace("ş", "s").replace(" ", "_")
        if self.tip == "isyeri":
            self.tip = "is_yeri"
        if self.tip not in ("konut", "is_yeri", "arsa"):
            raise ValueError("emlak_tipi: konut, is_yeri ya da arsa olmalı")
        self.alt = fold(self.get("alt_tip", {"konut": "daire", "is_yeri": "ofis", "arsa": "arsa"}[self.tip]))
        self.alt_ad = self.get("alt_tip_ad") or ALT_TIP_AD.get(self.alt, tr_cap(self.alt))
        self.isletme = fold(self.get("ilan_veren", "isletme")) != "sahibi"
        kan = self.get("kanallar") or ["portal", "instagram"]
        self.kanallar = [fold(k) for k in kan]
        self.sosyal = any(k in ("instagram", "sosyal", "facebook", "tiktok", "whatsapp") for k in self.kanallar)
        self.portal = any(k in ("portal",) + PLATFORMS for k in self.kanallar)
        self.yayin = parse_date(self.get("yayin_tarihi")) or tarih
        self.arsa = self.tip == "arsa"

    def get(self, path, default=None):
        return g(self.d, path, default)

    # türetilmiş metin parçaları
    @property
    def tur_ad(self):
        return ("Satılık" if self.tur == "satilik" else "Kiralık") + " " + self.alt_ad

    @property
    def mahalle(self):
        return clean_mahalle(self.get("konum.mahalle"))

    @property
    def konum_str(self):
        parts = [p for p in (self.mahalle, self.get("konum.ilce")) if p]
        s = ", ".join(str(p) for p in parts)
        il = self.get("konum.il")
        return f"{s} / {il}" if il and s else (s or str(il or ""))

    @property
    def m2(self):
        if self.arsa:
            return ival(self.get("arsa.alan_m2") or self.get("ozellikler.brut_m2"))
        return ival(self.get("ozellikler.net_m2") or self.get("ozellikler.brut_m2"))

    @property
    def m2_str(self):
        if self.arsa:
            return f"{self.m2} m²" if self.m2 else ""
        b, n = ival(self.get("ozellikler.brut_m2")), ival(self.get("ozellikler.net_m2"))
        if b and n:
            return f"{b} m² brüt / {n} m² net"
        return f"{b or n} m²" if (b or n) else ""

    @property
    def fiyat_str(self):
        f = tl(self.get("fiyat"))
        if not f:
            return ""
        return f + (" / ay" if self.tur == "kiralik" else "")

    @property
    def oda(self):
        return str(self.get("ozellikler.oda") or "")

    def text_pool(self):
        parts = list(self.get("vurgular") or [])
        parts += [self.get("ek_aciklama") or "", self.get("baslik_vurgu") or ""]
        for p in PLATFORMS:
            parts.append(self.get(f"basliklar.{p}") or "")
        parts.append(g(self.d, "komisyon.metin") or "")
        return "\n".join(str(x) for x in parts if x)


# ---------------------------------------------------------------- denetim
class Denetim:
    def __init__(self, ilan, rules):
        self.i = ilan
        self.r = rules
        self.items = {}
        self.cikarilan = []   # metne alınmayan vurgular
        self.celisen = []     # metinde iddiası olup girdiyle çelişen konular (YNL-02)
        self.indirim = False

    def add(self, rid, durum, bulgu, duzeltme=None, oneri=None):
        rule = self.r.by_id[rid]
        prev = self.items.get(rid)
        if prev and DURUM_SIRA.index(prev["durum"]) <= DURUM_SIRA.index(durum):
            prev["bulgu"] += " " + bulgu
            if oneri:
                prev.setdefault("oneri", []).append(oneri)
            return
        item = {
            "id": rid, "baslik": rule["baslik"], "kategori": rule["kategori"], "durum": durum, "bulgu": bulgu,
            "duzeltme": duzeltme or str(rule["duzeltme"]).strip(), "guven": rule["guven"],
            "dayanak": "; ".join(f"{k['belge']} m.{k['madde']}" if str(k["madde"])[:1].isdigit() else f"{k['belge']}: {k['madde']}"
                                 for k in rule["kaynak"]),
            "kaynak": [{"url": k["url"], "tarih": str(k["tarih"]), "okunma": str(k["okunma"])} for k in rule["kaynak"]],
        }
        if rule.get("belirsizlik"):
            item["belirsizlik"] = " ".join(str(rule["belirsizlik"]).split())
        if prev and prev.get("oneri"):
            item["oneri"] = prev["oneri"]
        if oneri:
            item.setdefault("oneri", []).append(oneri)
        self.items[rid] = item

    def ok(self, rid, bulgu="Uygun görünüyor."):
        if rid not in self.items:
            self.add(rid, "GECTI", bulgu)

    def na(self, rid, bulgu):
        if rid not in self.items:
            self.add(rid, "UYGULANMAZ", bulgu)

    def need(self, rid, fields, label=None):
        miss = []
        for path, ad in fields:
            v = self.i.get(path)
            if isinstance(v, list):
                if path in ("ozellikler.donatilar",):
                    continue  # boş liste = "donatı yok" beyanı
                if not v:
                    miss.append(ad)
            elif not filled(v):
                miss.append(ad + (" (bilinmiyor)" if unknown(v) else ""))
        if miss:
            self.add(rid, "DUZELT", "Eksik: " + ", ".join(miss) + ".")
        else:
            self.ok(rid, label or "Girildi.")
        return not miss

    # ---------------------------------------------------------- kontroller
    def run(self):
        i, lex = self.i, self.r.lex
        pool = i.text_pool()

        # EİDS
        yd = i.get("eids.yetki_dogrulandi")
        if yes(yd):
            self.ok("EIDS-01", "EİDS yetki doğrulaması yapıldı olarak girildi.")
        else:
            self.add("EIDS-01", "DUZELT", "EİDS yetki doğrulaması " + ("yapılmadı." if no(yd) else "girilmedi / bilinmiyor.")
                     + " Doğrulama olmadan ilan hiçbir kanalda yayınlanamaz.")
        link = str(i.get("eids.ilan_linki") or "").strip()
        if i.sosyal:
            if link.startswith(("http://", "https://")):
                self.ok("EIDS-02", f"EİDS doğrulamalı ilan linki girildi ({link}).")
            else:
                self.add("EIDS-02", "DUZELT", "Sosyal medya çıktısı istendi ama EİDS doğrulamalı ilan linki yok"
                         + (" (girilen değer bir URL değil)." if link else "."))
            fs = match_terms(pool, lex.get("fiyatsiz"))
            if fs:
                self.add("EIDS-03", "DUZELT", f"Metinde fiyatı gizleyen ifade var: {', '.join(fs)}.")
            elif num(i.get("fiyat")):
                self.ok("EIDS-03", "Fiyat açıklamaya, kalıcı rozete ve son karta yazılıyor.")
            else:
                self.add("EIDS-03", "DUZELT", "Fiyat yok.")
        else:
            self.na("EIDS-02", "Sosyal medya kanalı seçilmedi.")
            self.na("EIDS-03", "Sosyal medya kanalı seçilmedi.")
        ait = i.get("gorseller.bu_tasinmaza_ait")
        if no(ait):
            self.add("EIDS-04", "DUZELT", "Görsellerin bir kısmı bu taşınmaza ait değil (gorseller.bu_tasinmaza_ait: hayir).")
        elif yes(ait):
            self.ok("EIDS-04", "Görseller bu taşınmaza ait olarak girildi.")
        else:
            self.add("EIDS-04", "MANUEL", "Görsellerin yalnız bu taşınmazdan olduğunu teyit edin (gorseller.bu_tasinmaza_ait).")

        # Yetki
        if i.isletme:
            ybn = str(i.get("isletme.yetki_belgesi_no") or "").strip()
            if not ybn:
                self.add("YTK-01", "DUZELT", "isletme.yetki_belgesi_no boş.")
            elif not re.fullmatch(r"[0-9 ]{5,}", ybn):
                self.add("YTK-01", "MANUEL", f"Yetki belgesi numarası '{ybn}' rakamlardan oluşmuyor; TTBS'deki numarayla karşılaştırın.")
            else:
                self.ok("YTK-01", f"Yetki belgesi no: {ybn}.")
            self.need("YTK-02", [("isletme.unvan", "yetki belgesindeki işletme adı/unvanı")])
            sz = i.get("yetkilendirme.sozlesme")
            if yes(sz):
                self.ok("YTK-03", "Yazılı yetkilendirme sözleşmesi var olarak girildi.")
            elif no(sz):
                self.add("YTK-03", "DUZELT", "Yazılı yetkilendirme sözleşmesi yok.")
            else:
                self.add("YTK-03", "UYARI", "Yetkilendirme sözleşmesi girilmedi; teyit edin.")
            bitis = parse_date(i.get("yetkilendirme.bitis"))
            if not bitis:
                self.add("YTK-04", "MANUEL", "Yetki bitiş tarihi girilmedi (yetkilendirme.bitis); EİDS izninin süresini kontrol edin.")
            elif bitis < i.yayin:
                self.add("YTK-04", "DUZELT", f"Yetki {bitis.isoformat()} tarihinde bitmiş; yayın tarihi {i.yayin.isoformat()}.")
            elif (bitis - i.yayin).days < 30:
                self.add("YTK-04", "UYARI", f"Yetki {bitis.isoformat()} tarihinde bitiyor ({(bitis - i.yayin).days} gün). "
                         "Uzatılmazsa ilan bitişten sonraki üç gün içinde kaldırılmalı.")
            else:
                self.ok("YTK-04", f"Yetki {bitis.isoformat()} tarihine kadar geçerli.")
        else:
            for rid in ("YTK-01", "YTK-02", "YTK-03", "YTK-04"):
                self.na(rid, "İlanı taşınmaz sahibi veriyor (ilan_veren: sahibi).")

        # Zorunlu bilgiler
        self.need("ZRN-01", [("konum.il", "il"), ("konum.ilce", "ilçe"), ("konum.mahalle", "mahalle")])
        adr = match_terms(pool, lex.get("adres"))
        if adr:
            self.add("ZRN-01", "DUZELT", "Metinde açık adres kalıbı var (sokak/cadde + numara ya da daire no). Adres ilana yazılmaz.")
        if filled(i.get("konum.acik_adres")):
            self.items["ZRN-01"].setdefault("oneri", []).append("konum.acik_adres girildi; kit bunu hiçbir metne yazmaz.")
        self.need("ZRN-02", [("konum.ada", "ada"), ("konum.parsel", "parsel")])
        if i.arsa:
            self.need("ZRN-03", [("arsa.imar_durumu", "imar durumu")])
        else:
            self.need("ZRN-03", [("tapu.iskan", "yapı kullanma izni (iskân) durumu")])
        self.need("ZRN-04", [("tapu.durum", "tapu cinsi/durumu")])
        z5 = [("kullanim_durumu", "fiili kullanım durumu")]
        if i.arsa:
            z5.insert(0, ("arsa.alan_m2", "alan (m²)"))
        else:
            z5 = [("ozellikler.brut_m2", "brüt m²"), ("ozellikler.bina_yasi", "bina yaşı")] + z5
        self.need("ZRN-05", z5)
        if i.arsa:
            for rid in ("ZRN-06", "ZRN-09", "ZRN-10", "ZRN-14"):
                self.na(rid, "Arsa/arazi için uygulanmaz.")
        else:
            self.need("ZRN-06", [("ozellikler.kat", "kat"), ("ozellikler.cephe", "cephe"), ("ozellikler.manzara", "manzara")])
            z9 = [("ozellikler.oda", "oda/bölüm sayısı"), ("ozellikler.banyo", "banyo"), ("ozellikler.tuvalet", "tuvalet"),
                  ("ozellikler.balkon", "balkon")]
            ok9 = self.need("ZRN-09", z9)
            odalar = i.get("odalar") or []
            if not odalar or any(not filled(o.get("m2")) for o in odalar if isinstance(o, dict)):
                self.add("ZRN-09", "DUZELT", "Odaların yaklaşık büyüklükleri eksik (odalar listesi: ad + m2)."
                         if ok9 else "Odaların yaklaşık büyüklükleri de eksik.")
            self.need("ZRN-10", [("ozellikler.yapi_tipi", "apartman/site/müstakil")])
            if i.get("ozellikler.donatilar") is None:
                self.add("ZRN-10", "DUZELT", "Donatılar girilmedi (ozellikler.donatilar; boş liste = ek donatı yok).")
            en = i.get("enerji.sinif")
            if filled(en):
                self.ok("ZRN-14", f"Enerji sınıfı: {en}.")
            elif no(i.get("enerji.belge")):
                self.ok("ZRN-14", "Enerji kimlik belgesi yok olarak girildi.")
            else:
                self.add("ZRN-14", "UYARI", "Enerji kimlik belgesi bilgisi girilmedi (enerji.sinif ya da enerji.belge: yok).")
        if not (i.get("ulasim") or []):
            self.add("ZRN-07", "DUZELT", "ulasim listesi boş.")
        else:
            self.ok("ZRN-07", f"{len(i.get('ulasim'))} durak/mesafe girildi.")
        if not (i.get("sosyal") or []):
            self.add("ZRN-08", "DUZELT", "sosyal listesi boş.")
        else:
            self.ok("ZRN-08", f"{len(i.get('sosyal'))} sosyal mekân/mesafe girildi.")
        if i.arsa:
            self.need("ZRN-11", [("arsa.hisse", "hisse"), ("arsa.emsal", "emsal"), ("arsa.gabari", "öngörülen bina yüksekliği (gabari)"),
                                 ("arsa.ekili_dikili", "ekili/dikili ürün")])
        else:
            self.na("ZRN-11", "Yalnız arsa/arazi için.")
        self.need("ZRN-12", [("tapu.ipotek_haciz", "ipotek/haciz durumu")])
        if i.isletme:
            self.need("ZRN-13", [("isletme.telefon", "iletişim (telefon)")])
        else:
            self.need("ZRN-13", [("iletisim.telefon", "iletişim (telefon)")])

        # Fiyat
        fiyat = num(i.get("fiyat"))
        if not fiyat:
            self.add("FYT-01", "DUZELT", "fiyat boş ya da sayı değil.")
        else:
            self.ok("FYT-01", f"Fiyat: {i.fiyat_str}.")
        ft = fold(i.get("fiyat_turu", "toplam"))
        pes = match_terms(pool, lex.get("pesinat"))
        if ft != "toplam":
            self.add("FYT-02", "DUZELT", f"fiyat_turu '{i.get('fiyat_turu')}': ilan fiyatı toplam bedel değil.")
        elif pes:
            self.add("FYT-02", "UYARI", f"Metinde ödeme planı ifadesi var ({', '.join(pes)}); toplam fiyatın hemen yanında yazılı olduğundan emin olun.")
        else:
            self.ok("FYT-02", "Fiyat toplam bedel olarak girildi.")
        pb = tr_upper(i.get("para_birimi", "TL")).replace("₺", "TL").replace("TRY", "TL")
        if pb != "TL":
            self.add("FYT-03", "UYARI", f"Para birimi {pb}.")
        else:
            self.ok("FYT-03", "TL.")
        if fiyat:
            esik = num(self.r.esik.get("fiyat_min_satilik" if i.tur == "satilik" else "fiyat_min_kiralik")) or 0
            if fiyat < esik:
                self.add("FYT-04", "DUZELT", f"Fiyat {tl(fiyat)}; {i.tur} için gerçekçi alt sınırın ({tl(esik)}) altında.")
            else:
                self.ok("FYT-04", "Fiyat makul aralıkta.")
        else:
            self.na("FYT-04", "Fiyat yok.")
        yeni = (num(i.get("ozellikler.bina_yasi")) == 0) or fold(i.get("satici", "")) == "muteahhit" or (
            i.tip == "is_yeri" and i.tur == "satilik")
        if yeni and i.tur == "satilik":
            kdv = fold(i.get("kdv", ""))
            if kdv in ("dahil", "haric", "hariç", "yok"):
                self.ok("FYT-05", f"KDV: {i.get('kdv')}.")
            else:
                self.add("FYT-05", "UYARI", "Yeni bina / müteahhit / iş yeri satışı; KDV durumu belirtilmedi (kdv: dahil | haric | yok).")
        else:
            self.na("FYT-05", "İkinci el konut ya da kiralık.")
        onceki = num(i.get("fiyat_gecmisi.onceki_fiyat"))
        if onceki and fiyat and onceki < fiyat:
            art = (fiyat - onceki) / onceki * 100
            self.add("FYT-06", "UYARI", f"İlan fiyatı {tl(onceki)} → {tl(fiyat)} (%{art:.1f} artış).")
        else:
            self.na("FYT-06", "Fiyat artışı girilmedi.")
        ind = match_terms(pool, lex.get("indirim"))
        indirim = bool(ind) or yes(i.get("fiyat_gecmisi.indirim_vurgusu"))
        self.indirim = indirim
        if indirim:
            s10 = num(i.get("fiyat_gecmisi.son_10_gun_en_dusuk"))
            if not onceki or not s10:
                self.add("FYT-07", "DUZELT", "İndirim/fiyat düşüşü vurgusu var" + (f" ({', '.join(ind)})" if ind else "")
                         + " ama önceki fiyat ya da son 10 günün en düşük fiyatı girilmedi.")
            elif onceki > s10:
                self.add("FYT-07", "DUZELT", f"Gösterilen önceki fiyat {tl(onceki)}, son 10 günün en düşüğü {tl(s10)}'den yüksek. "
                         f"Önceki fiyat olarak {tl(s10)} gösterilmeli.")
            elif fiyat and fiyat >= onceki:
                self.add("FYT-07", "DUZELT", "İndirim deniyor ama güncel fiyat önceki fiyattan düşük değil.")
            else:
                self.add("FYT-07", "UYARI", f"Fiyat düşüşü {tl(onceki)} → {tl(fiyat)} belgeli görünüyor; reklam_kontrol.yaml ile Reklam Etiketi Kontrolü'nü çalıştırın.")
        else:
            self.na("FYT-07", "İndirim vurgusu yok.")

        # Hizmet bedeli
        if i.tur == "satilik":
            oran = num(i.get("komisyon.toplam_oran"))
            if oran is not None and oran > 4:
                self.add("KMS-01", "DUZELT", f"Toplam hizmet bedeli %{oran:g} (KDV hariç sınır %4).")
            elif oran is not None:
                self.ok("KMS-01", f"Toplam hizmet bedeli %{oran:g} (sınır %4 + KDV).")
            else:
                self.na("KMS-01", "Hizmet bedeli ilanda belirtilmiyor.")
        else:
            ay = num(i.get("komisyon.toplam_ay"))
            if ay is not None and ay > 1:
                self.add("KMS-01", "DUZELT", f"Toplam hizmet bedeli {ay:g} aylık kira (sınır 1 aylık kira + KDV).")
            elif ay is not None:
                self.ok("KMS-01", f"Toplam hizmet bedeli {ay:g} aylık kira (sınır 1 ay + KDV).")
            else:
                self.na("KMS-01", "Hizmet bedeli ilanda belirtilmiyor.")
        gm = match_terms(pool, lex.get("gosterme"))
        if gm or (num(i.get("komisyon.gosterme_ucreti")) or 0) > 0:
            self.add("KMS-02", "DUZELT", "Gösterme ücreti isteniyor" + (f" ({', '.join(gm)})." if gm else "."))
        else:
            self.ok("KMS-02", "Gösterme ücreti yok.")

        # Yanıltıcı ifade
        kes = match_terms(pool, lex.get("kesin"))
        if kes:
            self.add("YNL-01", "DUZELT", f"Kesinlik/garanti ifadesi: {', '.join(kes)}.")
        else:
            self.ok("YNL-01", "Kesin getiri, garanti ya da gelecekteki imar vaadi yok.")
        self._iddialar(pool)
        tapu = fold(i.get("tapu.durum", ""))
        if tapu == "hisseli" and not filled(i.get("tapu.hisse")) and not filled(i.get("arsa.hisse")):
            self.add("YNL-03", "DUZELT", "Tapu hisseli ama hisse oranı yok.")
        elif tapu == "hisseli":
            self.ok("YNL-03", "Hisseli tapu; hisse oranı başlığa ve açıklamaya yazılıyor.")
        else:
            self.na("YNL-03", "Hisseli tapu değil.")
        dk = match_terms(pool, lex.get("dikkat"))
        if dk:
            self.add("YNL-04", "UYARI", f"Üstünlük/aciliyet ifadesi: {', '.join(dk)}. Belgeli değilse metinden çıkarın.")
        else:
            self.ok("YNL-04", "Üstünlük ya da aciliyet iddiası yok.")

        # Görseller
        yz = i.get("gorseller.yapay_zeka") or {}
        neler = [fold(x) for x in (yz.get("neler") or [])] if isinstance(yz, dict) else []
        if isinstance(yz, dict) and yes(yz.get("kullanildi")):
            bad = [x for x in neler if x in YZ_YANILTICI]
            if bad:
                self.add("GRS-01", "DUZELT", f"Yapay zekâ taşınmazı olduğundan farklı gösteriyor: {', '.join(bad)}. Bu görselleri kullanmayın.")
            elif neler and all(x in YZ_SERBEST for x in neler):
                self.add("GRS-01", "BILGI", "Yalnız ışık/renk düzeltmesi; beyan gerekmeyebilir (daha sıkı yorumda yine yazılır).")
            else:
                self.add("GRS-01", "UYARI", "Yapay zekâ ile görsel düzenleme var: " + (", ".join(neler) or "belirtilmedi")
                         + ". Kit beyanı açıklamaya, reel ekranına ve carousel açıklamasına ekledi.")
        else:
            self.ok("GRS-01", "Yapay zekâ görseli yok olarak girildi.")
        if yes(i.get("gorseller.temsili")):
            self.add("GRS-02", "UYARI", "Temsili/render görsel var; kit 'Temsili görseldir' ibaresini ekledi, görselin üzerine de yazın.")
        else:
            self.na("GRS-02", "Temsili görsel yok.")

        self.add("SM-01", "BILGI", "Satış/kiralama ya da yetki sonu + 3 gün içinde portal ilanını ve sosyal medya paylaşımlarını kaldırın.")
        if yes(i.get("reklam.ticari_iliski")):
            hesap = i.get("reklam.paylasan_hesap") or "paylaşan hesap"
            self.add("REK-01", "UYARI", f"İlan {hesap} tarafından iş birliğiyle paylaşılacak; 'Reklam' etiketi gerekir.")
        else:
            self.na("REK-01", "İşletmenin kendi hesabı / iş birliği yok.")
        self.add("CZA-01", "BILGI", "Ceza aralıkları raporun sonunda.")

    def _iddialar(self, pool):
        i, idd = self.i, (self.r.lex.get("iddia") or {})
        found = []
        f = fold(pool)

        def hit(key):
            return match_terms(f, idd.get(key))
        if hit("iskan") and not yes(i.get("tapu.iskan")):
            self.celisen.append("iskan")
            found.append(("DUZELT", f"Metin '{hit('iskan')[0]}' diyor ama tapu.iskan '{i.get('tapu.iskan')}'."))
        if hit("kredi") and no(i.get("krediye_uygun")):
            self.celisen.append("kredi")
            found.append(("DUZELT", f"Metin '{hit('kredi')[0]}' diyor ama krediye_uygun: hayir."))
        elif (hit("kredi") or yes(i.get("krediye_uygun"))) and not i.arsa and not yes(i.get("tapu.iskan")):
            found.append(("UYARI", "Krediye uygun deniyor ama iskân 'var' değil; bankanın onayını alın ya da ifadeyi çıkarın."))
        yas = num(i.get("ozellikler.bina_yasi"))
        if hit("sifir") and yas is not None and yas > 0:
            self.celisen.append("sifir")
            found.append(("DUZELT", f"Metin '{hit('sifir')[0]}' diyor ama bina yaşı {ival(yas)}."))
        man = fold(i.get("ozellikler.manzara", ""))
        if hit("deniz") and not any(w in man for w in ("deniz", "boğaz", "bogaz", "göl", "gol")):
            self.celisen.append("deniz")
            found.append(("DUZELT", f"Metin '{hit('deniz')[0]}' diyor ama manzara '{i.get('ozellikler.manzara') or 'girilmedi'}'."))
        if hit("site") and fold(i.get("ozellikler.yapi_tipi", "")) != "site" and not yes(i.get("ozellikler.site_ici")):
            self.celisen.append("site")
            found.append(("DUZELT", f"Metin '{hit('site')[0]}' diyor ama yapı tipi site değil."))
        if hit("esyali") and not yes(i.get("ozellikler.esyali")):
            self.celisen.append("esyali")
            found.append(("DUZELT", f"Metin '{hit('esyali')[0]}' diyor ama eşyalı 'evet' değil."))
        if hit("metro") and not (i.get("ulasim") or []):
            self.celisen.append("metro")
            found.append(("DUZELT", f"Metin ulaşım süresi veriyor ('{hit('metro')[0]}') ama ulasim listesi boş."))
        if not found:
            self.ok("YNL-02", "Metindeki iddialar girilen bilgilerle çelişmiyor.")
        for durum, b in found:
            self.add("YNL-02", durum, b)

    def platform_titles(self, titles):
        for p, t in titles.items():
            mx = int(self.r.platform.get(p, {}).get("baslik_max", 60))
            if len(t) > mx:
                self.add("PLT-01", "UYARI", f"{p} başlığı {len(t)} karakter (ayar {mx}): '{t}'.")
            letters = [c for c in t if c.isalpha()]
            up = sum(1 for c in letters if c == tr_upper(c) and c != tr_lower(c))
            ratio = up / len(letters) if letters else 0
            if ratio > float(self.r.esik.get("buyuk_harf_orani", 0.6)) or "!!" in t or re.search(r"[\U0001F300-\U0001FAFF]", t):
                self.add("PLT-02", "UYARI", f"{p} başlığında büyük harf/emoji/ünlem fazla: '{t}'.")
        self.ok("PLT-01", "Başlıklar platform ayarlarına sığıyor.")
        self.ok("PLT-02", "Başlıklar normal yazımla.")

    # ---------------------------------------------------------- sonuç
    def sorted_items(self):
        out = []
        for rid in CHECK_IDS:
            if rid in self.items:
                out.append(self.items[rid])
        return out

    def counts(self):
        c = {k: 0 for k in DURUM_SIRA}
        for it in self.items.values():
            c[it["durum"]] += 1
        return c

    def verdict(self):
        c = self.counts()
        if c["DUZELT"]:
            return "YAYINA HAZIR DEĞİL — DÜZELTME GEREKLİ"
        if c["UZMANA_SOR"]:
            return "UZMANA DANIŞIN"
        if c["UYARI"] or c["MANUEL"]:
            return "KONTROL LİSTESİNİ TAMAMLAYIN"
        return "BELİRGİN BİR SORUN BULUNMADI"


# ---------------------------------------------------------------- metin üretimi
def ozellik_ifadesi(i):
    """Başlık için tek öne çıkan özellik (yalnız girilen alanlardan, iddia üretmez)."""
    bv = getattr(i, "temiz_baslik_vurgu", i.get("baslik_vurgu"))
    if filled(bv):
        return str(bv)
    if i.arsa:
        imar = fold(i.get("arsa.imar_durumu", ""))
        if imar and "yok" not in imar and "imarsız" not in imar:
            return "İmarlı"
        if yes(i.get("arsa.yola_cephe")):
            return "Yola Cepheli"
        return ""
    man = fold(i.get("ozellikler.manzara", ""))
    if "deniz" in man or "boğaz" in man:
        return "Deniz Manzaralı"
    if fold(i.get("ozellikler.yapi_tipi", "")) == "site":
        return "Site İçinde"
    if yes(i.get("ozellikler.esyali")):
        return "Eşyalı"
    if (num(i.get("ozellikler.balkon")) or 0) > 0 and i.tip == "konut":
        return "Balkonlu"
    if filled(i.get("ozellikler.otopark")) and not no(i.get("ozellikler.otopark")):
        return "Otoparklı"
    if yes(i.get("ozellikler.asansor")):
        return "Asansörlü"
    return ""


def basliklar(i, rules):
    feat = ozellik_ifadesi(i)
    hisse = "Hisseli " if fold(i.get("tapu.durum", "")) == "hisseli" else ""
    mah, ilce = i.mahalle, str(i.get("konum.ilce") or "")
    oda = i.oda
    m2 = f"{i.m2} m²" if i.m2 else ""
    tur = i.tur_ad
    if hisse:
        tur = tur.replace(i.alt_ad, "Hisseli " + i.alt_ad)
    cands = {
        "sahibinden": [
            f"{ek_de(mah)} {feat} {oda} {tur}, {m2}",
            f"{ek_de(mah)} {oda} {tur}, {m2}",
            f"{ek_de(mah)} {oda} {tur}",
            f"{oda} {tur}",
        ],
        "hepsiemlak": [
            f"{ilce} {mah} {oda} {m2} {tur} - {feat}",
            f"{ilce} {mah} {oda} {m2} {tur}",
            f"{mah} {oda} {m2} {tur}",
        ],
        "emlakjet": [
            f"{oda} {tur} | {mah}, {ilce} | {feat}",
            f"{oda} {tur} | {mah}, {ilce}",
            f"{oda} {tur} | {mah}",
        ],
    }
    out = {}
    for p in PLATFORMS:
        if p in getattr(i, "temiz_basliklar", {}):
            out[p] = i.temiz_basliklar[p]
            continue
        mx = int(rules.platform.get(p, {}).get("baslik_max", 60))
        chosen = None
        for c in cands[p]:
            c = re.sub(r"\s+", " ", c).replace(" ,", ",").replace("| |", "|").strip(" -|,")
            c = re.sub(r"\s*-\s*$", "", c).strip()
            if c and len(c) <= mx:
                chosen = c
                break
        out[p] = chosen or re.sub(r"\s+", " ", cands[p][-1]).strip()[:mx].rstrip()
    return out


def sorunlar(text, rules, den):
    """Bir metin parçasını ilana koymayı engelleyen sebepler (boş liste = temiz)."""
    lex, out = rules.lex, []
    for key in ("kesin", "fiyatsiz", "gosterme", "adres", "dikkat"):
        out += match_terms(text, lex.get(key))
    st = {k: v["durum"] for k, v in den.items.items()}
    if st.get("FYT-07") == "DUZELT":
        out += [f"belgesiz indirim: {h}" for h in match_terms(text, lex.get("indirim"))]
    if st.get("FYT-02") == "DUZELT":
        out += [f"toplam fiyat değil: {h}" for h in match_terms(text, lex.get("pesinat"))]
    idd = lex.get("iddia") or {}
    for key in den.celisen:
        if match_terms(text, idd.get(key)):
            out.append("girilen bilgilerle çelişiyor")
    return list(dict.fromkeys(out))


def temizle(i, rules, den):
    """Kullanıcının serbest metinlerinden (vurgular, ek açıklama, başlık vurgusu, elle başlık) sorunlu parçaları ayıklar."""
    keep = []
    for v in i.get("vurgular") or []:
        s = sorunlar(v, rules, den)
        if s:
            den.cikarilan.append(f"'{v}' ({', '.join(s)})")
        else:
            keep.append(str(v))
    ek = []
    for sent in re.split(r"(?<=[.!?])\s+", str(i.get("ek_aciklama") or "").strip()):
        if not sent.strip():
            continue
        s = sorunlar(sent, rules, den)
        if s:
            den.cikarilan.append(f"'{sent.strip()}' ({', '.join(s)})")
        else:
            ek.append(sent.strip())
    i.temiz_vurgular, i.temiz_ek = keep, " ".join(ek)
    bv = i.get("baslik_vurgu")
    i.temiz_baslik_vurgu = bv
    if filled(bv):
        s = sorunlar(bv, rules, den)
        if s:
            den.cikarilan.append(f"başlık vurgusu '{bv}' ({', '.join(s)})")
            i.temiz_baslik_vurgu = ""
    i.temiz_basliklar = {}
    for pl in PLATFORMS:
        ov = i.get(f"basliklar.{pl}")
        if filled(ov):
            s = sorunlar(ov, rules, den)
            if s:
                den.cikarilan.append(f"{pl} başlığı '{ov}' ({', '.join(s)}); kitin başlığı kullanıldı")
            else:
                i.temiz_basliklar[pl] = str(ov)
    return keep


def bilgi_satirlari(i):
    """Taşınmaz bilgi blokları: (başlık, [satırlar])."""
    blocks = []
    if i.arsa:
        a = []
        if i.m2:
            a.append(f"Alan: {i.m2} m²")
        for path, ad in (("arsa.imar_durumu", "İmar durumu"), ("arsa.emsal", "Emsal"), ("arsa.gabari", "Öngörülen bina yüksekliği (gabari)"),
                         ("arsa.hisse", "Hisse"), ("arsa.ekili_dikili", "Ekili/dikili ürün"), ("arsa.yola_cephe", "Yola cephe"),
                         ("arsa.altyapi", "Altyapı")):
            v = i.get(path)
            if filled(v) or v == 0:
                a.append(f"{ad}: {_yn(v)}")
        if filled(i.get("kullanim_durumu")):
            a.append(f"Fiili kullanım: {KULLANIM_AD.get(fold(i.get('kullanim_durumu')), i.get('kullanim_durumu'))}")
        blocks.append(("Arsa bilgileri", a))
    else:
        a = []
        if i.m2_str:
            a.append(f"Alan: {i.m2_str}")
        o = i.get("ozellikler") or {}
        if i.tip == "konut":
            if o.get("oda"):
                a.append(f"Oda: {o.get('oda')}")
        elif o.get("oda"):
            a.append(f"Bölüm/oda: {o.get('oda')}")
        for k, ad in (("banyo", "Banyo"), ("tuvalet", "Tuvalet"), ("balkon", "Balkon")):
            if o.get(k) is not None and o.get(k) != "":
                a.append(f"{ad}: {o.get(k)}")
        if o.get("kat") is not None:
            ks = f" / {o.get('kat_sayisi')} katlı bina" if o.get("kat_sayisi") else ""
            a.append(f"Kat: {o.get('kat')}{ks}")
        if o.get("bina_yasi") is not None:
            a.append(f"Bina yaşı: {o.get('bina_yasi')}")
        for k, ad in (("cephe", "Cephe"), ("manzara", "Manzara"), ("isitma", "Isıtma")):
            if filled(o.get(k)):
                a.append(f"{ad}: {o.get(k)}")
        if filled(o.get("yapi_tipi")):
            yt = YAPI_AD.get(fold(o.get("yapi_tipi")), o.get("yapi_tipi"))
            a.append(f"Yapı: {tr_cap(yt)}" + (f" ({o.get('site_adi')})" if filled(o.get("site_adi")) else ""))
        if o.get("esyali") is not None and o.get("esyali") != "":
            a.append(f"Eşya: {'Eşyalı' if yes(o.get('esyali')) else 'Eşyasız'}")
        if filled(i.get("kullanim_durumu")):
            a.append(f"Fiili kullanım: {KULLANIM_AD.get(fold(i.get('kullanim_durumu')), i.get('kullanim_durumu'))}")
        blocks.append(((tr_cap(i.alt_ad) if i.tip == "konut" else "İş yeri") + " bilgileri", a))
        odalar = [o for o in (i.get("odalar") or []) if isinstance(o, dict)]
        if odalar:
            blocks.append(("Bölümler (yaklaşık)", [f"{o.get('ad')}: {o.get('m2')} m²" + (f", {o.get('not')}" if o.get("not") else "")
                                                   for o in odalar]))
        don = i.get("ozellikler.donatilar")
        if isinstance(don, list):
            blocks.append(("Bina ve donatılar", [str(x) for x in don] or ["Ek donatı yok"]))
    k = []
    for e in i.get("ulasim") or []:
        k.append(f"{e.get('yer')}: {e.get('mesafe')}")
    for e in i.get("sosyal") or []:
        k.append(f"{e.get('yer')}: {e.get('mesafe')}")
    if k:
        blocks.append(("Konum ve yaklaşık mesafeler", k))
    t = []
    td = fold(i.get("tapu.durum", ""))
    if td:
        hs = i.get("tapu.hisse") or i.get("arsa.hisse")
        t.append(f"Tapu: {TAPU_AD.get(td, i.get('tapu.durum'))}" + (f" ({hs} hisse)" if td == "hisseli" and filled(hs) else ""))
    if not i.arsa and filled(i.get("tapu.iskan")):
        isk = fold(i.get("tapu.iskan"))
        t.append("Yapı kullanma izni (iskân): " + {"var": "Var", "yok": "Yok", "proje": "Proje aşamasında"}.get(isk, str(i.get("tapu.iskan"))))
    if filled(i.get("tapu.imar")):
        t.append(f"İmar: {i.get('tapu.imar')}")
    if filled(i.get("tapu.ipotek_haciz")):
        ih = str(i.get("tapu.ipotek_haciz"))
        t.append("İpotek/haciz: " + ("Yok" if no(ih) else ih))
    if filled(i.get("krediye_uygun")) and not i.arsa:
        t.append("Krediye uygunluk: " + ("Uygun (banka değerlendirmesine bağlı)" if yes(i.get("krediye_uygun")) else
                                          "Uygun değil" if no(i.get("krediye_uygun")) else str(i.get("krediye_uygun"))))
    if filled(i.get("enerji.sinif")):
        t.append(f"Enerji kimlik belgesi: {i.get('enerji.sinif')} sınıfı")
    elif no(i.get("enerji.belge")) and not i.arsa:
        t.append("Enerji kimlik belgesi: Yok")
    if t:
        blocks.append(("Tapu ve hukuki durum", t))
    return blocks


def _yn(v, evet="Var", hayir="Yok"):
    if yes(v):
        return evet
    if no(v):
        return hayir
    return str(v)


GEREKLI = "[GEREKLİ]"


def bad(i, rid):
    return getattr(i, "st", {}).get(rid) == "DUZELT"


def ybn(i):
    v = i.get("isletme.yetki_belgesi_no")
    return str(v) if filled(v) else GEREKLI


def fiyat_degisim_satiri(i):
    """Belgeli fiyat düşüşü metinde kalıyorsa: önceki fiyat (son 10 günün en düşüğü) + tarih."""
    if not getattr(i, "_indirim", False) or bad(i, "FYT-07"):
        return ""
    s10 = num(i.get("fiyat_gecmisi.son_10_gun_en_dusuk")) or num(i.get("fiyat_gecmisi.onceki_fiyat"))
    d1, d2 = parse_date(i.get("fiyat_gecmisi.degisim_tarihi")), parse_date(i.get("fiyat_gecmisi.gecerlilik_bitis"))
    fmt = lambda d: d.strftime("%d.%m.%Y")
    when = (f"{fmt(d1)} - {fmt(d2)} arasında geçerli" if d1 and d2 else f"{fmt(d1)} tarihinden itibaren geçerli" if d1 else "")
    return f"Önceki fiyat (son 10 günün en düşüğü): {tl(s10)} · Güncel: {tl(i.get('fiyat'))}" + (f" · {when}" if when else "")


def fiyat_satirlari(i):
    f = []
    if i.fiyat_str:
        if bad(i, "FYT-02"):
            f.append(f"Satış fiyatı: [TOPLAM BEDEL GEREKLİ] (girilen {tl(i.get('fiyat'))} toplam bedel değil)")
        elif i.tur == "satilik":
            kd = fold(i.get("kdv", ""))
            kdv = {"dahil": ", KDV dahil", "haric": ", KDV hariç", "hariç": ", KDV hariç"}.get(kd, "")
            f.append(f"Satış fiyatı: {tl(i.get('fiyat'))} (toplam bedel{kdv})")
        else:
            f.append(f"Aylık kira: {tl(i.get('fiyat'))}")
            if num(i.get("depozito")):
                f.append(f"Depozito: {tl(i.get('depozito'))}")
    if num(i.get("aidat")):
        f.append(f"Aidat: {tl(i.get('aidat'))} / ay")
    if filled(i.get("odeme_plani")):
        f.append(f"Ödeme: {i.get('odeme_plani')}")
    dg = fiyat_degisim_satiri(i)
    if dg:
        f.append(dg)
    km = i.get("komisyon.metin")
    if bad(i, "KMS-01"):
        f.append("Hizmet bedeli: [YASAL SINIRA ÇEKİLMELİ: satışta toplam %4 + KDV, kirada 1 aylık kira + KDV]")
    elif filled(km):
        f.append(f"Hizmet bedeli: {km}")
    return f


def zorunlu_satirlari(i):
    z = []
    if i.isletme:
        un = i.get("isletme.unvan")
        mk = i.get("isletme.marka")
        z.append(f"İşletme: {un if filled(un) else GEREKLI}" + (f" ({mk})" if filled(mk) and mk != un else ""))
        z.append(f"Yetki belgesi no: {ybn(i)}")
    loc = ", ".join(str(x) for x in (i.get("konum.il"), i.get("konum.ilce"), i.mahalle) if x)
    if loc:
        z.append(f"İl / ilçe / mahalle: {loc}")
    z.append(f"Ada / parsel: {i.get('konum.ada') or GEREKLI} / {i.get('konum.parsel') or GEREKLI}")
    tel = i.get("isletme.telefon") if i.isletme else i.get("iletisim.telefon")
    if filled(tel):
        z.append(f"İletişim: {tel}")
    if yes(i.get("eids.yetki_dogrulandi")):
        z.append("EİDS: İlan, taşınmaz sahibinin e-Devlet üzerinden verdiği ilan yayınlama izniyle yayımlanmaktadır.")
    else:
        z.append("EİDS: [İLAN YAYINLAMA İZNİ GEREKLİ — izin gelmeden yayınlamayın]")
    return z


def beyanlar(i):
    b = []
    yz = i.get("gorseller.yapay_zeka") or {}
    if isinstance(yz, dict) and yes(yz.get("kullanildi")) and bad(i, "GRS-01"):
        b.append("[Yapay zekâ ile taşınmazı değiştiren görseller çıkarılmalı; beyan bunu düzeltmez]")
    elif isinstance(yz, dict) and yes(yz.get("kullanildi")):
        neler = [fold(x) for x in (yz.get("neler") or [])]
        for n in neler:
            if n in YZ_BEYAN:
                b.append(YZ_BEYAN[n])
        if not b and not all(n in YZ_SERBEST for n in neler):
            b.append(YZ_BEYAN["diger"])
        if neler and all(n in YZ_SERBEST for n in neler):
            b.append("Fotoğraflarda yalnız ışık ve renk düzeltmesi yapılmıştır.")
    if yes(i.get("gorseller.temsili")):
        b.append("Proje görselleri temsilidir.")
    return b


def giris_cumlesi(i):
    mah = ek_de(i.mahalle) if i.mahalle else ""
    tur = tr_lower(i.tur_ad)
    if i.arsa:
        hs = i.get("arsa.hisse") or i.get("tapu.hisse")
        s = f"{mah} {tur}: {i.m2} m²" if i.m2 else f"{mah} {tur}"
        if filled(hs) and fold(hs) != "tam":
            s += f", {hs} hisse"
        elif fold(i.get("tapu.durum", "")) == "hisseli":
            s += f", hisseli (hisse oranı {GEREKLI})"
        return s.strip() + "."
    o = i.get("ozellikler") or {}
    bits = [i.m2_str.replace(" / ", ", ")]
    if o.get("kat") is not None:
        kat = o.get("kat")
        katx = f"{kat}. katı" if isinstance(kat, int) or str(kat).isdigit() else f"{tr_lower(kat)} katı"
        gen = YAPI_GEN.get(fold(o.get("yapi_tipi", "")), "binanın")
        bits.append(f"{o.get('kat_sayisi')} katlı {gen} {katx}" if o.get("kat_sayisi") else katx)
    s = f"{mah} {o.get('oda', '')} {tur}: " + ", ".join(b for b in bits if b) + "."
    return re.sub(r"\s+", " ", s).replace(" :", ":").strip()


def aciklama(i, platform, vurgular):
    blocks = bilgi_satirlari(i)
    fiyat = fiyat_satirlari(i)
    zor = zorunlu_satirlari(i)
    bey = beyanlar(i)
    lines = [giris_cumlesi(i), ""]
    if platform == "emlakjet":
        ozet = [x for x in (i.fiyat_str and f"Fiyat: {i.fiyat_str}", i.m2_str and f"Alan: {i.m2_str}", i.konum_str and f"Konum: {i.konum_str}") if x]
        lines += ["Özet:"] + [f"- {x}" for x in ozet] + [""]
    if vurgular:
        lines += ["Öne çıkanlar:"] + [f"- {v}" for v in vurgular] + [""]
    if getattr(i, "temiz_ek", ""):
        lines += [i.temiz_ek, ""]
    order = blocks
    if platform == "hepsiemlak":
        # tapu ve konum önce gelsin
        order = sorted(blocks, key=lambda b: 0 if b[0].startswith(("Tapu", "Konum")) else 1)
    for title, rows in order:
        if rows:
            lines += [f"{title}:"] + [f"- {r}" for r in rows] + [""]
    if fiyat:
        lines += ["Fiyat ve ödeme:" if i.tur == "satilik" else "Kira ve ödeme:"] + [f"- {r}" for r in fiyat] + [""]
    if bey:
        lines += ["Görseller hakkında:"] + [f"- {b}" for b in bey] + [""]
    if zor:
        lines += ["İlan bilgileri (Taşınmaz Ticareti Hakkında Yönetmelik m.14/2-i):"] + [f"- {z}" for z in zor]
    return "\n".join(lines).strip() + "\n"


def ozellik_listesi(i):
    o = i.get("ozellikler") or {}
    out = []
    if i.arsa:
        for path, ad in (("arsa.imar_durumu", "İmar"), ("arsa.yola_cephe", "Yola cephe"), ("arsa.altyapi", "Altyapı"),
                         ("arsa.ekili_dikili", "Ekili/dikili")):
            if filled(i.get(path)):
                out.append(f"{ad}: {_yn(i.get(path))}")
    else:
        if yes(o.get("asansor")):
            out.append("Asansör")
        if filled(o.get("otopark")) and not no(o.get("otopark")):
            out.append(str(o.get("otopark")) if not yes(o.get("otopark")) else "Otopark")
        if (num(o.get("balkon")) or 0) > 0:
            out.append("Balkon")
        if yes(o.get("esyali")):
            out.append("Eşyalı")
        if fold(o.get("yapi_tipi", "")) == "site":
            out.append("Site içerisinde")
        for d in o.get("donatilar") or []:
            if str(d) not in out:
                out.append(str(d))
        if filled(o.get("isitma")):
            out.append(f"Isıtma: {o.get('isitma')}")
    if filled(i.get("enerji.sinif")):
        out.append(f"Enerji sınıfı {i.get('enerji.sinif')}")
    return out


def form_alanlari(i):
    o = i.get("ozellikler") or {}
    f = [("Fiyat", tl(i.get("fiyat")))]
    if i.arsa:
        f += [("m²", i.m2), ("İmar durumu", i.get("arsa.imar_durumu")), ("Ada no", i.get("konum.ada")), ("Parsel no", i.get("konum.parsel")),
              ("Emsal", i.get("arsa.emsal")), ("Gabari", i.get("arsa.gabari")), ("Tapu durumu", TAPU_AD.get(fold(i.get("tapu.durum", "")), i.get("tapu.durum")))]
    else:
        f += [("m² (Brüt)", o.get("brut_m2")), ("m² (Net)", o.get("net_m2")), ("Oda sayısı", o.get("oda")), ("Bina yaşı", o.get("bina_yasi")),
              ("Bulunduğu kat", o.get("kat")), ("Kat sayısı", o.get("kat_sayisi")), ("Isıtma", o.get("isitma")), ("Banyo sayısı", o.get("banyo")),
              ("Balkon", "Var" if (num(o.get("balkon")) or 0) > 0 else "Yok"), ("Asansör", _yn(o.get("asansor"), "Var", "Yok") if o.get("asansor") is not None else None),
              ("Otopark", o.get("otopark")), ("Eşyalı", _yn(o.get("esyali"), "Evet", "Hayır") if o.get("esyali") is not None else None),
              ("Kullanım durumu", KULLANIM_AD.get(fold(i.get("kullanim_durumu", "")), i.get("kullanim_durumu"))),
              ("Site içerisinde", "Evet" if fold(o.get("yapi_tipi", "")) == "site" else "Hayır"), ("Site adı", o.get("site_adi")),
              ("Aidat (TL)", ival(i.get("aidat"))), ("Krediye uygun", _yn(i.get("krediye_uygun"), "Evet", "Hayır") if filled(i.get("krediye_uygun")) else None),
              ("Tapu durumu", TAPU_AD.get(fold(i.get("tapu.durum", "")), i.get("tapu.durum")))]
        if i.tur == "kiralik":
            f.append(("Depozito (TL)", ival(i.get("depozito"))))
    f.append(("Kimden", "Emlak ofisinden" if i.isletme else "Sahibinden"))
    return [(k, v) for k, v in f if v not in (None, "", [])]


def hashtags(i):
    tags = []
    for base in (i.get("konum.ilce"), f"{tr_lower(i.tur_ad)}", f"{i.get('konum.ilce') or ''}{tr_lower(i.tur_ad)}", "emlak"):
        if not base:
            continue
        t = "#" + re.sub(r"[^0-9a-zçğıöşü]", "", tr_lower(base))
        if len(t) > 2 and t not in tags:
            tags.append(t)
    return tags[:4]


def reel_plani(i, vurgular):
    sure = int(num(i.get("reels.sure_sn")) or 20)
    odalar = [o for o in (i.get("odalar") or []) if isinstance(o, dict)][:6]
    if i.arsa:
        shots = [{"ad": "Arsanın genel görünümü", "kamera": "drone ya da yüksek noktadan yavaş açılış (izin ve güvenlik kurallarına uyun)"},
                 {"ad": "Yol ve cephe", "kamera": "yol kenarından sabit, 5 sn"},
                 {"ad": "Sınır ve çevre", "kamera": "yavaş yatay kaydırma"}]
    else:
        shots = [{"ad": "Bina girişi / dış cephe", "kamera": "yürüyerek yaklaşma, sabit tutun"}]
        for o in odalar:
            ad = str(o.get("ad"))
            low = fold(ad)
            kam = ("yavaş ileri itme (push-in)" if "salon" in low or "ofis" in low or "toplant" in low else
                   "soldan sağa yavaş kaydırma" if "mutfak" in low else
                   "pencereden dışarı yavaş açılış" if "balkon" in low or "teras" in low else
                   "sabit, 5 sn bekleyin" if "banyo" in low or "wc" in low else "köşeden çapraz, sabit")
            shots.append({"ad": ad, "m2": o.get("m2"), "kamera": kam})
        man = str(i.get("ozellikler.manzara") or "")
        if man and not no(man) and not any("balkon" in fold(s["ad"]) for s in shots):
            shots.append({"ad": f"Manzara ({man})", "kamera": "pencereden yavaş açılış"})
    hook_s, end_s = 2.5, 3.0
    body = max(len(shots) - 1, 1)
    per = max(1.5, round((sure - hook_s - end_s) / body, 1))
    rows = []
    t = 0.0
    hook_txt = " · ".join(x for x in (i.oda, f"{i.m2} m²" if i.m2 else "", i.mahalle) if x)
    rows.append((t, t + hook_s, shots[0]["ad"], shots[0]["kamera"], f"{hook_txt}\n{i.tur_ad}"))
    t += hook_s
    kisa = ekran_beyani(i)
    for s in shots[1:] if len(shots) > 1 else []:
        label = s["ad"] + (f" · {s['m2']} m²" if s.get("m2") else "")
        if kisa and not s["ad"].startswith(("Bina girişi", "Manzara")):
            label += f"\n({kisa})"
        rows.append((t, t + per, s["ad"], s["kamera"], label))
        t += per
    rows.append((t, t + end_s, "Son kart", "son kare bulanık ve koyu, üstüne yazı", "SON_KART"))
    t += end_s
    return rows, round(t, 1)


def eids_ok(i):
    return yes(i.get("eids.yetki_dogrulandi")) and str(i.get("eids.ilan_linki") or "").startswith(("http://", "https://"))


def eids_ibare(i, kisa=False):
    """EİDS iddiası yalnız doğrulama + link varken yazılır; yoksa yer tutucu."""
    if eids_ok(i):
        return "EİDS doğrulamalı ilan" if kisa else "EİDS doğrulamalı ilan linki açıklamada"
    return "[EİDS İZNİ VE İLAN LİNKİ GEREKLİ]"


def fiyat_goster(i):
    return "[TOPLAM BEDEL GEREKLİ]" if bad(i, "FYT-02") else i.fiyat_str


def ekran_beyani(i):
    yz = i.get("gorseller.yapay_zeka") or {}
    out = []
    if isinstance(yz, dict) and yes(yz.get("kullanildi")) and not bad(i, "GRS-01"):
        for n in [fold(x) for x in (yz.get("neler") or [])]:
            if n in YZ_KISA:
                out.append(YZ_KISA[n])
            elif n not in YZ_SERBEST:
                out.append(YZ_KISA["diger"])
    if yes(i.get("gorseller.temsili")):
        out.append("Temsili görseldir")
    return " · ".join(dict.fromkeys(out))


def son_kart(i):
    s = [fiyat_goster(i), " · ".join(x for x in (i.oda, f"{i.m2} m²" if i.m2 else "", i.konum_str) if x)]
    if filled(i.get("eids.ilan_no")):
        s.append(f"İlan no: {i.get('eids.ilan_no')}")
    if i.isletme:
        s.append(f"{i.get('isletme.unvan') or GEREKLI} · Yetki belge no: {ybn(i)}")
        s.append(str(i.get("isletme.telefon") or ""))
    s.append(eids_ibare(i))
    return [x for x in s if x and x.strip(" ·")]


def ig_caption(i, vurgular):
    fy = "[TOPLAM BEDEL GEREKLİ]" if bad(i, "FYT-02") else i.fiyat_str
    lines = [f"{(i.oda + ' ') if i.oda else ''}{i.tur_ad} · {i.konum_str}", f"Fiyat: {fy}"]
    dg = fiyat_degisim_satiri(i)
    if dg:
        lines.append(dg)
    link = i.get("eids.ilan_linki")
    no_ = i.get("eids.ilan_no")
    lines.append("EİDS doğrulamalı ilan: " + (str(link) if filled(link) else "[İLAN LİNKİ GEREKLİ]") + (f" (ilan no {no_})" if filled(no_) else ""))
    lines.append("")
    facts = [x for x in (i.m2_str and f"{i.m2_str}", i.oda and f"{i.oda}", ) if x]
    if not i.arsa:
        o = i.get("ozellikler") or {}
        if o.get("kat") is not None:
            facts.append(f"{o.get('kat')}. kat")
        if o.get("bina_yasi") is not None:
            facts.append(f"{o.get('bina_yasi')} yaşında bina")
    else:
        if filled(i.get("arsa.imar_durumu")):
            facts.append(f"İmar: {i.get('arsa.imar_durumu')}")
        if filled(i.get("arsa.hisse")):
            facts.append(f"Hisse: {i.get('arsa.hisse')}")
    lines.append(" · ".join(facts))
    for v in vurgular[:3]:
        lines.append(f"- {v}")
    if num(i.get("aidat")):
        lines.append(f"Aidat: {tl(i.get('aidat'))} / ay")
    for b in beyanlar(i):
        lines.append(b)
    lines.append("")
    if i.isletme:
        lines.append(f"{i.get('isletme.unvan') or GEREKLI} · Yetki belge no: {ybn(i)}")
        lines.append(f"Ada/parsel: {i.get('konum.ada') or GEREKLI}/{i.get('konum.parsel') or GEREKLI} · {i.get('isletme.telefon') or ''}")
    lines.append(" ".join(hashtags(i)))
    if yes(i.get("reklam.ticari_iliski")):
        hes = i.get("isletme.instagram") or i.get("isletme.unvan") or "@isletme"
        lines.insert(0, f"Reklam | {hes} tarafından sağlandı.")
    return "\n".join(lines).strip() + "\n"


def carousel_plan(i, vurgular):
    hesap = i.get("carousel.hesap") or i.get("isletme.instagram") or ""
    sab = i.get("carousel.sablon") or "acik-editoryal"
    mah = i.mahalle
    baslik = f"*{i.m2} m²* {tr_lower(i.tur_ad)}" if i.m2 and not i.arsa else f"*{tr_lower(i.tur_ad)}*" if i.arsa else tr_lower(i.tur_ad)
    sl = []
    sl.append({"tip": "kanca", "ust": i.konum_str.split(" / ")[0], "sayi": (f"{i.m2} m²" if i.arsa and i.m2 else i.oda or (f"{i.m2} m²" if i.m2 else "1")),
               "baslik": baslik, "alt": f"{fiyat_goster(i)} · {eids_ibare(i, kisa=True)}"})
    ul = [f"{e.get('yer')}: {e.get('mesafe')}" for e in (i.get("ulasim") or [])][:2]
    so = [f"{e.get('yer')}: {e.get('mesafe')}" for e in (i.get("sosyal") or [])][:3]
    if ul or so:
        sl.append({"tip": "liste", "ust": "Yaklaşık mesafeler", "baslik": f"Konum: *{mah or i.get('konum.ilce')}*",
                   "maddeler": (ul + so)[:5], "isaret": "nokta"})
    blocks = dict(bilgi_satirlari(i))
    if i.arsa:
        rows = blocks.get("Arsa bilgileri", [])
        if rows:
            sl.append({"tip": "madde", "baslik": "Arsa *bilgileri*", "metin": ". ".join(rows[:4]) + "."})
    else:
        o = i.get("ozellikler") or {}
        ic = []
        if o.get("oda"):
            ic.append(f"{o.get('oda')} düzen")
        for k, ad in (("banyo", "banyo"), ("tuvalet", "tuvalet"), ("balkon", "balkon")):
            if (num(o.get(k)) or 0) > 0 and not (k == "tuvalet" and num(o.get("banyo"))):
                ic.append(f"{ival(o.get(k))} {ad}")
        if o.get("kat") is not None:
            ic.append(f"{o.get('kat')}. kat")
        if filled(o.get("cephe")):
            ic.append(f"{o.get('cephe')} cephe")
        odalar = [od for od in (i.get("odalar") or []) if isinstance(od, dict)][:3]
        if odalar:
            ic.append(", ".join(f"{od.get('ad')} {od.get('m2')} m²" for od in odalar))
        sl.append({"tip": "madde", "baslik": "İç *özellikler*", "metin": ". ".join(tr_cap(x) for x in ic) + "."})
        bina = []
        if filled(o.get("yapi_tipi")):
            bina.append(tr_cap(YAPI_AD.get(fold(o.get("yapi_tipi")), o.get("yapi_tipi"))))
        if o.get("bina_yasi") is not None:
            bina.append(f"{o.get('bina_yasi')} yaşında bina")
        don = [str(d) for d in (o.get("donatilar") or [])][:3]
        if don:
            bina.append(", ".join([don[0]] + [tr_lower(x[:1]) + x[1:] for x in don[1:]]))
        if bina:
            sl.append({"tip": "madde", "baslik": "Bina ve *donatılar*", "metin": ". ".join(bina) + "."})
    tapu = blocks.get("Tapu ve hukuki durum", [])
    if tapu:
        sl.append({"tip": "liste", "ust": "Hukuki durum", "baslik": "Tapu ve *imar*", "maddeler": tapu[:5], "isaret": "tik"})
    bilgi = [f"Fiyat: {'[TOPLAM BEDEL GEREKLİ]' if bad(i, 'FYT-02') else i.fiyat_str}"]
    if filled(i.get("eids.ilan_no")):
        bilgi.append(f"İlan no: {i.get('eids.ilan_no')}")
    if i.isletme:
        bilgi.append(f"Yetki belge no: {ybn(i)}")
    bilgi.append(f"Ada {i.get('konum.ada') or GEREKLI} / Parsel {i.get('konum.parsel') or GEREKLI}")
    if filled(i.get("enerji.sinif")):
        bilgi.append(f"Enerji sınıfı: {i.get('enerji.sinif')}")
    sl.append({"tip": "liste", "ust": "İlan bilgileri", "baslik": "Fiyat ve *belgeler*", "maddeler": bilgi[:5], "isaret": "nokta"})
    sl.append({"tip": "cta", "tur": "paylas", "baslik": "Ev arayan birine *gönder*" if i.tip == "konut" else "İhtiyacı olana *gönder*",
               "metin": eids_ibare(i) + "."})
    for s in sl:   # 2'den az maddeli liste okunmaz: madde slaytına çevir
        if s["tip"] == "liste" and len(s.get("maddeler", [])) < 2:
            s.update({"tip": "madde", "metin": ". ".join(s.pop("maddeler")) + "."})
            s.pop("isaret", None)
            s.pop("ust", None)
    sl = sl[:10]
    link = i.get("eids.ilan_linki") or "[İLAN LİNKİ GEREKLİ]"
    cap = {
        "kanca": f"{i.tur_ad} · {i.konum_str} · {'[TOPLAM BEDEL GEREKLİ]' if bad(i, 'FYT-02') else i.fiyat_str}",
        "maddeler": [x for x in ([i.m2_str, i.oda] + vurgular[:2]) if x],
        "cta": f"EİDS doğrulamalı ilan: {link}" + (f" · Yetki belge no: {i.get('isletme.yetki_belgesi_no')}" if i.isletme else ""),
        "anahtar_kelimeler": [x for x in (tr_lower(i.tur_ad), f"{i.get('konum.ilce') or ''} {tr_lower(i.alt_ad)}".strip(), "emlak ilanı") if x],
        "hashtagler": hashtags(i),
    }
    plan = {"konu": f"{ek_de(mah)} {tr_lower(i.tur_ad)}" if mah else i.tur_ad, "sablon": sab, "hesap": hesap,
            "seri": f"{i.tur_ad.split()[0]} · {i.get('konum.ilce') or ''}".strip(" ·"), "slaytlar": sl, "caption": cap,
            "reklam": None}
    if yes(i.get("reklam.ticari_iliski")):
        plan["reklam"] = {"tur": "Reklam", "veren": i.get("isletme.instagram") or i.get("isletme.unvan")}
    return plan


# ---------------------------------------------------------------- YAML yazıcı (bağımlılıksız)
def _q(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{s}"'


def to_yaml(obj, ind=0):
    sp = "  " * ind
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, dict) and v:
                out.append(f"{sp}{k}:")
                out.append(to_yaml(v, ind + 1))
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                out.append(f"{sp}{k}:")
                for it in v:
                    first = True
                    for kk, vv in it.items():
                        pre = f"{sp}  - " if first else f"{sp}    "
                        first = False
                        if isinstance(vv, list):
                            out.append(f"{pre}{kk}: [{', '.join(_q(x) for x in vv)}]")
                        elif isinstance(vv, dict):
                            out.append(f"{pre}{kk}:")
                            out.append(to_yaml(vv, ind + 3))
                        else:
                            out.append(f"{pre}{kk}: {_q(vv)}")
            elif isinstance(v, list):
                out.append(f"{sp}{k}: [{', '.join(_q(x) for x in v)}]")
            elif isinstance(v, dict):
                out.append(f"{sp}{k}: {{}}")
            else:
                out.append(f"{sp}{k}: {_q(v)}")
    return "\n".join(x for x in out if x != "")


def reklam_girdisi(i, caption, reel_rows, sure):
    yz = i.get("gorseller.yapay_zeka") or {}
    neler = []
    for n in (yz.get("neler") or []) if isinstance(yz, dict) else []:
        n = fold(n)
        neler.append({"sanal_mobilya": "urun_gorseli", "render": "urun_gorseli", "gokyuzu": "arka_plan",
                      "isik_renk": "duzenleme"}.get(n, "urun_gorseli"))
    ticari = yes(i.get("reklam.ticari_iliski"))
    d = {
        "platform": "instagram", "bicim": "reels",
        "hesap_turu": "icerik_uretici" if ticari else "marka_kendi",
        "yayin_tarihi": i.yayin.isoformat(),
        "ticari_iliski": "evet" if ticari else "hayir",
        "iliski_turu": ["ucret"] if ticari else [],
        "reklam_veren": i.get("isletme.unvan") or "",
        "reklam_veren_hesap": i.get("isletme.instagram") or "",
        "urun_kategorisi": "hizmet",
        "platform_ortaklik_etiketi": "hayir",
        "urunu_deneyimledi": "evet",
        "filtre": "hayir",
        "aciklama": caption,
        "ekran_yazilari": [{"metin": (r[4] if r[4] != "SON_KART" else " · ".join(son_kart(i)[:2])).replace("\n", " "),
                            "baslangic": round(r[0], 1), "bitis": round(r[1], 1), "konum": "orta"} for r in reel_rows],
        "seslendirme": "",
        "sure_sn": sure,
        "parca_sayisi": 1,
        "her_parcada_etiket": "evet",
        "yapay_zeka": {"kullanildi": "evet" if isinstance(yz, dict) and yes(yz.get("kullanildi")) else "hayir",
                       "neler": sorted(set(neler)), "gercek_kisi_kopyasi": "hayir"},
    }
    d["ekran_yazilari"].insert(0, {"metin": f"{fiyat_goster(i)} · {eids_ibare(i)}", "baslangic": 0, "bitis": sure, "konum": "ust"})
    if ticari:
        d["ekran_yazilari"].insert(0, {"metin": f"REKLAM · {i.get('isletme.instagram') or i.get('isletme.unvan')}",
                                       "baslangic": 0, "bitis": sure, "konum": "ust"})
    if getattr(i, "_indirim", False):
        d["indirim"] = {
            "indirimli_fiyat": ival(i.get("fiyat")), "onceki_fiyat": ival(i.get("fiyat_gecmisi.onceki_fiyat")),
            "son_10_gun_en_dusuk": ival(i.get("fiyat_gecmisi.son_10_gun_en_dusuk")),
            "baslangic": str(i.get("fiyat_gecmisi.degisim_tarihi") or ""), "bitis": str(i.get("fiyat_gecmisi.gecerlilik_bitis") or ""), "stok_adedi": None,
            "urun_turu": "mal", "satis_kanali": str(i.get("fiyat_gecmisi.kanal") or "ilan platformu"),
            "onceki_fiyat_kanali": str(i.get("fiyat_gecmisi.onceki_kanal") or i.get("fiyat_gecmisi.kanal") or "ilan platformu"),
        }
    d["cocuk"] = {"hedef_kitle": "hayir", "oynuyor": "hayir"}
    d["hedefleme"] = {"cocuk_profilleme": "hayir"}
    d["karsilastirma"] = {"rakip_adi_var": "hayir"}
    return d


def find_reklam_etiketi(arg):
    if arg == "kapali":
        return None
    if arg and arg != "otomatik":
        p = Path(arg).expanduser()
        if p.is_dir():
            p = p / "scripts" / "kontrol.py"
        return p if p.is_file() else None
    for c in (Path.home() / ".claude" / "skills" / "reklam-etiketi" / "scripts" / "kontrol.py",
              SKILL_DIR.parent / "reklam-etiketi" / "scripts" / "kontrol.py"):
        if c.is_file():
            return c
    return None


# ---------------------------------------------------------------- rapor
def render_report(den, ilan, rules, tarih, ekler=None):
    i, items = ilan, den.sorted_items()
    c = den.counts()
    L = [f"# Emlak ilanı kontrol raporu", "", f"**{DISCLAIMER}**", "",
         f"- İlan: {i.tur_ad} · {i.konum_str} · {i.fiyat_str or 'fiyat yok'}",
         f"- Kanallar: {', '.join(i.kanallar)} · Yayın tarihi: {i.yayin.isoformat()} · Kontrol tarihi: {tarih.isoformat()}",
         f"- Kural dosyası: sürüm {rules.data.get('surum')}, kaynaklar {rules.data.get('kural_tarihi')} tarihinde okundu", "",
         f"## Sonuç: {den.verdict()}", "",
         "| DÜZELT | UZMANA SOR | UYARI | GÖZLE KONTROL | BİLGİ | GEÇTİ | UYGULANMAZ |", "|---|---|---|---|---|---|---|",
         "| " + " | ".join(str(c[k]) for k in DURUM_SIRA) + " |", ""]
    act = [it for it in items if it["durum"] in ("DUZELT", "UZMANA_SOR", "UYARI", "MANUEL")]
    if act:
        L += ["## Yapılacaklar", ""]
        for it in sorted(act, key=lambda x: DURUM_SIRA.index(x["durum"])):
            L += [f"### [{DURUM_ETIKET[it['durum']]}] {it['id']} · {it['baslik']}", "",
                  f"- **Bulgu:** {it['bulgu']}", f"- **Ne yapmalı:** {' '.join(it['duzeltme'].split())}",
                  f"- **Dayanak:** {it['dayanak']} (güven: {GUVEN_AD[it['guven']]})"]
            for o in it.get("oneri", []):
                L.append(f"- **Öneri:** {o}")
            if it.get("belirsizlik"):
                L.append(f"- **Belirsizlik:** {it['belirsizlik']}")
            L.append("")
    if den.cikarilan:
        L += ["## Metne alınmayan vurgular", "", "Aşağıdaki ifadeler üretilen ilan metinlerine konmadı:", ""]
        L += [f"- {x}" for x in den.cikarilan] + [""]
    if ekler:
        L += ["## Ek dosyalar", ""] + [f"- {e}" for e in ekler] + [""]
    L += ["## Tüm kontroller", "", "| Kod | Kontrol | Durum | Güven |", "|---|---|---|---|"]
    for it in items:
        L.append(f"| {it['id']} | {it['baslik']} | {DURUM_ETIKET[it['durum']]} | {GUVEN_AD[it['guven']]} |")
    L += ["", "## EİDS takvimi (bilgi)", ""]
    for e in rules.data.get("eids_takvim", []):
        L.append(f"- {e['tarih']}: {e['olay']}" + (" **[kaynaklar çelişkili]**" if e.get("belirsiz") else "") + f" ({e['kaynak']})")
    L += ["", "Bu kit daha sıkı yorumu uygular: bugün her ilan türü ve her kanal için EİDS yetki doğrulaması şart sayılır.", "",
          "## İdari para cezası aralıkları (bilgi)", ""]
    for cz in rules.data.get("cezalar", []):
        L += [f"- **{cz['kim']}**", f"  - Dayanak: {cz['dayanak']}", f"  - Kanundaki tutar: {cz['nominal']}",
              f"  - 2026: {cz['yil_2026']}" + (" (yeniden değerleme oranlarıyla hesaplandı; Bakanlığın ilan ettiği tablo bulunamadı)" if cz.get("hesaplanmis") else "")]
        if cz.get("tekrar"):
            L.append(f"  - {cz['tekrar']}")
        if cz.get("ornekler"):
            L.append(f"  - Uygulama örnekleri: {cz['ornekler']}")
    L += ["", "## Kaynaklar", ""]
    for k in rules.data.get("kaynaklar", []):
        L.append(f"- [{k['id']}] {k['belge']}. {k['url']} (belge tarihi {k['tarih']}, okunma {k['okunma']})")
    L += ["", "---", "", f"**{DISCLAIMER}** Mevzuat ve Bakanlık uygulaması değişebilir; yayından önce Resmî Gazete ve "
          "Ticaret Bakanlığı duyurularını kontrol edin. Emin olmadığınız durumda bir avukata ya da ticaret il müdürlüğüne danışın.", ""]
    return "\n".join(L)


def report_json(den, ilan, rules, tarih):
    return {
        "uyari": DISCLAIMER, "sonuc": den.verdict(), "sayilar": den.counts(), "kontrol_tarihi": tarih.isoformat(),
        "yayin_tarihi": ilan.yayin.isoformat(), "kural_surumu": rules.data.get("surum"), "kural_tarihi": rules.data.get("kural_tarihi"),
        "kontroller": den.sorted_items(), "metne_alinmayan": den.cikarilan,
    }


# ---------------------------------------------------------------- komutlar
def run_check(spec_path, rules, tarih):
    d = load_data(spec_path)
    if not isinstance(d, dict):
        raise ValueError("girdi bir YAML/JSON sözlüğü olmalı")
    ilan = Ilan(d, tarih)
    den = Denetim(ilan, rules)
    den.run()
    ilan.st = {k: v["durum"] for k, v in den.items.items()}
    ilan._indirim = den.indirim
    temizle(ilan, rules, den)
    titles = basliklar(ilan, rules)
    den.platform_titles(titles)
    ilan._indirim = den.indirim
    return ilan, den, titles


def cmd_kontrol(a, rules):
    tarih = parse_date(a.tarih) or _dt.date.today()
    ilan, den, _ = run_check(a.ilan, rules, tarih)
    md = render_report(den, ilan, rules, tarih)
    if a.cikti:
        Path(a.cikti).write_text(md, encoding="utf-8")
        print(f"rapor: {a.cikti}")
    else:
        print(md)
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(report_json(den, ilan, rules, tarih), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"SONUÇ: {den.verdict()}", file=sys.stderr)
    return 1 if den.counts()["DUZELT"] else 0


def cmd_uret(a, rules):
    tarih = parse_date(a.tarih) or _dt.date.today()
    ilan, den, titles = run_check(a.ilan, rules, tarih)
    out = Path(a.cikti)
    out.mkdir(parents=True, exist_ok=True)
    vur = ilan.temiz_vurgular
    taslak = den.counts()["DUZELT"] > 0
    banner = ("> **TASLAK — YAYINLAMAYIN.** Rapordaki DÜZELT maddeleri giderilmeden bu metinler hiçbir kanalda "
              "kullanılmamalı (rapor.md).\n\n") if taslak else ""
    ekler = []
    # 1) portal metinleri
    P = {}
    md = [f"# Portal ilan metinleri", "", f"_{DISCLAIMER} Metinleri yayınlamadan önce bilgileri tapu ve sözleşmeyle karşılaştırın._", "", banner]
    for p in PLATFORMS:
        pc = rules.platform.get(p, {})
        desc = aciklama(ilan, p, vur)
        feats = ozellik_listesi(ilan)
        P[p] = {"baslik": titles[p], "aciklama": desc, "ozellikler": feats, "form_alanlari": form_alanlari(ilan)}
        md += [f"## {pc.get('ad', p)}", "", f"**Başlık** ({len(titles[p])}/{pc.get('baslik_max')} karakter)", "", "```text", titles[p], "```", "",
               f"**Açıklama** ({len(desc)} karakter)", "", "```text", desc.rstrip(), "```", "",
               "**Özellik listesi** (panelde işaretlenecek kutular)", ""] + [f"- {x}" for x in feats] + ["",
               "**Form alanları** (tipik alan adları; panelde eşleştirin)", "", "| Alan | Değer |", "|---|---|"]
        md += [f"| {k} | {v} |" for k, v in P[p]["form_alanlari"]] + ["", f"_Not: {pc.get('not', '')} Platform sınırları panelde doğrulanmadı (güven: düşük)._", ""]
    md += ["---", "", f"_{DISCLAIMER}_", ""]
    (out / "ilanlar.md").write_text("\n".join(md), encoding="utf-8")
    ekler.append("ilanlar.md: Sahibinden, Hepsiemlak, Emlakjet başlık + açıklama + özellik listesi + form alanları")
    # 2) Instagram
    if ilan.sosyal:
        rows, sure = reel_plani(ilan, vur)
        cap = ig_caption(ilan, vur)
        sk = son_kart(ilan)
        ig = [f"# Instagram planı", "", f"_{DISCLAIMER}_", "", banner,
              "## Reels (9:16, 1080x1920)", "",
              f"- Süre: ~{sure} sn. Kesimler müziğin vuruşlarında; her çekimde 5 sn sabit duruş çekin (kesimde kısaltılır).",
              f"- **Kalıcı rozet (tüm video boyunca, sol üst):** `{fiyat_goster(ilan)} · {eids_ibare(ilan)}`",
              "- Yazılar güvenli alanda kalsın: üstten ~250 px, alttan ~440 px boşluk (arayüz ve altyazı alanı).",
              "- Görüntüler yalnız bu taşınmazdan (EİDS-04). Müzik: lisanslı ya da Instagram kütüphanesi (işletme hesabında kütüphane sınırlı olabilir).", ""]
        bey = beyanlar(ilan)
        if bey:
            ig.append(f"- **Görsel beyanı (ilgili görüntülerin üstünde ve açıklamada):** {' '.join(bey)}")
            ig.append("")
        ig += ["| Zaman | Çekim | Kamera | Ekran yazısı |", "|---|---|---|---|"]
        for r in rows:
            txt = r[4] if r[4] != "SON_KART" else "<br>".join(sk)
            ig.append(f"| {r[0]:.1f}–{r[1]:.1f} sn | {r[2]} | {r[3]} | {txt.replace(chr(10), '<br>')} |")
        ig += ["", "### Son kart", "", "```text"] + sk + ["```", "", "### Kapak yazısı", "", "```text",
               f"{ilan.oda + ' · ' if ilan.oda else ''}{ilan.tur_ad}", f"{ilan.konum_str}", fiyat_goster(ilan), "```", "",
               "## Açıklama (reels ve carousel için)", "", "```text", cap.rstrip(), "```", "",
               "Instagram açıklamadaki link tıklanmaz: ilan linkini profil bağlantısına ya da hikâye bağlantı çıkartmasına da ekleyin.", "",
               "## Hikâye (story) metni", "", "```text", f"{ilan.tur_ad} · {ilan.mahalle or ilan.konum_str}", fiyat_goster(ilan),
               "EİDS doğrulamalı ilan için bağlantıya dokunun" if eids_ok(ilan) else eids_ibare(ilan), "```", "", "---", "", f"_{DISCLAIMER}_", ""]
        (out / "instagram.md").write_text("\n".join(ig), encoding="utf-8")
        ekler.append("instagram.md: reels çekim planı + ekran yazıları + son kart + açıklama + story")
        if not a.carousel_yok:
            plan = carousel_plan(ilan, vur)
            head = [f"# {DISCLAIMER}", "# Türkçe Carousel Üretici planı (github.com/redirhan/turkce-carousel):",
                    "#   carousel.py kontrol carousel_plan.yaml && carousel.py render carousel_plan.yaml --cikti carousel/",
                    "# Fiyat, EİDS linki ve yetki belge no slaytlardan ve açıklamadan çıkarılmamalı." + (" TASLAK: önce rapor.md'deki DÜZELT maddeleri." if taslak else ""), ""]
            (out / "carousel_plan.yaml").write_text("\n".join(head) + to_yaml(plan) + "\n", encoding="utf-8")
            ekler.append("carousel_plan.yaml: Türkçe Carousel Üretici planı (7-8 slayt + açıklama)")
        need_rek = den.indirim or "GRS-01" in den.items and den.items["GRS-01"]["durum"] in ("UYARI", "DUZELT") or yes(ilan.get("reklam.ticari_iliski"))
        if need_rek:
            rk = reklam_girdisi(ilan, cap, rows, sure)
            (out / "reklam_kontrol.yaml").write_text(f"# {DISCLAIMER}\n# Reklam Etiketi Kontrolü girdisi (github.com/redirhan/reklam-etiketi)\n"
                                                     + to_yaml(rk) + "\n", encoding="utf-8")
            ekler.append("reklam_kontrol.yaml: Reklam Etiketi Kontrolü girdisi (indirim / yapay zekâ / iş birliği)")
            kp = find_reklam_etiketi(a.reklam_etiketi)
            if kp:
                res = subprocess.run([sys.executable, str(kp), str(out / "reklam_kontrol.yaml"), "--cikti", str(out / "reklam_rapor.md"),
                                      "--tarih", tarih.isoformat(), "--ocr", "kapali"], capture_output=True, text=True)
                ekler.append(f"reklam_rapor.md: Reklam Etiketi Kontrolü sonucu (çıkış kodu {res.returncode}; 1 = DÜZELT var)")
            else:
                ekler.append("Reklam Etiketi Kontrolü bulunamadı ya da kapalı; çalıştırmak için: "
                             "python3 ~/.claude/skills/reklam-etiketi/scripts/kontrol.py reklam_kontrol.yaml")
    md = render_report(den, ilan, rules, tarih, ekler)
    (out / "rapor.md").write_text(md, encoding="utf-8")
    js = report_json(den, ilan, rules, tarih)
    js["metinler"] = {p: {"baslik": P[p]["baslik"], "aciklama": P[p]["aciklama"], "ozellikler": P[p]["ozellikler"]} for p in PLATFORMS}
    (out / "rapor.json").write_text(json.dumps(js, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = [e.split(":")[0] for e in ekler if e.split(":")[0].endswith((".md", ".yaml"))]
    print(f"çıktı: {out}/ ({', '.join(files + ['rapor.md', 'rapor.json'])})")
    print(f"SONUÇ: {den.verdict()}")
    return 1 if taslak else 0


SABLON_ORTAK = """# Emlak İlan Kiti — ilan girdisi
# {disc}
# Bilmediğiniz alanı 'bilinmiyor' yazın; uydurmayın. Açık adres (sokak, kapı no) hiçbir alana yazılmaz.
ilan_turu: {tur}            # satilik | kiralik
emlak_tipi: {tip}           # konut | is_yeri | arsa
alt_tip: {alt}              # daire | villa | mustakil | rezidans | ofis | dukkan | depo | arsa | tarla | bag_bahce
ilan_veren: isletme         # isletme | sahibi
yayin_tarihi: "2026-11-03"
kanallar: [portal, instagram]   # portal = Sahibinden/Hepsiemlak/Emlakjet; instagram = reels + carousel
fiyat:                      # satılıkta TOPLAM satış bedeli, kiralıkta aylık kira (TL, sayı)
fiyat_turu: toplam          # toplam | pesinat | baslangic  (yalnız 'toplam' geçer)
para_birimi: TL
kdv: bilinmiyor             # dahil | haric | yok | bilinmiyor  (yeni bina / müteahhit / iş yeri satışı)
aidat:
depozito:                   # kiralık
konum:
  il: ""
  ilce: ""
  mahalle: ""
  ada: ""
  parsel: ""
"""
SABLON_BINA = """ozellikler:
  brut_m2:
  net_m2:
  oda: ""                   # konut "3+1"; iş yerinde bölüm sayısı
  banyo:
  tuvalet:
  balkon:
  kat:
  kat_sayisi:
  bina_yasi:
  isitma: ""
  cephe: ""
  manzara: ""               # yoksa "yok"
  yapi_tipi: apartman       # apartman | site | mustakil | plaza | is_hani | is_merkezi | diger
  site_adi: ""
  asansor: hayir
  otopark: ""
  esyali: hayir
  donatilar: []             # ["Kapıcı", "Kapalı otopark"]; boş liste = ek donatı yok
odalar:                     # yaklaşık büyüklükler (m.15/3-f) ve reels çekim listesi
  - {ad: "Salon", m2: }
tapu:
  durum: kat_mulkiyeti      # kat_mulkiyeti | kat_irtifaki | hisseli | mustakil | tapusuz
  hisse: ""
  iskan: bilinmiyor         # var | yok | proje | bilinmiyor
  ipotek_haciz: bilinmiyor  # yok | açıklama
krediye_uygun: bilinmiyor   # evet | hayir | bilinmiyor
kullanim_durumu: ""         # bos | kiracili | mal_sahibi
enerji:
  belge: bilinmiyor         # var | yok
  sinif: ""                 # A-G
"""
SABLON_ARSA = """arsa:
  alan_m2:
  imar_durumu: ""           # ör. "Konut alanı" ya da "İmar yok (tarım arazisi)"
  emsal: ""                 # imarsızsa "yok"
  gabari: ""                # öngörülen bina yüksekliği; imarsızsa "yok"
  hisse: ""                 # tam ise "tam", değilse "1/4" gibi
  ekili_dikili: ""          # "yok" ya da "12 zeytin ağacı"
  yola_cephe: ""
  altyapi: ""
tapu:
  durum: arsa               # arsa | tarla | hisseli
  ipotek_haciz: bilinmiyor
kullanim_durumu: ""         # boş, tarım yapılıyor...
"""
SABLON_SON = """ulasim:                     # toplu taşıma durakları (m.15/3-d), ölçerek yazın
  - {yer: "", mesafe: ""}
sosyal:                     # okul, hastane, park, çarşı (m.15/3-e)
  - {yer: "", mesafe: ""}
isletme:
  unvan: ""                 # yetki belgesinde yazan ad/unvan
  marka: ""
  yetki_belgesi_no: ""
  telefon: ""
  instagram: ""
yetkilendirme:
  sozlesme: bilinmiyor      # evet | hayir
  bitis: ""                 # yetki/izin bitiş tarihi YYYY-AA-GG
eids:
  yetki_dogrulandi: bilinmiyor   # evet | hayir  (e-Devlet ilan yayınlama izni geldi mi?)
  ilan_no: ""
  ilan_linki: ""            # sosyal medya için zorunlu (önce portalda yayınlayın)
komisyon:
  toplam_oran:              # satış: toplam hizmet bedeli %, KDV hariç (sınır 4)
  toplam_ay:                # kira: toplam hizmet bedeli, ay (sınır 1)
  metin: ""                 # ilanda yazılacaksa: "Alıcıdan %2 + KDV"
fiyat_gecmisi:              # yalnız fiyat değiştiyse
  onceki_fiyat:
  son_10_gun_en_dusuk:
  degisim_tarihi: ""
  gecerlilik_bitis: ""      # varsa
  kanal: ""
  indirim_vurgusu: hayir
gorseller:
  bu_tasinmaza_ait: evet
  temsili: hayir
  yapay_zeka:
    kullanildi: hayir
    neler: []               # sanal_mobilya | gokyuzu | render | isik_renk | yapi_degisikligi | manzara
reklam:
  ticari_iliski: hayir      # bir içerik üretici para/hediye karşılığı paylaşıyorsa evet
  paylasan_hesap: ""
vurgular: []                # ölçülebilir, doğru ifadeler: "Tramvay durağına 350 m"
ek_aciklama: ""
baslik_vurgu: ""            # başlıkta tek öne çıkan özellik (boşsa kit seçer)
reels: {sure_sn: 20}
carousel: {sablon: acik-editoryal, hesap: ""}
"""


def cmd_sablon(a):
    t = a.tur
    if t == "satilik-daire":
        tur, tip, alt, body = "satilik", "konut", "daire", SABLON_BINA
    elif t == "kiralik-ofis":
        tur, tip, alt, body = "kiralik", "is_yeri", "ofis", SABLON_BINA
    else:
        tur, tip, alt, body = "satilik", "arsa", "arsa", SABLON_ARSA
    sys.stdout.write(SABLON_ORTAK.format(disc=DISCLAIMER, tur=tur, tip=tip, alt=alt) + body + SABLON_SON)
    return 0


def cmd_doctor(rules_path):
    ok = True
    print(f"Emlak İlan Kiti — doctor\n{DISCLAIMER}\n")
    v = sys.version_info
    print(f"{'ok ' if v >= (3, 8) else 'HATA'} Python {v.major}.{v.minor}.{v.micro} (3.8+ gerekir)")
    ok &= v >= (3, 8)
    try:
        import yaml  # type: ignore  # noqa
        print("ok  PyYAML var")
    except ImportError:
        print("ok  PyYAML yok; dahili YAML okuyucu kullanılacak")
    try:
        r = Rules(rules_path)
        errs = r.validate()
        print(f"{'ok ' if not errs else 'HATA'} kural dosyası: {len(r.by_id)} kural, sürüm {r.data.get('surum')}, kaynak tarihi {r.data.get('kural_tarihi')}")
        for e in errs[:10]:
            print("     " + e)
        ok &= not errs
    except Exception as e:  # noqa
        print(f"HATA kural dosyası okunamadı: {e}")
        return 2
    with tempfile.TemporaryDirectory() as td:
        spec = Path(td) / "t.yaml"
        spec.write_text(SABLON_ORTAK.format(disc=DISCLAIMER, tur="satilik", tip="konut", alt="daire") + SABLON_BINA + SABLON_SON, encoding="utf-8")
        try:
            _, den, _ = run_check(spec, r, _dt.date(2026, 10, 27))
            print(f"ok  boş şablon denetlendi ({den.counts()['DUZELT']} DÜZELT bekleniyor, sonuç: {den.verdict()})")
        except Exception as e:  # noqa
            print(f"HATA şablon denetlenemedi: {e}")
            ok = False
    print(f"ok  Türkçe: {tr_upper('istanbul ılıca')} / {ek_de('Caferağa')}, {ek_de('Kadıköy')}, {ek_de('Etimesgut')}")
    kp = find_reklam_etiketi("otomatik")
    print(f"{'ok ' if kp else 'not'} Reklam Etiketi Kontrolü: " + ("bulundu" if kp else "kurulu değil (isteğe bağlı: github.com/redirhan/reklam-etiketi)"))
    tc = Path.home() / ".claude" / "skills" / "turkce-carousel" / "scripts" / "carousel.py"
    print(f"{'ok ' if tc.is_file() else 'not'} Türkçe Carousel Üretici: " + ("bulundu" if tc.is_file() else "kurulu değil (isteğe bağlı: github.com/redirhan/turkce-carousel)"))
    print("ok  ağ, hesap, ücretli API ve tarayıcı kullanılmaz")
    print("\nHAZIR" if ok else "\nSORUN VAR")
    return 0 if ok else 2


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ilan.py", description="Emlak İlan Kiti — " + DISCLAIMER)
    ap.add_argument("--kurallar", default=str(DEFAULT_RULES))
    sub = ap.add_subparsers(dest="komut")
    sub.add_parser("doctor", help="kurulum kontrolü")
    s = sub.add_parser("sablon", help="boş ilan girdisi")
    s.add_argument("--tur", choices=["satilik-daire", "kiralik-ofis", "arsa"], default="satilik-daire")
    k = sub.add_parser("kontrol", help="yalnız kontrol raporu")
    k.add_argument("ilan")
    k.add_argument("--cikti")
    k.add_argument("--json", dest="json_out")
    k.add_argument("--tarih", help="kontrol tarihi YYYY-AA-GG (varsayılan bugün)")
    u = sub.add_parser("uret", help="metinler + planlar + rapor")
    u.add_argument("ilan")
    u.add_argument("--cikti", required=True)
    u.add_argument("--tarih")
    u.add_argument("--carousel-yok", action="store_true")
    u.add_argument("--reklam-etiketi", default="otomatik", help="otomatik | kapali | kontrol.py yolu")
    sub.add_parser("kurallari-dogrula", help="kural dosyasını denetle")
    a = ap.parse_args(argv)
    if a.komut == "doctor":
        return cmd_doctor(a.kurallar)
    if a.komut == "sablon":
        return cmd_sablon(a)
    if not a.komut:
        ap.print_help()
        return 2
    try:
        rules = Rules(a.kurallar)
    except Exception as e:  # noqa
        print(f"kural dosyası okunamadı: {e}", file=sys.stderr)
        return 2
    if a.komut == "kurallari-dogrula":
        errs = rules.validate()
        for e in errs:
            print("HATA " + e)
        print(f"{len(rules.by_id)} kural, {len(rules.data.get('kaynaklar', []))} kaynak: " + ("geçerli" if not errs else f"{len(errs)} hata"))
        return 1 if errs else 0
    try:
        if a.komut == "kontrol":
            return cmd_kontrol(a, rules)
        if a.komut == "uret":
            return cmd_uret(a, rules)
    except (ValueError, FileNotFoundError) as e:
        print(f"girdi hatası: {e}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
