"""Emlak İlan Kiti birim testleri (python3 -m unittest discover -s tests).
Bu bir hukuki görüş değildir; bilgilendirme amaçlıdır."""
import copy
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ilan  # noqa: E402
import mini_yaml  # noqa: E402

TARIH = dt.date(2026, 10, 27)
EX = ROOT / "examples"


def check(d):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "i.json"
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        return ilan.run_check(p, ilan.Rules(), TARIH)


def base():
    return mini_yaml.load(EX / "01-satilik-daire" / "ilan.yaml")


def durum(den, rid):
    return den.items[rid]["durum"]


class Kurallar(unittest.TestCase):
    def test_kural_dosyasi_gecerli(self):
        self.assertEqual(ilan.Rules().validate(), [])

    def test_her_kuralda_kaynak_tarih_guven(self):
        for r in ilan.Rules().data["kurallar"]:
            self.assertIn(r["guven"], ("yuksek", "orta", "dusuk"), r["id"])
            for k in r["kaynak"]:
                self.assertTrue(k["url"].startswith("https://"), r["id"])
                self.assertTrue(ilan.parse_date(k["tarih"]) and ilan.parse_date(k["okunma"]), r["id"])

    def test_pyyaml_ile_ayni(self):
        try:
            import yaml  # noqa
        except ImportError:
            self.skipTest("PyYAML yok")
        text = (ROOT / "rules" / "kurallar.yaml").read_text(encoding="utf-8")
        self.assertEqual(json.dumps(yaml.safe_load(text), sort_keys=True, default=str),
                         json.dumps(mini_yaml.loads(text), sort_keys=True, default=str))


class Turkce(unittest.TestCase):
    def test_bulunma_eki(self):
        self.assertEqual(ilan.ek_de("Bostanlı"), "Bostanlı'da")
        self.assertEqual(ilan.ek_de("Kadıköy"), "Kadıköy'de")
        self.assertEqual(ilan.ek_de("Etimesgut"), "Etimesgut'ta")
        self.assertEqual(ilan.ek_de("Çeşme"), "Çeşme'de")
        self.assertEqual(ilan.ek_de("Kızılay"), "Kızılay'da")

    def test_buyuk_harf(self):
        self.assertEqual(ilan.tr_upper("istanbul ılıca"), "İSTANBUL ILICA")

    def test_flow_map(self):
        d = mini_yaml.loads('odalar:\n  - {ad: "Salon", m2: 32, not: "güney, batı"}\n')
        self.assertEqual(d["odalar"][0], {"ad": "Salon", "m2": 32, "not": "güney, batı"})

    def test_tl(self):
        self.assertEqual(ilan.tl(8750000), "8.750.000 TL")
        self.assertEqual(ilan.num("1.250.000"), 1250000)


class Denetim(unittest.TestCase):
    def test_uyumlu_ornekler_duzelt_yok(self):
        for name in ("01-satilik-daire", "02-kiralik-ofis"):
            _, den, _ = ilan.run_check(EX / name / "ilan.yaml", ilan.Rules(), TARIH)
            self.assertEqual(den.counts()["DUZELT"], 0, name)

    def test_uyumsuz_ornek_beklenen_bulgular(self):
        _, den, _ = ilan.run_check(EX / "03-arsa-uyumsuz" / "ilan.yaml", ilan.Rules(), TARIH)
        duz = {k for k, v in den.items.items() if v["durum"] == "DUZELT"}
        for rid in ("EIDS-01", "EIDS-02", "EIDS-03", "EIDS-04", "YTK-01", "ZRN-02", "ZRN-11", "FYT-02", "FYT-07",
                    "KMS-01", "KMS-02", "YNL-01", "YNL-02", "YNL-03", "GRS-01"):
            self.assertIn(rid, duz)

    def test_eids_yoksa_duzelt(self):
        d = base()
        d["eids"]["yetki_dogrulandi"] = "bilinmiyor"
        _, den, _ = check(d)
        self.assertEqual(durum(den, "EIDS-01"), "DUZELT")

    def test_sosyal_medyada_link_zorunlu(self):
        d = base()
        d["eids"]["ilan_linki"] = ""
        _, den, _ = check(d)
        self.assertEqual(durum(den, "EIDS-02"), "DUZELT")
        d["kanallar"] = ["portal"]
        _, den, _ = check(d)
        self.assertEqual(durum(den, "EIDS-02"), "UYGULANMAZ")

    def test_fiyat_icin_dm(self):
        d = base()
        d["vurgular"] = ["Fiyat için DM atın"]
        _, den, _ = check(d)
        self.assertEqual(durum(den, "EIDS-03"), "DUZELT")

    def test_komisyon_siniri(self):
        d = base()
        d["komisyon"] = {"toplam_oran": 4}
        _, den, _ = check(d)
        self.assertEqual(durum(den, "KMS-01"), "GECTI")
        d["komisyon"] = {"toplam_oran": 4.5}
        _, den, _ = check(d)
        self.assertEqual(durum(den, "KMS-01"), "DUZELT")
        k = mini_yaml.load(EX / "02-kiralik-ofis" / "ilan.yaml")
        k["komisyon"] = {"toplam_ay": 2}
        _, den, _ = check(k)
        self.assertEqual(durum(den, "KMS-01"), "DUZELT")

    def test_acik_adres(self):
        d = base()
        d["ek_aciklama"] = "Adres: Lale Sokak No: 12 Daire: 5"
        _, den, _ = check(d)
        self.assertEqual(durum(den, "ZRN-01"), "DUZELT")

    def test_iddia_celiskisi(self):
        d = base()
        d["vurgular"] = ["Sıfır bina, deniz manzaralı"]
        _, den, _ = check(d)
        self.assertEqual(durum(den, "YNL-02"), "DUZELT")
        self.assertTrue(any("Sıfır bina" in x for x in den.cikarilan))

    def test_yetki_suresi_bitmis(self):
        d = base()
        d["yetkilendirme"]["bitis"] = "2026-10-01"
        _, den, _ = check(d)
        self.assertEqual(durum(den, "YTK-04"), "DUZELT")

    def test_belgesiz_indirim(self):
        d = base()
        d["vurgular"] = ["Fiyat düştü"]
        _, den, _ = check(d)
        self.assertEqual(durum(den, "FYT-07"), "DUZELT")

    def test_komisyon_yuzdesi_indirim_sayilmaz(self):
        d = base()
        _, den, _ = check(d)
        self.assertEqual(durum(den, "FYT-07"), "UYGULANMAZ")

    def test_baslik_sinirda(self):
        for name in ("01-satilik-daire", "02-kiralik-ofis", "03-arsa-uyumsuz"):
            rules = ilan.Rules()
            _, _, titles = ilan.run_check(EX / name / "ilan.yaml", rules, TARIH)
            for p, t in titles.items():
                self.assertLessEqual(len(t), rules.platform[p]["baslik_max"], (name, p, t))


class Cikti(unittest.TestCase):
    def run_uret(self, name):
        td = tempfile.mkdtemp()
        rc = ilan.main(["uret", str(EX / name / "ilan.yaml"), "--cikti", td, "--tarih", "2026-10-27",
                        "--reklam-etiketi", "kapali"])
        return rc, Path(td)

    def test_her_ciktida_uyari(self):
        for name in ("01-satilik-daire", "03-arsa-uyumsuz"):
            _, out = self.run_uret(name)
            for f in out.iterdir():
                self.assertIn(ilan.DISCLAIMER, f.read_text(encoding="utf-8"), f.name)

    def test_dogrulanmamis_ilanda_eids_iddiasi_yok(self):
        rc, out = self.run_uret("03-arsa-uyumsuz")
        self.assertEqual(rc, 1)
        ig = (out / "instagram.md").read_text(encoding="utf-8")
        self.assertNotIn("EİDS doğrulamalı ilan linki açıklamada", ig)
        self.assertNotIn("450.000 TL", ig)  # peşinat fiyat gibi gösterilmez
        car = (out / "carousel_plan.yaml").read_text(encoding="utf-8")
        self.assertNotIn("EİDS doğrulamalı ilan\"", car)
        ilanlar = (out / "ilanlar.md").read_text(encoding="utf-8")
        self.assertIn("TASLAK", ilanlar)
        for bad in ("imar gelecek", "değer kazanacak", "Deniz manzaralı", "gösterme bedeli"):
            self.assertNotIn(bad.lower(), ilanlar.lower().split("## sahibinden", 1)[1])

    def test_uyumlu_ciktida_zorunlu_bilgiler(self):
        rc, out = self.run_uret("01-satilik-daire")
        self.assertEqual(rc, 0)
        t = (out / "ilanlar.md").read_text(encoding="utf-8")
        for s in ("Yetki belgesi no: 3500123", "Ada / parsel: 4521 / 17", "İzmir, Karşıyaka, Bostanlı", "8.750.000 TL",
                  "yapay zekâ ile yerleştirilmiştir"):
            self.assertIn(s, t)
        ig = (out / "instagram.md").read_text(encoding="utf-8")
        self.assertIn("https://example.com/ilan/1234567890", ig)
        self.assertIn("8.750.000 TL · EİDS doğrulamalı ilan linki açıklamada", ig)
        self.assertTrue((out / "reklam_kontrol.yaml").is_file())

    def test_carousel_plan_formati(self):
        _, out = self.run_uret("02-kiralik-ofis")
        plan = mini_yaml.load(out / "carousel_plan.yaml")
        self.assertTrue(5 <= len(plan["slaytlar"]) <= 10)
        self.assertEqual(plan["slaytlar"][0]["tip"], "kanca")
        self.assertEqual(plan["slaytlar"][-1]["tip"], "cta")
        self.assertLessEqual(len(plan["caption"]["hashtagler"]), 4)
        for s in plan["slaytlar"]:
            if s["tip"] == "liste":
                self.assertTrue(2 <= len(s["maddeler"]) <= 6)


if __name__ == "__main__":
    unittest.main()
