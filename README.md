# papyrus-layout-studien

Automatische Analyse von PAGE-XML-Layoutdaten von Papyrusfragmenten mit besonderem Augenmerk auf Maas's Law (Schrägheit der Kolumnen)

Für die Erstellung der Pythonskripte und ihrer Dokumentation wurde zuerst die Hilfe des KI-Modells Claude Haiku 4.5 verwendet. Die Skripte und ihre Dokumentation wurden allerdings ab Juni 2026 vollständig mit Claude Opus 4.7/4.8 in Claude Cowork überarbeitet und erweitert.

Link zur Transkribussammlung: https://app.transkribus.org/invitations/c22ceb11-967c-4cda-b82a-6453340cc983

## Ablauf

Das Notebook `scripts/papyrus-layoutstudien.ipynb` steuert die Auswertung als **Pipeline**. Zentraler Datenspeicher ist `data/layout_data.json`: Die PAGE-XML-Dateien (Transkribus-Export unter `page_xml/`) werden dorthin eingelesen, und jeder Verarbeitungsschritt liest diese Datei und schreibt seine Ergebnisse zurück.

Reihenfolge (jeder Schritt setzt den vorigen voraus):

1. **PAGE-XML → JSON** (`page_xml_to_json.py`) – erzeugt/aktualisiert `data/layout_data.json` mit Bildmaßen, px/cm-Skala, Kolumnen (`column_data`: Polygone, Zeilen) und Fragmenten (`fragment_data`).
2. **Bildverarbeitung** (`image_processing.py`) – Bounding-Box, Flächen- und Randmaße je Platte.
3. **Kolumnen-Merkmale** (`column_metrics.py`) – Maße je Kolumne und Kolumnenpaar (braucht die Bbox aus Schritt 2).
4. **Kolumnenneigung** (`column_tilt.py`) – Maas's-Law-Winkel je nutzbarer Kolumne.
5. **Überblick & Export** (`layout_overview.py`, `csv_to_typst.py`) – zusammenfassende Tabellen als Markdown, CSV und Typst.

Hinweis: Ein erneuter Lauf von Schritt 1 überschreibt `column_data` komplett und verwirft dabei die pro Kolumne berechneten Felder (`metrics`, `tilt`); danach die Schritte 3–5 erneut ausführen. Die Verarbeitungsfunktionen sind dateibasiert (Argument `data_file=…`) und lassen sich auch einzeln außerhalb des Notebooks aufrufen.

## Skripte (`scripts/`)

- **`page_xml_to_json.py`** (`collect_layout_data`) – Liest die PAGE-XML-Dateien (Transkribus-Export) aus und baut daraus `data/layout_data.json` auf: Bildmaße, px/cm-Skala und die Textregionen, getrennt nach Kolumnen und Fragmenten. Bestehende Einträge bleiben erhalten; neue Platten kommen hinzu.
- **`image_processing.py`** (`process_layout_data`) – Segmentiert das Fragment vom hellen Leuchttisch-Hintergrund, erzeugt eine Binärmaske und leitet daraus Bounding-Box, Fläche, Bedeckungsgrad und Ränder ab. Alternativ manueller Bbox-Modus (`bbox_measurement: "manual"` im Eintrag), wenn die automatische Segmentierung unzuverlässig ist. Segmentierungsparameter sind in der Dataclass `SegmentationParams` gebündelt.
- **`column_metrics.py`** (`measure_columns`) – Berechnet je Kolumne Höhe, Breite, Fläche, oberen/unteren Rand und die Schriftspiegel-Verhältnisse (Kolumne ↔ Blatt) sowie je Nachbarpaar den Intercolumn-Abstand und die Kolumne-zu-Kolumne-Breite/-Fläche. Werte in px und – wo eine px/cm-Skala vorliegt – in cm bzw. cm².
- **`column_tilt.py`** (`measure_tilt`) – Misst die Neigung der linken Kante jeder nutzbaren Kolumne (Maas's Law) gegen drei Referenzen: die Bild-Senkrechte, eine plattenweite Ideal-Horizontale aus den Oberkanten und die Schrifthorizontale der jeweiligen Kolumne aus ihren Baselines (Johnson-Methode). Zusätzlich je Platte die geschätzte Plattenschiefe. Winkel auf 0,1° gerundet.
- **`layout_overview.py`** (`generate_overview`) – Baut aus `data/layout_data.json` zwei Tabellen: eine Zusammenfassung pro Platte und eine Tabelle pro Kolumne.
- **`csv_to_typst.py`** – Wandelt CSV-Tabellen in Typst-Tabellen (`.typ`) um (kurze, umbrechbare Kopf-Labels, inhaltsabhängige Spaltenbreiten, numerische Spalten rechtsbündig). Für DIN A4 quer gedacht.

## Ausgaben

- **`data/layout_data.json`** – zentraler Datenspeicher mit allen erfassten und berechneten Werten (Quelle für alle folgenden Ausgaben).
- **`data/layout_summary_per_plate.csv`** – eine Zeile je Platte (Kolumnen-/Fragmentzahl, Maße, mittlere Neigung, Plattenschiefe).
- **`data/layout_per_column.csv`** – eine Zeile je Kolumne (Neigung in drei Varianten plus Kolumnen-Merkmale).
- **`layout_overview.md`** – dieselbe Platten-Zusammenfassung als lesbares Markdown.
- **`text/layout_summary_per_plate.typ`**, **`text/layout_per_column.typ`** – die beiden Tabellen als Typst zum Einbinden in die Arbeit.
- **`images/masks/…_mask.png`**, **`…_bbox_preview.png`** – Binärmasken und Vorschaubilder der Bildverarbeitung.

## Abhängigkeiten

Bildverarbeitung: `numpy`, `opencv-python` (siehe `requirements.txt`). Die übrigen Skripte nutzen nur die Standardbibliothek. Zum Kompilieren der Typst-Tabellen wird Typst benötigt.
