"""
page_xml_to_json.py
-------------------
Liest PAGE-XML-Dateien (Transkribus-Export) aus und baut das ``layout_data``-Dict
für die Papyrus-Layoutstudien auf.

Pro Datei/Platte werden Bildmaße, die px/cm-Skala sowie die Textregionen erfasst,
getrennt nach **Kolumnen** (``column_data``) und **Fragmenten** (``fragment_data``).
Die Klassifikation läuft über das ``structure type`` im ``custom``-Attribut der Region.

Die Liste der auszuwertenden Dateien wird vom Aufrufer übergeben (im Notebook
definiert). Bestehende Einträge in der Ziel-JSON bleiben erhalten – z. B. manuelle
bbox-Felder und Messwerte –, die ausgelesenen Felder werden ergänzt/aktualisiert.

Nutzung aus dem Notebook::

    import page_xml_to_json as pxj

    page_xml_files = list(PAGE_XML_DIR.rglob('page/*.xml'))   # im Notebook definiert
    layout_data = pxj.collect_layout_data(page_xml_files, data_file=DATA_FILE)

Abhängigkeiten: nur Standardbibliothek (``xml.etree.ElementTree``, ``json``).
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

#: Namespace des PAGE-XML-Schemas (Transkribus-Export).
PAGE_NS = {'p': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}


# ---------------------------------------------------------------------------
# Region-Klassifikation und -Auslesen
# ---------------------------------------------------------------------------

def region_kind(custom: str | None) -> str | None:
    """Klassifiziert eine TextRegion über ihr ``structure type`` im custom-Attribut.

    Returns:
        ``'column'``   für Kolumnen (inkl. ``column_unusable`` / ``column_incomplete``),
        ``'fragment'`` für Fragmente (z. B. Platte T, an die Editionen angeglichen),
        ``None``       für sonstige Regionen (``marginalia``, ``bounding_box_edge`` …).
    """
    c = custom or ''
    if 'column' in c:
        return 'column'
    if 'fragment' in c:
        return 'fragment'
    return None


def extract_region(region: ET.Element, ns: dict = PAGE_NS) -> dict:
    """Sammelt Polygon, usable-Flag und Zeilen einer Region (Kolumne oder Fragment)."""
    custom = region.get('custom') or ''
    lines = []
    for line in region.findall('p:TextLine', ns):
        line_custom = line.get('custom') or ''
        baseline = line.find('p:Baseline', ns)
        lines.append({
            'usable': 'damaged' not in line_custom,
            'polygon': line.find('p:Coords', ns).get('points'),
            'baseline': baseline.get('points') if baseline is not None else None,
        })
    return {
        'usable': 'unusable' not in custom,
        'polygon': region.find('p:Coords', ns).get('points'),
        'lines': lines,
    }


# ---------------------------------------------------------------------------
# Eine Datei parsen
# ---------------------------------------------------------------------------

def parse_page_xml(file, ns: dict = PAGE_NS) -> tuple[str, dict]:
    """Liest eine PAGE-XML-Datei aus.

    Returns:
        ``(key, entry)`` – ``key`` ist der Dateistamm (z. B.
        ``'0001_P_09782-Pl-A_R_001'``), ``entry`` das zugehörige Daten-Dict.
    """
    file = Path(file)
    root = ET.parse(file).getroot()
    stem = file.stem
    # Transkribus stellt dem Export-Bildnamen ein 4-stelliges Praefix voran
    # (z. B. `0012_`); fuer den Originalnamen wird es entfernt.
    image_file = 'images/' + stem[5:] + '.jpg'

    page = root.find('p:Page', ns)
    regions = page.findall('p:TextRegion', ns)

    image_w = int(page.get('imageWidth'))
    image_h = int(page.get('imageHeight'))

    # px/cm-Skala: einige Bilder enthalten unten einen horizontalen Maßstab; die
    # ChartRegion liegt ueber 10 cm davon. Pixel pro 10 cm = x2 - x1 der ersten
    # beiden Punkte.
    scale = page.find('p:ChartRegion/p:Coords', ns)
    if scale is not None:
        points = scale.get('points').split()
        x1 = int(points[0].split(',')[0])
        x2 = int(points[1].split(',')[0])
        px_per_cm = (x2 - x1) / 10
    else:
        px_per_cm = None

    # Regionen nach Typ trennen
    column_data = []
    fragment_data = []
    for region in regions:
        kind = region_kind(region.get('custom'))
        if kind == 'column':
            column_data.append(extract_region(region, ns))
        elif kind == 'fragment':
            fragment_data.append(extract_region(region, ns))

    entry = {
        'xml_file': file.as_posix(),
        'image_file': image_file,
        'image_w': image_w,
        'image_h': image_h,
        'px/cm': px_per_cm,
        'column_data': column_data,
        'fragment_data': fragment_data,
    }
    return stem, entry


# ---------------------------------------------------------------------------
# Mehrere Dateien einsammeln
# ---------------------------------------------------------------------------

def collect_layout_data(page_xml_files, data_file=None, ns: dict = PAGE_NS,
                        save: bool = True, verbose: bool = True) -> dict:
    """Wertet alle übergebenen PAGE-XML-Dateien aus und baut ``layout_data`` auf.

    Lädt – falls vorhanden – bestehende Daten aus ``data_file`` und ergänzt sie
    (``setdefault``/``update``), sodass neue Platten automatisch hinzukommen und
    bestehende Zusatzfelder (manuelle bbox, Messwerte) erhalten bleiben.

    Args:
        page_xml_files: Iterable von Pfaden zu PAGE-XML-Dateien (im Notebook definiert).
        data_file: JSON-Datei zum Laden und Speichern. ``None`` = nur im Speicher,
            ohne Laden/Schreiben.
        ns: PAGE-Namespace (Standard: :data:`PAGE_NS`).
        save: Ergebnis nach ``data_file`` schreiben (nur wenn ``data_file`` gesetzt).
        verbose: Fortschritt ausgeben.

    Returns:
        Das aufgebaute ``layout_data``-Dict.
    """
    layout_data: dict = {}
    if data_file is not None and Path(data_file).exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            layout_data = json.load(f)

    for file in page_xml_files:
        stem, entry = parse_page_xml(file, ns)
        if verbose:
            print(f"Processing page: {stem}")
        layout_data.setdefault(stem, {}).update(entry)

    if save and data_file is not None:
        n_cols = sum(len(e.get('column_data', [])) for e in layout_data.values())
        n_frags = sum(len(e.get('fragment_data', [])) for e in layout_data.values())
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(layout_data, f, indent=2, ensure_ascii=False)
        if verbose:
            print(f"Writing {len(layout_data)} pages "
                  f"({n_cols} columns, {n_frags} fragments) to {data_file}")

    return layout_data
