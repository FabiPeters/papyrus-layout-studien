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
            'skew':        entry.get('tilt_reference', {}).get('plate_skew_deg'),
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
        'Ø Neigung = mittlere Kolumnenneigung der nutzbaren Kolumnen gegen die Bild-Senkrechte (vert.) '
        'bzw. die plattenweite Ideal-Horizontale (ideal); Schiefe = geschätzte Plattenschiefe. '
        'Neigung positiv = untere Kante nach links. '
        'Teile = Zahl zusammenhängender Maskenteile (Fragmentierungsmaß: 1 = zusammenhängendes Blatt, '
        '>1 = physisch getrennte Stücke; — im manuellen Bbox-Modus). '
        'Auf stark fragmentierten Platten (viele unbenutzbare Kolumnen, Teile > 1) sind die Neigungswinkel '
        'nur mit geringer Konfidenz zu lesen.',
        '',
        '## Pro Platte',
        '',
        '| Platte | Kolumnen | nutzbar | Fragmente | Teile | Höhe (cm) | Breite (cm) | Zeilen gesamt | Ø Zeilen/Kol | min | max | Ø Neig. vert. (°) | Ø Neig. ideal (°) | Schiefe (°) |',
        '|--------|---------:|--------:|----------:|------:|----------:|------------:|--------------:|-------------:|----:|----:|------------------:|------------------:|------------:|',
    ]
    for r in rows:
        md_lines.append(
            f"| {r['plate']} | {r['n_cols']} | {r['n_usable']} | {r['n_frags']} | {fmt(r['pieces'])} | "
            f"{fmt(r['h_cm'])} | {fmt(r['w_cm'])} | {r['total_lines']} | "
            f"{fmt(r['avg_lines'])} | {fmt(r['min_lines'])} | {fmt(r['max_lines'])} | "
            f"{fmt(r['tilt_v'])} | {fmt(r['tilt_i'])} | {fmt(r['skew'], 2)} |"
        )

    return '\n'.join(md_lines) + '\n'


def generate_overview(data: dict | None = None, data_file=None,
                      overview_file=None, save: bool = True,
                      verbose: bool = True) -> str:
    """Lädt/akzeptiert ``layout_data``, baut den Überblick und schreibt ihn.

    Args:
        data: ``layout_data``-Dict. Wenn ``None``, wird aus ``data_file`` geladen.
        data_file: JSON-Quelle (für Laden und als „Datenquelle"-Angabe im Kopf).
        overview_file: Zielpfad der Markdown-Datei. ``None`` = nicht schreiben.
        save: Markdown nach ``overview_file`` schreiben.
        verbose: kurze Statusmeldung ausgeben.

    Returns:
        Den erzeugten Markdown-String.
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

    if save and overview_file is not None:
        overview_file = Path(overview_file)
        with open(overview_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        if verbose:
            print(f'Ueberblick geschrieben nach {overview_file}')

    return markdown
