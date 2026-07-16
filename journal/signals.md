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
Status:      given / väntar på entry
Uppdatering 17:31 UTC: Pris 64 206, wick ner till ~64 150 — entryzonen ej nådd än.
             Bredare bild visar lägre toppar från 65 500 (15/7) → 64 800: 15m-strukturen
             är en nedtrend, och stödet 63 850–63 900 har redan testats 3 ggr.
             Setup intakt men taktisk: ta inte entry utan tydlig reaktion, och
             flytta SL till breakeven snabbt om den fylls.
