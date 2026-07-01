"""
column_metrics.py
-----------------
Einfache Layout-Merkmale je Kolumne (und je Kolumnenpaar) für die Papyrus-
Layoutstudien. Läuft **nach** der Bounding-Box-Berechnung (``image_processing``),
weil oberer/unterer Rand und die Schriftspiegel-Verhältnisse die Platten-Bbox
als Blattmaß brauchen.

Annahmen zur Kolumnen-Geometrie
-------------------------------
Kolumnen sind mit **4 Punkten im Uhrzeigersinn** markiert, erster Punkt oben
links: ``p0=oben-links, p1=oben-rechts, p2=unten-rechts, p3=unten-links``.
Bildkoordinaten: x nach rechts, y nach unten.

Gemessene Merkmale (px, cm bzw. cm²)
------------------------------------
Pro Kolumne:
- ``height``  = ((y2+y3) − (y0+y1)) / 2            (Höhe aus den y-Werten)
- ``width``   = ((x1+x2) − (x0+x3)) / 2            (Breite aus den x-Werten)
- ``area``    = Polygonfläche (Shoelace)
- ``margin_top`` / ``margin_bottom``               (Kolumnenober-/-unterkante ↔ Blattkante)
- ``schriftspiegel_height_ratio`` / ``…_area_ratio`` (Kolumne ↔ Blatt)

Pro Kolumnenpaar (in ``to_next`` der linken Kolumne):
- ``intercolumn``      = Spalt zwischen rechter Kante links und linker Kante rechts
- ``col2col_width``    = linke Kante ↔ linke Kante der nächsten Kolumne
- ``col2col_area``     = Viereck aus den beiden linken Kanten

Horizontale Abstände werden in der Mitte des y-Überlappungsbereichs der beiden
Kanten gemessen; da die Kanten gerade sind, entspricht das dem Mittel über die
Überlappung.

cm-Werte sind abgeleitet (px / px_per_cm); ohne Skala ``None``. Ränder und
Schriftspiegel-Verhältnisse werden bei Mehrfach-Fragment-Platten (z. B. T)
unterdrückt, da die Bbox dort kein sinnvolles Blattmaß ist.

Nutzung::

    import column_metrics as cm
    layout_data = cm.measure_columns(layout_data, data_file=DATA_FILE)

Abhängigkeiten: nur Standardbibliothek.
"""

from __future__ import annotations

import json
from pathlib import Path

Point = tuple[float, float]


# ---------------------------------------------------------------------------
# Geometrie-Helfer
# ---------------------------------------------------------------------------

def parse_points(points: str) -> list[Point]:
    """'132,489 435,506 …' -> [(132.0, 489.0), (435.0, 506.0), …]"""
    out = []
    for pair in points.split():
        x, y = pair.split(',')
        out.append((float(x), float(y)))
    return out


def polygon_area(pts: list[Point]) -> float:
    """Fläche eines Polygons (Shoelace), immer positiv."""
    n = len(pts)
    s = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _edge_x_at_y(top: Point, bottom: Point, y: float) -> float:
    """x-Wert einer Kante (top->bottom) auf Höhe y (lineare Interpolation)."""
    (ax, ay), (bx, by) = top, bottom
    if by == ay:
        return (ax + bx) / 2.0
    return ax + (bx - ax) * (y - ay) / (by - ay)


def _horizontal_distance(edge_l: tuple[Point, Point], edge_r: tuple[Point, Point]) -> float:
    """Horizontaler Abstand zweier (annähernd senkrechter) Kanten.

    Gemessen in der Mitte des gemeinsamen y-Bereichs beider Kanten; das entspricht
    bei geraden Kanten exakt dem Mittel über die Überlappung. Fehlt eine
    Überlappung, wird auf den gemeinsamen Mittel-y beider Kanten zurückgegriffen.
    """
    (lt, lb) = edge_l
    (rt, rb) = edge_r
    lo = max(min(lt[1], lb[1]), min(rt[1], rb[1]))
    hi = min(max(lt[1], lb[1]), max(rt[1], rb[1]))
    if hi > lo:
        ym = (lo + hi) / 2.0
    else:  # kein Überlappungsbereich -> Mittel der beiden Kanten-Mitten
        ym = (min(lt[1], lb[1]) + max(lt[1], lb[1]) +
              min(rt[1], rb[1]) + max(rt[1], rb[1])) / 4.0
    return _edge_x_at_y(rt, rb, ym) - _edge_x_at_y(lt, lb, ym)


def _cm(px: float | None, px_per_cm: float | None, nd: int = 2) -> float | None:
    if px is None or not px_per_cm:
        return None
    return round(px / px_per_cm, nd)


def _cm2(px_area: float | None, px_per_cm: float | None, nd: int = 2) -> float | None:
    if px_area is None or not px_per_cm:
        return None
    return round(px_area / (px_per_cm ** 2), nd)


def _ratio(a: float | None, b: float | None, nd: int = 3) -> float | None:
    if a is None or not b:
        return None
    return round(a / b, nd)


# ---------------------------------------------------------------------------
# Merkmale je Kolumne / je Paar
# ---------------------------------------------------------------------------

def column_metrics(pts: list[Point], px_per_cm: float | None,
                   sheet: dict | None) -> dict:
    """Berechnet Höhe, Breite, Fläche, Ränder und Schriftspiegel einer Kolumne.

    ``sheet`` ist ``{'top': y, 'bottom': y, 'height': h, 'area': a}`` der Platte
    oder ``None`` (dann keine Rand-/Schriftspiegelwerte).
    """
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts[:4]

    height = ((y2 + y3) - (y0 + y1)) / 2.0
    width = ((x1 + x2) - (x0 + x3)) / 2.0
    area = polygon_area(pts)

    m = {
        'height_px':  round(height, 1),
        'height_cm':  _cm(height, px_per_cm),
        'width_px':   round(width, 1),
        'width_cm':   _cm(width, px_per_cm),
        'area_px':    int(round(area)),
        'area_cm2':   _cm2(area, px_per_cm),
        'margin_top_px':    None,
        'margin_top_cm':    None,
        'margin_bottom_px': None,
        'margin_bottom_cm': None,
        'schriftspiegel_height_ratio': None,
        'schriftspiegel_area_ratio':   None,
    }

    if sheet is not None:
        col_top = (y0 + y1) / 2.0       # Mittel der oberen Punkte
        col_bottom = (y2 + y3) / 2.0    # Mittel der unteren Punkte
        margin_top = col_top - sheet['top']
        margin_bottom = sheet['bottom'] - col_bottom
        m.update({
            'margin_top_px':    round(margin_top, 1),
            'margin_top_cm':    _cm(margin_top, px_per_cm),
            'margin_bottom_px': round(margin_bottom, 1),
            'margin_bottom_cm': _cm(margin_bottom, px_per_cm),
            'schriftspiegel_height_ratio': _ratio(height, sheet['height']),
            'schriftspiegel_area_ratio':   _ratio(area, sheet.get('area')),
        })

    return m


def pair_metrics(left_pts: list[Point], right_pts: list[Point],
                 px_per_cm: float | None) -> dict:
    """Berechnet Intercolumn, Kolumne-zu-Kolumne-Breite und -Fläche für ein Paar
    benachbarter Kolumnen (links -> rechts)."""
    l0, l1, l2, l3 = left_pts[:4]     # links: TL,TR,BR,BL
    r0, r1, r2, r3 = right_pts[:4]    # rechts: TL,TR,BR,BL

    left_col_right_edge = (l1, l2)    # rechte Kante der linken Kolumne
    right_col_left_edge = (r0, r3)    # linke Kante der rechten Kolumne
    left_col_left_edge = (l0, l3)     # linke Kante der linken Kolumne

    intercolumn = _horizontal_distance(left_col_right_edge, right_col_left_edge)
    col2col_width = _horizontal_distance(left_col_left_edge, right_col_left_edge)
    # Viereck aus den beiden linken Kanten: l0(TL) l3(BL) r3(BL) r0(TL)
    col2col_area = polygon_area([l0, l3, r3, r0])

    return {
        'intercolumn_px':   round(intercolumn, 1),
        'intercolumn_cm':   _cm(intercolumn, px_per_cm),
        'col2col_width_px': round(col2col_width, 1),
        'col2col_width_cm': _cm(col2col_width, px_per_cm),
        'col2col_area_px':  int(round(col2col_area)),
        'col2col_area_cm2': _cm2(col2col_area, px_per_cm),
    }


# ---------------------------------------------------------------------------
# Orchestrierung
# ---------------------------------------------------------------------------

def _sheet_from_entry(entry: dict) -> dict | None:
    """Blattmaße aus der Bbox; ``None`` wenn keine Bbox oder Mehrfach-Fragment."""
    if len(entry.get('fragment_data', [])) > 1:
        return None
    if 'bbox_origin' not in entry or entry.get('bbox_h') is None:
        return None
    top = entry['bbox_origin'][1]
    h = entry['bbox_h']
    area = entry.get('bbox_area_px')
    return {'top': top, 'bottom': top + h, 'height': h, 'area': area}


def measure_plate(entry: dict) -> None:
    """Berechnet alle Merkmale für die Kolumnen eines Platten-Eintrags (in-place)."""
    cols = entry.get('column_data', [])
    if not cols:
        return
    px_per_cm = entry.get('px/cm')
    sheet = _sheet_from_entry(entry)

    # Kolumnen von links nach rechts ordnen (Nachbarschaft fuer Paar-Metriken)
    parsed = [(c, parse_points(c['polygon'])) for c in cols]
    parsed.sort(key=lambda cp: sum(p[0] for p in cp[1]) / len(cp[1]))  # mittlerer x

    # Merkmale je Kolumne
    for col, pts in parsed:
        col['metrics'] = column_metrics(pts, px_per_cm, sheet)

    # Merkmale je Paar -> in 'to_next' der jeweils linken Kolumne
    for i in range(len(parsed)):
        if i < len(parsed) - 1:
            (lcol, lpts) = parsed[i]
            (rcol, rpts) = parsed[i + 1]
            pm = pair_metrics(lpts, rpts, px_per_cm)
            pm['both_usable'] = bool(lcol.get('usable') and rcol.get('usable'))
            lcol['metrics']['to_next'] = pm
        else:
            parsed[i][0]['metrics']['to_next'] = None


def measure_columns(layout_data: dict, data_file=None,
                    save: bool = True, verbose: bool = True) -> dict:
    """Berechnet Kolumnen-Merkmale für alle Platten und schreibt sie zurück.

    Args:
        layout_data: Dict ``{key: entry}`` (nach der Bbox-Berechnung).
        data_file: JSON-Zielpfad zum Speichern (erforderlich, wenn ``save=True``).
        save: Ergebnis nach ``data_file`` schreiben.
        verbose: Fortschritt/Kurzstatistik ausgeben.

    Returns:
        Das aktualisierte ``layout_data``-Dict.
    """
    n_cols = n_pairs = 0
    for key, entry in layout_data.items():
        measure_plate(entry)
        cols = entry.get('column_data', [])
        n_cols += len(cols)
        n_pairs += sum(1 for c in cols if c.get('metrics', {}).get('to_next'))
        if verbose and cols:
            print(f"[{key}] {len(cols)} Kolumnen vermessen")

    if save:
        if data_file is None:
            raise ValueError("data_file required when save=True.")
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(layout_data, f, indent=2, ensure_ascii=False)
        if verbose:
            print(f"\n{n_cols} Kolumnen, {n_pairs} Paare vermessen -> {data_file}")

    return layout_data
