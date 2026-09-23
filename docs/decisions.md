# Beslutslogg

Nya beslut läggs till överst. Ändra inte gamla beslut, skriv ett nytt som ersätter.

## 2026-09-23 — En dagsbar räknas först när datumet slagit om i New York

Ersätter rättelsen nedan och `SETTLE_DELAY`.

Diagnos på användarens dator 2026-09-23 08:57 UTC: Yahoo levererade ingen bar alls för
2026-09-22 (DIA-svaret slutade 2026-09-21). Raden för 2026-09-22 som hämtades kvällen
innan, 17:43 New York-tid, var alltså en preliminär bar som Yahoo bygger av
realtidskurser och sedan tar bort över natten. Den var också den enda inkonsistenta
datan på 16 år för 55 symboler. De två tidigare förklaringarna (för tidig hämtning
med sex timmars marginal, respektive fel i Yahoos slutliga data) var fel.

Regel (`FINAL_BAR` i `schema.py`): en version av en dagsbar är slutgiltig bara om den
sparades på ett senare kalenderdatum i New York än barens eget datum, dvs. från ca
06:00 svensk tid dagen efter.

- Ingest sparar bara slutgiltiga barer.
- `latest_bars()` ignorerar versioner som inte är slutgiltiga, så de preliminära
  raderna från 2026-09-22 som redan ligger sparade används inte. Inget raderas.
- `data update` skriver en OBS-rad när en symbol saknar senaste förväntade börsdag.
  Förväntad börsdag räknas som vardag; amerikanska helgdagar känns inte till och kan
  ge en falsk OBS-rad dagen efter en helgdag.
- Reparationen i Yahoo-adaptern (`MAX_RANGE_REPAIR`) behålls som skyddsnät, men den
  har inte visats behövas för slutgiltig data.

## 2026-09-23 — Rättelse: Yahoos öppningskurs utanför dagens intervall

Felen från 2026-09-22 (open över high för DIA, GS, UNH, DIS) fanns kvar med identiska
värden efter omhämtning dagen efter. Orsaken var alltså inte att datan hämtades för
tidigt, som antogs i beslutet nedan, utan ett fel i Yahoos egen data. Yahoo-adaptern
vidgar nu high/low så att de omfattar open och close när avvikelsen är högst 1 % av
kursen (`MAX_RANGE_REPAIR`). Större avvikelser lämnas orörda och flaggas av
kvalitetskontrollen.

Väntetiden efter stängning (`SETTLE_DELAY`) sänks från sex timmar till en timme.
Sex timmar byggde på det felaktiga antagandet att Yahoo rättar dagsbaren i efterhand;
i praktiken hindrade den bara användaren från att hämta gårdagen före 04:00 svensk tid.
`data update` skriver nu ut senaste sparade börsdag, så att en utelämnad dag syns.

## 2026-09-22 — Konventioner för marknadsdata (fas 1)

- **Tidsstämplar:** en dagsbar har `known_at` = ordinarie stängning 16:00 New York-tid
  den dagen. Dagar med tidig stängning räknas också som 16:00, vilket bara gör datan
  senare känd, aldrig tidigare. `ingested_at` är när raden sparades.
- **Ofärdiga dagar sparas inte.** En bar sparas först sex timmar efter stängning
  (`SETTLE_DELAY`). Första riktiga körningen visade att Yahoos dagsbar direkt efter
  stängning kan vara felaktig (öppning över dagens högsta).
- **Stegvis uppdatering:** utan `--start` hämtas bara från tio dagar före senast
  sparade bar, så att leverantörens sena korrigeringar ersätter tidigare versioner.
- **Versioner:** senaste `ingested_at` vinner per instrument och datum. Versionen väljs
  innan as-of-filtreringen, så en senare korrigering (t.ex. ny splitjustering) används
  för alla datum. Det är ett medvetet val för splitjusterad leverantörsdata.
- **Priser:** splitjusterade, inte utdelningsjusterade. Prisfilter som "pris > 5 USD"
  blir något fel före en split; det hanteras när universe-filtret byggs.
- **Instrument-ID:** genereras av oss (`ins_…`) och kopplas till källa + symbol i ett
  register. Med gratisdata går det inte att upptäcka när en ticker återanvänds av ett
  annat bolag; det löses när vi byter till en källa med permanenta ID:n.
- **Lagring:** Parquet-filer läses med Polars. DuckDB läggs till när frågorna kräver
  det.
- **Yahoo är bara för utveckling.** Ingen avnoterad data, alltså survivorship bias.
  Källa för riktig forskning väljs innan fas 2.

## 2026-09-22 — Grundbeslut

| Fråga | Beslut |
|---|---|
| Marknad | Amerikanska aktier först |
| Konto | ISK hos Nordnet, ordrar läggs manuellt |
| Positionsstorlek | ca 2 000–15 000 kr |
| Användarens dator | Windows 11 |
| Databudget | Inte bestämd. Fas 1 byggs leverantörsoberoende; källa väljs innan fas 2 |
| Arkitektur | Enligt `docs/architecture.md` |

### Konsekvens: kostnader väger tungt

Med positioner på 2 000–15 000 kr i USD-aktier blir de fasta kostnaderna stora i
förhållande till risken per trade:

- Valutaväxling vid köp och sälj (Nordnet tar en avgift per växling, ofta runt 0,25 %
  beroende på prisnivå).
- Courtage med minimiavgift, som slår hårdast på små positioner.
- Spread och slippage.

Exempel: en trade med stopp 5 % under entry har 1R = 5 % av positionen. Kostar
rundturen 1 % motsvarar det 0,2R per trade, vilket kan äta upp hela edgen.

Därför:

- Kostnadsmodellen är en egen, konfigurerbar modul med användarens faktiska
  courtageklass och växlingsavgift. Värdena fylls i från Nordnets prislista.
- Riskmotorn blockerar trades där kostnaden överstiger en gräns i andel av R.
- Alla backtester körs med kostnader, och med dubbla kostnader som stresstest.
- Färre och större positioner är att föredra framför många små.

### Konsekvens: Windows

Norgate Data kräver en Windows-app och passar därför. Datainhämtning från Norgate
körs då på användarens dator och skriver Parquet-filer som resten av systemet läser.
