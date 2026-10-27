# Real-Estate Listing Kit for Turkey (Claude Code skill)

Enter a property's facts once; Claude writes the title, description and feature list for **Sahibinden, Hepsiemlak and
Emlakjet**, an **Instagram Reels shot plan** (on-screen texts, persistent price badge, end card, caption) and a
**carousel plan**, and checks the listing against Turkish real-estate advertising rules **before** it goes live:
**EİDS** (the Ministry of Trade's Electronic Listing Verification System) and the **Regulation on Real Estate Trade**
(Taşınmaz Ticareti Hakkında Yönetmelik).

Free, MIT licensed, by Redirhan Studio. Runs fully locally: no publishing, no portal or Instagram login, no paid APIs,
no browser. Python standard library only. Output texts are Turkish.

> **Not legal advice; for information only** ("Bu bir hukuki görüş değildir; bilgilendirme amaçlıdır" opens and closes
> every output).

![carousel example](examples/01-satilik-daire/carousel_onizleme.jpg)

## What it does

- **Portal texts** for three Turkish portals: short title, sectioned description, feature checkboxes, form-field table.
  Built only from the facts you enter; it never invents features.
- **Mandatory-info block** in every description (Reg. art. 14/2-i): licence (yetki belgesi) number, business name as on
  the licence, province/district/neighbourhood, block/parcel (ada/parsel; never the street address), contact, energy
  class, EİDS line.
- **Instagram**: room-by-room Reels shot list, a persistent `price · EİDS-verified listing link in caption` badge, end
  card, cover, caption with price + EİDS link + licence number, story text; on-screen AI disclosure for virtually
  staged photos.
- **Carousel plan** in the [turkce-carousel](https://github.com/redirhan/turkce-carousel) format.
- **Compliance report**: 42 rules, each with article number, source link, document date, read date and a confidence
  level. If anything blocks publication, texts are marked "DRAFT, DO NOT PUBLISH" with `[GEREKLİ]` placeholders, and
  risky phrases ("zoning is coming", "DM for price", a "sea view" the facts do not support) are kept out of the copy.
- **Ad rules**: documented price drops, AI images or paid partnerships produce an input file for the free
  [reklam-etiketi](https://github.com/redirhan/reklam-etiketi) checker (run automatically when installed).

## Install and use

```bash
cp -R emlak-ilan ~/.claude/skills/
python3 ~/.claude/skills/emlak-ilan/scripts/ilan.py doctor
S=~/.claude/skills/emlak-ilan/scripts
python3 $S/ilan.py sablon --tur satilik-daire > ilan.yaml     # or kiralik-ofis | arsa
python3 $S/ilan.py uret ilan.yaml --cikti out/
```

Exit code 1 means at least one blocking (DÜZELT) finding. Examples: `examples/` (sale flat, office for rent, and a
deliberately non-compliant plot of land with 18 blocking findings).

## Uncertain rules

Where sources conflict the stricter rule is encoded and flagged: EİDS start dates for sale listings (1 Feb 2026
nationwide vs. three pilot provinces, then 15 Feb 2026; no date found for land) — the kit requires EİDS for every
listing and channel today (Ministry statement, 22 Aug 2026); fine amounts (Law 6585 art. 18(1)(i): TRY 10,000-300,000
in the statute, TRY 28,620-858,620 computed for 2026 with the official revaluation rates; no Ministry table found);
whether art. 15(3) details must appear in the listing; where the link goes on social media; whether the discount rule
applies to agents; foreign-currency prices; portal title limits (could not be verified without a login).

## License

MIT (`LICENSE`), © 2026 Redirhan Studio.
