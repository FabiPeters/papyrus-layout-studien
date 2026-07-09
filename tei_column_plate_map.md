# TEI-Kolumnen ↔ Platten – P. 9782 (TM 62580)

Quelle: `xml/TM_62580.xml` (papyri.info, TEI). Erstellt: 2026-06-25, aktualisiert: 2026-07-09.

Zuordnung der durchnummerierten Kolumnen der Haupt-Edition (`<div subtype="column">`) zu den Platten. Verknuepfungsschluessel sind die `corresp`-FR-IDs: in `custodialHist` verweist jede `FR####` ueber `graphic` auf eine Platten-Bilddatei, in den Kolumnen-divs auf dieselbe FR-ID. Die Platten G1 und N2 sind in `custodialHist` nicht verlinkt; ihre Kolumnen wurden anhand der PAGE-XML manuell zugeordnet.

Haupt-Edition: **75 Kolumnen** (FR7070–FR7528).

## Zuordnung pro Platte

| Platte | TEI-Kol. # | # Kol. | # Transkribus | Quelle | Abgleich |
|--------|-----------|------:|--------------:|--------|:--------:|
| A | 1–6 | 6 | 6 | custodialHist | ✓ |
| B | 7–10 | 4 | 4 | custodialHist | ✓ |
| C | 11–14 | 4 | 4 | custodialHist | ✓ |
| D | 15–18 | 4 | 4 | custodialHist | ✓ |
| E | 19–22 | 4 | 4 | custodialHist | ✓ |
| F | 23–26 | 4 | 4 | custodialHist | ✓ |
| G1 | 27–29 | 3 | 3 | manuell | ✓ |
| H | 42–52 | 11 | 11 | custodialHist | ✓ |
| N2 | 53–54 | 2 | 2 | manuell | ✓ |
| O | 55–58 | 4 | 4 | custodialHist | ✓ |
| P | 59–62 | 4 | 4 | custodialHist | ✓ |
| Q | 63–66 | 4 | 4 | custodialHist | ✓ |
| R | 67–71 | 5 | 5 | custodialHist | ✓ |
| S | 73–75 | 3 | 3 | custodialHist | ✓ |

Fuer alle gelisteten Platten stimmt die Kolumnenzahl mit den Transkribus-Daten ueberein. „custodialHist" = ueber die TEI-`custodialHist` verlinkt; „manuell" = anhand der PAGE-XML von Hand zugewiesen (G1, N2).

## Noch nicht zugeordnete Kolumnen

13 Kolumnen besitzen FR-IDs, die in `custodialHist` keine `graphic`-Verknuepfung haben und (noch) keiner Platte zugeordnet sind:

- **Kol. 30–41, 72**
- FR-IDs: FR7099, FR7100, FR7101, FR7102, FR7103, FR7104, FR7105, FR7106, FR7107, FR7108, FR7109, FR7110, FR7525

(Die vormals ebenfalls nicht zugeordneten Kol. 27–29 und 53–54 wurden inzwischen manuell G1 bzw. N2 zugewiesen.)

## Abdeckung

- Platten via custodialHist: A, B, C, D, E, F, H, O, P, Q, R, S
- Platten manuell zugeordnet (nicht in custodialHist): G1, N2
- Ohne Kolumnen-Zuordnung: T (enthaelt nur Fragmente)

Hinweis: Den 75 Hauptkolumnen folgen im TEI nachgestellte Einzelfragmente (`<div subtype="fragment">`, FR7529–FR7548); Fragment C enthaelt zwei eigene Kolumnen. Diese sind hier nicht mitgezaehlt.
