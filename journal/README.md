# Trade Journal & Signaler

Detta är journalen för trades och signaler. Arbetsflöde:

## Så funkar det

1. **Du skickar en skärmdump** av en chart (gärna med symbol och tidsram synlig).
2. **Claude analyserar** och svarar med en signal i detta format:

   ```
   SIGNAL: KÖP / SÄLJ / AVVAKTA
   Symbol:      ...
   Tidsram:     ...
   Entry:       ...
   Stop Loss:   ...
   Take Profit: ...
   R/R:         ...
   Setup:       (kort motivering – vilken strategi/struktur som används)
   ```

3. **Signalen loggas** i `signals.md`.
4. **När du tar en trade** säger du till ("tog den", "in på X") – den loggas i `trades.csv`.
5. **När traden stängs** säger du resultatet ("TP", "SL", "stängde på X") – journalen uppdateras och statistiken räknas om.

## Filer

| Fil | Innehåll |
|-----|----------|
| `signals.md` | Alla signaler som getts, med motivering |
| `trades.csv` | Tagna trades med entry/SL/TP och utfall |
| `stats.md` | Löpande statistik: winrate, snitt-R, per setup |

## Regler

- Varje signal har alltid Entry, Stop Loss och Take Profit. Inga undantag.
- Signaler med R/R under ~1.5 flaggas eller ges som AVVAKTA.
- Strategi väljs utifrån vad charten visar (struktur, S/R, trend, momentum) – det som passar situationen.

> Obs: Signalerna är teknisk analys av chartbilder, inte finansiell rådgivning. Du fattar besluten.
