#!/usr/bin/env python3
"""
csv_to_typst.py
---------------
Konvertiert CSV-Tabellen in Typst-Tabellen (.typ) fuer die Textfassung der Arbeit.

Pro CSV wird eine .typ-Datei mit einem ``#table(...)`` erzeugt: Kopfzeile fett,
numerische Spalten rechtsbuendig. Ausgabe standardmaessig nach ``<projekt>/text/``.

Vgl. Typst-Tabellen-Doku: https://typst.app/docs/guides/tables/

Nutzung::

    # alle CSVs aus data/ nach text/ konvertieren
    python csv_to_typst.py

    # bestimmte Dateien (Ausgabe ebenfalls nach text/)
    python csv_to_typst.py ../data/layout_per_column.csv

Die erzeugten .typ enthalten nur die Tabelle; im Dokument z. B. einbetten mit::

    #figure(include "text/layout_per_column.typ", caption: [ ... ]) <tbl:kolumnen>

Abhaengigkeiten: nur Standardbibliothek.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / 'data'
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / 'text'

# Zeichen, die im Typst-Content-Modus escaped werden muessen (Backslash zuerst).
_SPECIAL = ['#', '$', '_', '*', '`', '<', '@', '[', ']', '~']


def escape_typst(value) -> str:
    """Escaped Typst-Sonderzeichen im Content-Modus (z. B. '_' -> '\\_')."""
    s = str(value)
    s = s.replace('\\', '\\\\')          # Backslash zuerst
    for ch in _SPECIAL:
        s = s.replace(ch, '\\' + ch)
    return s


def _is_number(s: str) -> bool:
    s = s.strip()
    if s == '':
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False


def column_alignments(header, data_rows):
    """Numerische Spalten -> 'right', sonst 'left' (fuer den align-Parameter)."""
    aligns = []
    for j in range(len(header)):
        vals = [r[j] for r in data_rows if j < len(r) and str(r[j]).strip() != '']
        numeric = bool(vals) and all(_is_number(v) for v in vals)
        aligns.append('right' if numeric else 'left')
    return aligns


# Kurze, umbruchfreundliche Kopf-Labels fuer die Typst-Ausgabe (an Leerzeichen
# umbrechbar). Nicht gelistete Spalten: Fallback '_' -> Leerzeichen.
HEADER_MAP = {
    # Platten-Zusammenfassung
    'n_cols': 'Kol.', 'n_usable': 'nutzbar', 'n_frags': 'Frag.',
    'n_mask_components': 'Teile', 'total_lines': 'Zeilen ges.',
    'avg_lines': 'Ø Zeilen / Kol.', 'min_lines': 'min Zeilen', 'max_lines': 'max Zeilen',
    'tilt_vert_mean_deg': 'Ø Neig. vert. (°)', 'tilt_ideal_mean_deg': 'Ø Neig. ideal (°)',
    'tilt_baseline_mean_deg': 'Ø Neig. base (°)', 'plate_skew_deg': 'Schiefe (°)',
    'baseline_skew_deg': 'Baseline Schiefe (°)', 'n_columns_with_baseline': 'Kol. mit Zeilen',
    # gemeinsam / pro Kolumne
    'plate': 'Platte', 'column_index': 'Kol.', 'usable': 'nutzbar', 'n_lines': 'Zeilen',
    'tilt_vs_vertical_deg': 'Neig. vert. (°)', 'tilt_vs_ideal_deg': 'Neig. ideal (°)',
    'tilt_vs_baseline_deg': 'Neig. base (°)',
    'height_cm': 'Höhe (cm)', 'width_cm': 'Breite (cm)', 'area_cm2': 'Fläche (cm²)',
    'margin_top_cm': 'Rand oben (cm)', 'margin_bottom_cm': 'Rand unten (cm)',
    'schriftspiegel_height_ratio': 'Spiegel Verh. H',
    'intercolumn_cm': 'Intercol. (cm)',
    'col2col_width_cm': 'Kol. – Kol. Breite (cm)',
    'col2col_area_cm2': 'Kol. – Kol. Fläche (cm²)',
}


def header_label(name: str) -> str:
    """Kurzes Anzeige-Label einer Spalte (Fallback: '_' -> Leerzeichen)."""
    return HEADER_MAP.get(name, str(name).replace('_', ' '))


def column_widths(labels, data_rows, n, em_per_char=0.52, pad_em=1.0):
    """Spaltenbreiten in em: breit genug fuer das laengste Datentoken bzw. das
    laengste einzelne Kopf-Wort (mehrwortige Labels brechen an Leerzeichen um)."""
    widths = []
    for j in range(n):
        data_len = max([len(str(r[j])) for r in data_rows if j < len(r)] or [1])
        word_len = max([len(w) for w in labels[j].split()] or [1])
        chars = max(data_len, word_len, 2)
        widths.append(round(chars * em_per_char + pad_em, 1))
    return widths


def csv_to_typst_string(rows, source_name=None) -> str:
    """Baut aus geparsten CSV-Zeilen (erste Zeile = Kopf) ein Typst ``#table``."""
    if not rows:
        raise ValueError('CSV enthaelt keine Zeilen.')
    header, data_rows = rows[0], rows[1:]
    n = len(header)
    aligns = column_alignments(header, data_rows)
    labels = [header_label(h) for h in header]
    widths = column_widths(labels, data_rows, n)

    lines = []
    if source_name:
        lines += [
            f'// Automatisch erzeugt aus {source_name} durch scripts/csv_to_typst.py.',
            '// Nicht von Hand bearbeiten - bei Aenderungen das Skript erneut ausfuehren.',
            '// Spaltenbreiten sind auf den Inhalt abgestimmt (Koepfe brechen um);',
            '// fuer DIN A4 quer setzen, z. B.: #set page(flipped: true).',
            '',
        ]
    lines.append('#table(')
    lines.append('  columns: (' + ', '.join(f'{w}em' for w in widths) + '),')
    lines.append('  align: (' + ', '.join(aligns) + '),')
    header_cells = ', '.join(f'[*{escape_typst(lbl)}*]' for lbl in labels)
    lines.append(f'  table.header({header_cells}),')
    for r in data_rows:
        r = list(r) + [''] * (n - len(r))       # fehlende Spalten auffuellen
        lines.append('  ' + ', '.join(f'[{escape_typst(v)}]' for v in r[:n]) + ',')
    lines.append(')')
    lines.append('')
    return '\n'.join(lines)


def convert_file(csv_path, out_dir=DEFAULT_OUTPUT_DIR, verbose=True) -> Path:
    """Konvertiert eine CSV-Datei und legt die .typ in ``out_dir`` ab."""
    csv_path = Path(csv_path)
    with open(csv_path, newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    typ_path = out_dir / (csv_path.stem + '.typ')
    typ_path.write_text(csv_to_typst_string(rows, source_name=f'data/{csv_path.name}'),
                        encoding='utf-8')
    if verbose:
        n_rows = max(len(rows) - 1, 0)
        n_cols = len(rows[0]) if rows else 0
        print(f'{csv_path.name} -> {typ_path}  ({n_rows} Zeilen, {n_cols} Spalten)')
    return typ_path


def main(argv=None):
    ap = argparse.ArgumentParser(description='CSV-Tabellen nach Typst (.typ) konvertieren.')
    ap.add_argument('csv_files', nargs='*',
                    help='CSV-Dateien (Standard: alle *.csv in data/).')
    ap.add_argument('--outdir', default=str(DEFAULT_OUTPUT_DIR),
                    help='Zielordner der .typ-Dateien (Standard: text/).')
    args = ap.parse_args(argv)

    files = [Path(p) for p in args.csv_files] or sorted(DEFAULT_INPUT_DIR.glob('*.csv'))
    if not files:
        print(f'Keine CSV-Dateien gefunden in {DEFAULT_INPUT_DIR}.')
        return
    for p in files:
        convert_file(p, out_dir=args.outdir)


if __name__ == '__main__':
    main()
