# Beslutslogg

Nya beslut läggs till överst. Ändra inte gamla beslut, skriv ett nytt som ersätter.

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
