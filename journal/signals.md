# Signallogg

Format per signal:

```
## [#ID] YYYY-MM-DD HH:MM — SYMBOL (tidsram)
Signal:      KÖP / SÄLJ / AVVAKTA
Entry:       ...
Stop Loss:   ...
Take Profit: ...
R/R:         ...
Setup:       ...
Status:      given / tagen / ej tagen
```

---

<!-- Nya signaler läggs till nedanför denna rad, senaste överst -->

## [#4] 2026-07-17 ~16:35 UTC — GULD GC1! (1h, COMEX)
Signal:      SÄLJ vid motstånd (limit) — endast intradag pga fredagskväll
Entry:       4 055 (zon 4 052–4 062)
Stop Loss:   4 086
Take Profit: 4 000
R/R:         ~1.8
Setup:       1h-nedtrend: lägre toppar 4 140 (10/7) → 4 085 (15/7). Veckans största
             fall sedan juni (inflations-/ränteoro) = säljarnas marknad. Stödzonen
             3 975–4 000 har hållit 3+ ggr och priset studsade nyss till 4 025 —
             mitt i rangen, ingen trade där. Entry vid omtest av motståndet
             4 055–4 060, med trenden.
Ogiltig om:  1h-candle stänger över 4 062 → strukturskifte, stå platt.
             Då gäller istället omvänt scenario: KÖP rekyl mot 4 055–4 060 med
             mål 4 100 (reclaim av 4 000 + brott av lower high = botten kan vara satt).
VIKTIGT:     COMEX stänger 21:00 UTC för helgen. Ingen position över helgen —
             Mellanöstern-eskalering kan gappa guld UPPÅT över SL (safe haven).
             Ej fylld före ~19:30 UTC → dra ordern. Fylld men ej i mål → stäng före 21:00.
Status:      ANNULLERAD — fel bildunderlag (endast 1h, 4h-kontext saknades).
             Ersätts av ny analys med korrekta skärmdumpar. Lägg INTE denna order.

## [#2] 2026-07-16 ~19:20 UTC — BTCUSD (1h, Bitstamp)
Signal:      KÖP vid stödzon (limit)
Entry:       63 950 (zon 63 850–64 050)
Stop Loss:   63 550
Take Profit: TP1 64 800 (ta hälften + flytta SL till breakeven), TP2 65 300
R/R:         ~2.1 till TP1, ~3.4 till TP2
Setup:       1h-bilden är konstruktiv: dubbelbotten 61 700/61 800 (9/7 & 14/7) följt av
             stark impuls till 65 500 (15/7). Nuvarande nedgång är en rekyl i den rörelsen.
             Entryzonen = intradagsstödet 63 850–64 000 + 38–50% retracement av rallyt
             (38,2% ≈ 64 100, 50% ≈ 63 650). SL under 50%-nivån.
Ogiltig om:  1h-candle stänger under 63 600 → rekylen är djupare, nästa zon 62 800–63 000.
Status:      avslutad — SL träffad (på pappret −1R), oklart om användaren tog den
Utfall 17/7: Priset föll rakt genom entryzonen (fill ~63 950) och genom SL 63 550
             under natten/morgonen, fortsatte till ~62 600. Nedgången var nyhetsdriven
             (risk-off: USA–Iran, Hormuz, chipsell-off) — stödet höll inte.
             Lärdom: 3:e–4:e testet av ett stöd + nyhetsrisk = mindre position eller avstå.

## [#3] 2026-07-17 ~13:25 UTC — BTCUSD (1h + 15m, Bitstamp)
Signal:      SÄLJ vid pullback (limit)
Entry:       63 150 (zon 63 100–63 300)
Stop Loss:   63 650
Take Profit: 62 150 (strax ovanför huvudstödet 61 900–62 100)
R/R:         ~2.0–2.3
Setup:       Nedtrend på både 1h och 15m efter brott av 63 600. Studsen till 63 300
             (15m, ~12:00 UTC) avvisades = lägre topp. Entry på omtest av brottszonen,
             SL ovanför avvisningstoppen. Macro-medvind för short: risk-off-våg
             (Iran/Hormuz/chip-rout) — men nyhetsdrivet = risk för våldsamma squeezes
             åt båda håll vid deeskalering. Kör mindre position än normalt.
Ogiltig om:  15m-candle stänger över 63 500 → strukturen har vänt, stå platt.
Nästa setup: KÖP vid 61 900–62 100 (stort 1h-stöd, testat 9/7 & 13–14/7) — men endast
             med tydlig reaktion, ingen stående limit i nyhetsdrivet fall.
Status:      TAGEN — fylld ~14:00 UTC → trade #1 i trades.csv
Order:       Short 63 132 / SL 63 653 / TP 62 166 / storlek 6 (dubblad från 3)
             Risk ~3 090 USD, reward ~5 830 USD → R/R ~1.85

## [#1] 2026-07-16 ~17:20 UTC — BTCUSD (15m, Bitstamp)
Signal:      AVVAKTA → villkorat KÖP vid stöd
Entry:       64 000 (limit vid stödzonen 63 900–64 050, kräver avvisningsreaktion)
Stop Loss:   63 750
Take Profit: 64 600
R/R:         ~2.4 (risk 250 / reward 600)
Setup:       Range-dag utan makrokatalysator. Dubbelbotten 63 900–64 000 tidigare idag,
             range-topp 64 800 avvisad hårt. Pris föll i mitten av rangen vid signal
             (64 145) — ingen entry i fallande kniv, köp endast vid reaktion på stödet.
Ogiltig om:  15m-candle stänger under 63 900 → setup avblåst (då är range-botten bruten).
Status:      avslutad — TP nådd, ej tagen av användaren (ingen trade loggad)
Utfall:      Priset studsade på stödzonen och nådde TP 64 600 (+2.4R på pappret).
Uppdatering 17:31 UTC: Pris 64 206, wick ner till ~64 150 — entryzonen ej nådd än.
             Bredare bild visar lägre toppar från 65 500 (15/7) → 64 800: 15m-strukturen
             är en nedtrend, och stödet 63 850–63 900 har redan testats 3 ggr.
             Setup intakt men taktisk: ta inte entry utan tydlig reaktion, och
             flytta SL till breakeven snabbt om den fylls.
