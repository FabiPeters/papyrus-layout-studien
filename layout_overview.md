# Layout-Überblick – 2026-07-07

Datenquelle: `layout_data.json`

## Gesamtüberblick

- Platten: 15
- Kolumnen gesamt: 62 (davon nutzbar: 55)
- Fragmente gesamt: 4
- Kolumnen mit erfassten Zeilen: 10 (ohne Zeilendaten: 52)
- Zeilen gesamt: 457
- Ø Zeilen pro Kolumne: 45.7
- Zeilen pro Kolumne (min / max): 25 / 53

> Ø, min und max beziehen sich nur auf Kolumnen mit erfassten Zeilen. Fragmente (z. B. Platte T) werden separat gezaehlt und fliessen nicht in die Kolumnen-Statistik ein. Höhe/Breite (cm) sind aus den Bbox-Pixelmaßen und der px/cm-Skala abgeleitet (— ohne Skala oder bei mehreren Fragmenten). Ø Neigung = mittlere Kolumnenneigung der nutzbaren Kolumnen gegen drei Referenzen: die Bild-Senkrechte (vert.), die plattenweite Ideal-Horizontale aus den Oberkanten (ideal) und die Schrifthorizontale der jeweiligen Kolumne aus ihren Baselines (baseline, Johnson-Methode; nur wo Zeilen erfasst sind, sonst —). Schiefe = geschätzte Plattenschiefe aus den Oberkanten; Baseline-Schiefe = plattenweite Schrifthorizontale aus den Baselines (Kontrolle zur Oberkanten-Schiefe, in Klammern die Zahl der Kolumnen mit Zeilen). Neigung positiv = untere Kante nach links. Teile = Zahl zusammenhängender Maskenteile (Fragmentierungsmaß: 1 = zusammenhängendes Blatt, >1 = physisch getrennte Stücke; — im manuellen Bbox-Modus). Auf stark fragmentierten Platten (viele unbenutzbare Kolumnen, Teile > 1) sind die Neigungswinkel nur mit geringer Konfidenz zu lesen.

## Pro Platte

| Platte | Kolumnen | nutzbar | Fragmente | Teile | Höhe (cm) | Breite (cm) | Zeilen gesamt | Ø Zeilen/Kol | min | max | Ø Neig. vert. (°) | Ø Neig. ideal (°) | Ø Neig. baseline (°) | Schiefe (°) | Baseline-Schiefe (°) |
|--------|---------:|--------:|----------:|------:|----------:|------------:|--------------:|-------------:|----:|----:|------------------:|------------------:|---------------------:|------------:|---------------------:|
| A | 6 | 5 | 0 | 1 | 29.1 | 44.5 | 278 | 46.3 | 25 | 53 | 2.7 | 1.9 | 1.6 | 0.84 | 1.14 (5) |
| B | 4 | 4 | 0 | 1 | 29.2 | 34.0 | 179 | 44.8 | 44 | 46 | 3.1 | 2.2 | 1.9 | 0.91 | 1.24 (4) |
| C | 4 | 4 | 0 | 1 | 29.9 | 34.6 | 0 | — | — | — | 4.0 | 3.7 | — | 0.29 | — |
| D | 4 | 4 | 0 | 1 | 30.1 | 35.0 | 0 | — | — | — | 3.1 | 3.1 | — | -0.04 | — |
| E | 4 | 4 | 0 | 1 | 30.5 | 34.0 | 0 | — | — | — | 3.0 | 2.8 | — | 0.20 | — |
| F | 4 | 4 | 0 | 1 | 30.4 | 34.5 | 0 | — | — | — | 2.1 | 1.9 | — | 0.24 | — |
| G1 | 3 | 2 | 0 | 1 | 30.4 | 25.6 | 0 | — | — | — | 2.2 | 1.6 | — | 0.60 | — |
| H | 11 | 11 | 0 | — | — | — | 0 | — | — | — | 2.3 | 2.5 | — | -0.17 | — |
| N2 | 2 | 2 | 0 | 2 | 31.0 | 17.2 | 0 | — | — | — | 2.6 | 3.0 | — | -0.46 | — |
| O | 4 | 4 | 0 | 1 | 31.5 | 34.1 | 0 | — | — | — | 2.2 | 1.7 | — | 0.44 | — |
| P | 4 | 4 | 0 | 1 | 30.7 | 33.7 | 0 | — | — | — | 1.6 | 1.2 | — | 0.39 | — |
| Q | 4 | 4 | 0 | 1 | 31.2 | 34.3 | 0 | — | — | — | 2.1 | 1.4 | — | 0.79 | — |
| R | 5 | 2 | 0 | 3 | 26.8 | 33.7 | 0 | — | — | — | 0.7 | 1.4 | — | -0.73 | — |
| S | 3 | 1 | 0 | 3 | 30.6 | 20.7 | 0 | — | — | — | 0.7 | 1.1 | — | -0.36 | — |
| T | 0 | 0 | 4 | 4 | — | — | 0 | — | — | — | — | — | — | — | — |
