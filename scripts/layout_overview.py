"""
layout_overview.py
------------------
Erzeugt aus ``layout_data`` einen lesbaren Markdown-Überblick für die
Papyrus-Layoutstudien und schreibt ihn nach ``layout_overview.md``.

Pro Platte werden Anzahl Kolumnen (gesamt und nutzbar), Fragmente, Höhe/Breite
(cm) sowie Zeilen-Kennzahlen (Summe, Ø, min, max) ausgewiesen. Der Gesamt-
überblick fasst dieselben Kennzahlen über alle Platten zusammen.

Konventionen:
- Ø, min und max beziehen sich nur auf Kolumnen mit bereits erfassten Zeilen;
  Kolumnen ohne Zeilendaten werden separat ausgewiesen.
- Fragmente werden separat gezählt und fließen nicht in die Kolumnen-Statistik ein.
- Höhe/Breite (cm) stammen aus ``bbox_h_cm`` / ``bbox_w_cm`` des Eintrags
  (abgeleitet aus px und px/cm); fehlt der Wert, erscheint „—".

Nutzung aus dem Notebook::

    import layout_overview as lo
    from IPython.display import Markdown, display

    md = lo.generate_overview(data_file=DATA_FILE,
                              overview_file=PROJECT_ROOT / 'layout_overview.md')
    display(Markdown(md))

Abhängigkeiten: nur Standardbibliothek.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from statistics import mean


def plate_name(key: str) -> str:
    """'0001_P_09782-Pl-A_R_001' -> 'A'"""
    return key.split('-Pl-')[1].split('_R')[0] if '-Pl-' in key else key


def fmt(x, nd: int = 1) -> str:
    """Formatiert Zahl/None für die Ausgabe; ``None`` -> Gedankenstrich."""
    if x is None:
        return '—'  # keine Daten vorhanden
    return f'{x:.{nd}f}' if isinstance(x, float) else str(x)


def aggregate(data: dict) -> tuple[list[dict], dict]:
    """Aggregiert ``layout_data`` zu Zeilen pro Platte und einer Gesamtstatistik.

    Returns:
        ``(rows, totals)`` – ``rows`` ist eine Liste von Platten-Dicts,
        ``totals`` enthält die plattenübergreifenden Kennzahlen.
    """
    rows = []
    all_line_counts = []   # Zeilen je Kolumne, nur Kolumnen mit erfassten Zeilen
    total_cols = total_usable_cols = total_frags = cols_without_lines = 0

    for key, entry in data.items():
        cols = entry.get('column_data', [])
        frags = entry.get('fragment_data', [])
        line_counts = [len(c.get('lines', [])) for c in cols]
        captured = [n for n in line_counts if n > 0]
        n_usable = sum(1 for c in cols if c.get('usable'))

        # Neigungswinkel (nur Kolumnen mit erfasstem tilt)
        tilt_v = [c['tilt']['tilt_vs_vertical_deg'] for c in cols
                  if c.get('tilt') and c['tilt'].get('tilt_vs_vertical_deg') is not None]
        tilt_i = [c['tilt']['tilt_vs_ideal_deg'] for c in cols
                  if c.get('tilt') and c['tilt'].get('tilt_vs_ideal_deg') is not None]
        tilt_b = [c['tilt']['tilt_vs_baseline_deg'] for c in cols
                  if c.get('tilt') and c['tilt'].get('tilt_vs_baseline_deg') is not None]

        total_cols += len(cols)
        total_usable_cols += n_usable
        total_frags += len(frags)
        cols_without_lines += sum(1 for n in line_counts if n == 0)
        all_line_counts += captured

        rows.append({
            'plate':       plate_name(key),
            'n_cols':      len(cols),
            'n_usable':    n_usable,
            'n_frags':     len(frags),
            'h_cm':        entry.get('bbox_h_cm'),   # Plattenhoehe (cm), None ohne Skala/Mehrfach-Fragment
            'w_cm':        entry.get('bbox_w_cm'),   # Plattenbreite (cm), None ohne Skala/Mehrfach-Fragment
            'total_lines': sum(line_counts),
            'avg_lines':   mean(captured) if captured else None,
            'min_lines':   min(captured) if captured else None,
            'max_lines':   max(captured) if captured else None,
            'tilt_v':      mean(tilt_v) if tilt_v else None,   # Ø Neigung gegen Bild-Senkrechte
            'tilt_i':      mean(tilt_i) if tilt_i else None,   # Ø Neigung gegen Ideal-Horizontale
            'tilt_b':      mean(tilt_b) if tilt_b else None,   # Ø Neigung gegen Baseline-Horizontale (Ansatz 3)
            'skew':        entry.get('tilt_reference', {}).get('plate_skew_deg'),
            'base_skew':   entry.get('tilt_reference', {}).get('baseline_skew_deg'),  # Baseline-Schiefe der Platte
            'n_base':      entry.get('tilt_reference', {}).get('n_columns_with_baseline'),  # Kolumnen mit Baseline
            'pieces':      entry.get('n_mask_components'),     # Fragmentierung: getrennte Maskenteile
        })

    totals = {
        'n_plates':            len(data),
        'total_cols':          total_cols,
        'total_usable_cols':   total_usable_cols,
        'total_frags':         total_frags,
        'cols_with_lines':     len(all_line_counts),
        'cols_without_lines':  cols_without_lines,
        'total_lines':         sum(r['total_lines'] for r in rows),
        'avg_lines':           mean(all_line_counts) if all_line_counts else None,
        'min_lines':           min(all_line_counts) if all_line_counts else None,
        'max_lines':           max(all_line_counts) if all_line_counts else None,
    }
    return rows, totals


# Spaltenreihenfolge der CSV-Ausgaben (zugleich die Header).
PLATE_FIELDS = [
    'plate', 'n_cols', 'n_usable', 'n_frags', 'n_mask_components',
    'height_cm', 'width_cm',
    'tilt_vert_mean_deg', 'tilt_ideal_mean_deg', 'tilt_baseline_mean_deg',
    'plate_skew_deg', 'baseline_skew_deg',
]

# Nur cm-/cm²-Werte in der CSV; Pixelwerte und die Flächen-Ratio sind entfernt,
# damit die Tabelle (quer, DIN A4) nicht zu breit wird.
COLUMN_FIELDS = [
    'plate', 'column_index', 'usable', 'n_lines',
    'tilt_vs_vertical_deg', 'tilt_vs_ideal_deg', 'tilt_vs_baseline_deg',
    'height_cm', 'width_cm', 'area_cm2',
    'margin_top_cm', 'margin_bottom_cm',
    'schriftspiegel_height_ratio',
    'intercolumn_cm', 'col2col_width_cm', 'col2col_area_cm2',
]


def plate_csv_rows(data: dict) -> list[dict]:
    """Eine Zeile pro Platte (Zusammenfassung) mit sprechenden CSV-Spaltennamen."""
    rows, _ = aggregate(data)
    out = []
    for r in rows:
        out.append({
            'plate':                   r['plate'],
            'n_cols':                  r['n_cols'],
            'n_usable':                r['n_usable'],
            'n_frags':                 r['n_frags'],
            'n_mask_components':       r['pieces'],
            'height_cm':               r['h_cm'],
            'width_cm':                r['w_cm'],
            'total_lines':             r['total_lines'],
            'avg_lines':               round(r['avg_lines'], 2) if r['avg_lines'] is not None else None,
            'min_lines':               r['min_lines'],
            'max_lines':               r['max_lines'],
            'tilt_vert_mean_deg':      round(r['tilt_v'], 1) + 0.0 if r['tilt_v'] is not None else None,
            'tilt_ideal_mean_deg':     round(r['tilt_i'], 1) + 0.0 if r['tilt_i'] is not None else None,
            'tilt_baseline_mean_deg':  round(r['tilt_b'], 1) + 0.0 if r['tilt_b'] is not None else None,
            'plate_skew_deg':          r['skew'],
            'baseline_skew_deg':       r['base_skew'],
            'n_columns_with_baseline': r['n_base'],
        })
    return out


def column_csv_rows(data: dict) -> list[dict]:
    """Eine Zeile pro Kolumne: Neigung (3 Ansätze) und Kolumnen-Merkmale flach.

    Kolumnen sind pro Platte fortlaufend ab 1 nummeriert (Reihenfolge wie in
    ``column_data``). Fehlt ein Wert (z. B. ``tilt``/``metrics`` noch nicht
    berechnet, oder ``to_next`` bei der letzten Kolumne), bleibt die Zelle leer.
    """
    out = []
    for key, entry in data.items():
        plate = plate_name(key)
        for i, col in enumerate(entry.get('column_data', []), start=1):
            tilt = col.get('tilt') or {}
            m = col.get('metrics') or {}
            nxt = m.get('to_next') or {}
            out.append({
                'plate':                       plate,
                'column_index':                i,
                'usable':                      col.get('usable'),
                'n_lines':                     len(col.get('lines', [])),
                'tilt_vs_vertical_deg':        tilt.get('tilt_vs_vertical_deg'),
                'tilt_vs_ideal_deg':           tilt.get('tilt_vs_ideal_deg'),
                'tilt_vs_baseline_deg':        tilt.get('tilt_vs_baseline_deg'),
                'height_px':                   m.get('height_px'),
                'height_cm':                   m.get('height_cm'),
                'width_px':                    m.get('width_px'),
                'width_cm':                    m.get('width_cm'),
                'area_px':                     m.get('area_px'),
                'area_cm2':                    m.get('area_cm2'),
                'margin_top_px':               m.get('margin_top_px'),
                'margin_top_cm':               m.get('margin_top_cm'),
                'margin_bottom_px':            m.get('margin_bottom_px'),
                'margin_bottom_cm':            m.get('margin_bottom_cm'),
                'schriftspiegel_height_ratio': m.get('schriftspiegel_height_ratio'),
                'schriftspiegel_area_ratio':   m.get('schriftspiegel_area_ratio'),
                'intercolumn_px':              nxt.get('intercolumn_px'),
                'intercolumn_cm':              nxt.get('intercolumn_cm'),
                'col2col_width_px':            nxt.get('col2col_width_px'),
                'col2col_width_cm':            nxt.get('col2col_width_cm'),
                'col2col_area_px':             nxt.get('col2col_area_px'),
                'col2col_area_cm2':            nxt.get('col2col_area_cm2'),
            })
    return out


def write_csv(rows: list[dict], path, fieldnames: list[str]):
    """Schreibt ``rows`` als CSV nach ``path`` (``None`` -> leere Zelle)."""
    path = Path(path)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, restval='',
                                extrasaction='ignore')
        writer.writeheader()
        for r in rows:
            writer.writerow({k: ('' if v is None else v) for k, v in r.items()})
    return path


def build_overview_markdown(data: dict, source_name: str | None = None) -> str:
    """Baut den Markdown-Überblick als String (ohne Datei-I/O)."""
    rows, t = aggregate(data)

    md_lines = [
        f'# Layout-Überblick – {date.today().isoformat()}',
        '',
    ]
    if source_name:
        md_lines += [f'Datenquelle: `{source_name}`', '']
    md_lines += [
        '## Gesamtüberblick',
        '',
        f'- Platten: {t["n_plates"]}',
        f'- Kolumnen gesamt: {t["total_cols"]} (davon nutzbar: {t["total_usable_cols"]})',
        f'- Fragmente gesamt: {t["total_frags"]}',
        f'- Kolumnen mit erfassten Zeilen: {t["cols_with_lines"]} '
        f'(ohne Zeilendaten: {t["cols_without_lines"]})',
        f'- Zeilen gesamt: {t["total_lines"]}',
        f'- Ø Zeilen pro Kolumne: {fmt(t["avg_lines"])}',
        f'- Zeilen pro Kolumne (min / max): {fmt(t["min_lines"])} / {fmt(t["max_lines"])}',
        '',
        '> Ø, min und max beziehen sich nur auf Kolumnen mit erfassten Zeilen. '
        'Fragmente (z. B. Platte T) werden separat gezaehlt und fliessen nicht in die Kolumnen-Statistik ein. '
        'Höhe/Breite (cm) sind aus den Bbox-Pixelmaßen und der px/cm-Skala abgeleitet '
        '(— ohne Skala oder bei mehreren Fragmenten). '
        'Ø Neigung = mittlere Kolumnenneigung der nutzbaren Kolumnen gegen drei Referenzen: '
        'die Bild-Senkrechte (vert.), die plattenweite Ideal-Horizontale aus den Oberkanten (ideal) '
        'und die Schrifthorizontale der jeweiligen Kolumne aus ihren Baselines (baseline, Johnson-Methode; '
        'nur wo Zeilen erfasst sind, sonst —). '
        'Schiefe = geschätzte Plattenschiefe aus den Oberkanten; Baseline-Schiefe = plattenweite Schrifthorizontale '
        'aus den Baselines (Kontrolle zur Oberkanten-Schiefe, in Klammern die Zahl der Kolumnen mit Zeilen). '
        'Neigung positiv = untere Kante nach links. '
        'Teile = Zahl zusammenhängender Maskenteile (Fragmentierungsmaß: 1 = zusammenhängendes Blatt, '
        '>1 = physisch getrennte Stücke; — im manuellen Bbox-Modus). '
        'Auf stark fragmentierten Platten (viele unbenutzbare Kolumnen, Teile > 1) sind die Neigungswinkel '
        'nur mit geringer Konfidenz zu lesen.',
        '',
        '## Pro Platte',
        '',
        '| Platte | Kolumnen | nutzbar | Fragmente | Teile | Höhe (cm) | Breite (cm) | Zeilen gesamt | Ø Zeilen/Kol | min | max | Ø Neig. vert. (°) | Ø Neig. ideal (°) | Ø Neig. baseline (°) | Schiefe (°) | Baseline-Schiefe (°) |',
        '|--------|---------:|--------:|----------:|------:|----------:|------------:|--------------:|-------------:|----:|----:|------------------:|------------------:|---------------------:|------------:|---------------------:|',
    ]
    for r in rows:
        base_skew = (f"{fmt(r['base_skew'], 2)} ({r['n_base']})"
                     if r['base_skew'] is not None else '—')
        md_lines.append(
            f"| {r['plate']} | {r['n_cols']} | {r['n_usable']} | {r['n_frags']} | {fmt(r['pieces'])} | "
            f"{fmt(r['h_cm'])} | {fmt(r['w_cm'])} | {r['total_lines']} | "
            f"{fmt(r['avg_lines'])} | {fmt(r['min_lines'])} | {fmt(r['max_lines'])} | "
            f"{fmt(r['tilt_v'])} | {fmt(r['tilt_i'])} | {fmt(r['tilt_b'])} | {fmt(r['skew'], 2)} | {base_skew} |"
        )

    return '\n'.join(md_lines) + '\n'


def generate_overview(data: dict | None = None, data_file=None,
                      overview_file=None, plate_csv=None, column_csv=None,
                      save: bool = True, verbose: bool = True) -> str:
    """Lädt/akzeptiert ``layout_data``, baut den Überblick und schreibt ihn.

    Erzeugt drei Ausgaben:
    - die **Zusammenfassung pro Platte** als Markdown (``overview_file``) und
      zusätzlich als CSV (``plate_csv``);
    - die **Daten pro Kolumne** als CSV (``column_csv``).

    Werden ``plate_csv``/``column_csv`` nicht gesetzt, aber ``save=True``, so
    werden sie neben ``overview_file`` (bzw. neben ``data_file``) unter den Namen
    ``layout_summary_per_plate.csv`` und ``layout_per_column.csv`` abgelegt.

    Args:
        data: ``layout_data``-Dict. Wenn ``None``, wird aus ``data_file`` geladen.
        data_file: JSON-Quelle (für Laden und als „Datenquelle"-Angabe im Kopf).
        overview_file: Zielpfad der Markdown-Datei. ``None`` = kein Markdown schreiben.
        plate_csv: Zielpfad der Platten-CSV (``None`` = neben Markdown/JSON ablegen).
        column_csv: Zielpfad der Kolumnen-CSV (``None`` = neben Markdown/JSON ablegen).
        save: Ausgaben auf die Platte schreiben.
        verbose: kurze Statusmeldungen ausgeben.

    Returns:
        Den erzeugten Markdown-String (Zusammenfassung pro Platte).
    """
    source_name = None
    if data is None:
        if data_file is None:
            raise ValueError("Either data or data_file must be provided.")
        with open(data_file, encoding='utf-8') as f:
            data = json.load(f)
    if data_file is not None:
        source_name = Path(data_file).name

    markdown = build_overview_markdown(data, source_name=source_name)

    if save:
        # Basisverzeichnis für automatisch benannte CSVs bestimmen
        base_dir = None
        if overview_file is not None:
            overview_file = Path(overview_file)
            with open(overview_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
            if verbose:
                print(f'Ueberblick (Markdown) -> {overview_file}')
            base_dir = overview_file.parent
        elif data_file is not None:
            base_dir = Path(data_file).parent

        if plate_csv is None and base_dir is not None:
            plate_csv = base_dir / 'layout_summary_per_plate.csv'
        if column_csv is None and base_dir is not None:
            column_csv = base_dir / 'layout_per_column.csv'

        if plate_csv is not None:
            write_csv(plate_csv_rows(data), plate_csv, PLATE_FIELDS)
            if verbose:
                print(f'Zusammenfassung pro Platte (CSV) -> {plate_csv}')
        if column_csv is not None:
            write_csv(column_csv_rows(data), column_csv, COLUMN_FIELDS)
            if verbose:
                print(f'Daten pro Kolumne (CSV) -> {column_csv}')

    return markdown
