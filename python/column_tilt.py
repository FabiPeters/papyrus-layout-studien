"""
column_tilt.py
--------------
Neigungswinkel der Kolumnen (Maas's Law) für die Papyrus-Layoutstudien.

Gemessen wird die **linke Kante** jeder **nutzbaren** Kolumne gegen eine
Referenz-Senkrechte. Umgesetzt sind drei Varianten (vgl. Methodik-Notiz
„Winkelmessung Maas's Law"):

1. ``tilt_vs_vertical_deg`` – gegen die reine Bild-Senkrechte
   (Annahme: das Digitalisat ist lotrecht ausgerichtet).
2. ``tilt_vs_ideal_deg`` – gegen die Senkrechte einer plattenweiten
   Ideal-Horizontalen, die aus den **Oberkanten** aller nutzbaren Kolumnen
   gemittelt wird (entfernt eine globale Schieflage der Platte).
3. ``tilt_vs_baseline_deg`` – gegen die Senkrechte der tatsächlichen
   **Schrifthorizontalen**, längengewichtet aus den **Baselines** der jeweiligen
   Kolumne (Johnson-Methode). Nur wo Zeilen erfasst sind (aktuell A, B), sonst
   ``None``.

Geometrie (4 Punkte im Uhrzeigersinn, erster oben links):
``p0=oben-links, p1=oben-rechts, p2=unten-rechts, p3=unten-links``; Bild-
koordinaten x nach rechts, y nach unten.

- linke Kante  L = p3 − p0
- Oberkante    T = p1 − p0
- Baseline     b = p_Ende − p_Start (pro Zeile)

Gemeinsame Formel: Neigung = vorzeichenbehafteter Winkel von der Referenz-
Senkrechten zur linken Kante. Die Referenz-Senkrechte ist die um die Referenz-
Horizontale gedrehte Lot-Richtung; Variante 1 nutzt Referenz-Horizontale = 0,
Variante 2 die gemittelte Oberkanten-Richtung der Platte, Variante 3 die
gemittelte Baseline-Richtung der Kolumne. Es gilt
``tilt_vs_ideal = tilt_vs_vertical − plate_skew`` (Plattenschiefe als Konstante).

Zur Validierung wird je Platte auch die plattenweite Baseline-Horizontale
(``baseline_skew_deg``) bestimmt; ihr Vergleich mit ``plate_skew_deg`` (Oberkanten-
Proxy) zeigt, wie gut die Oberkante die Schriftlinie ersetzt.

Vorzeichen: **positiv = untere Kante gegenüber der oberen nach links versetzt**
(Kolumne kippt im Uhrzeigersinn), negativ = nach rechts.

Erwartungswert pro Kolumne: rund 1°–4°.

Ergebnis:
- je nutzbarer Kolumne ``column['tilt'] = {tilt_vs_vertical_deg, tilt_vs_ideal_deg,
  tilt_vs_baseline_deg}``
- je Platte ``entry['tilt_reference'] = {plate_skew_deg, baseline_skew_deg,
  n_columns_used, n_columns_with_baseline}``

Nutzung::

    import column_tilt as ct
    layout_data = ct.measure_tilt(layout_data, data_file=DATA_FILE)

Abhängigkeiten: nur Standardbibliothek.
"""

from __future__ import annotations

import json
import math

Point = tuple[float, float]


def parse_points(points: str) -> list[Point]:
    """'132,489 435,506 …' -> [(132.0, 489.0), …]"""
    out = []
    for pair in points.split():
        x, y = pair.split(',')
        out.append((float(x), float(y)))
    return out


def _signed_angle_deg(vx: float, vy: float, wx: float, wy: float) -> float:
    """Vorzeichenbehafteter Winkel von Vektor v nach w (Grad, −180..180)."""
    return math.degrees(math.atan2(vx * wy - vy * wx, vx * wx + vy * wy))


def top_edge_vector(pts: list[Point]) -> tuple[float, float]:
    """Oberkante p0->p1 (zeigt nach rechts)."""
    (x0, y0), (x1, y1) = pts[0], pts[1]
    return (x1 - x0, y1 - y0)


def left_edge_vector(pts: list[Point]) -> tuple[float, float]:
    """Linke Kante p0->p3 (zeigt nach unten)."""
    (x0, y0), (x3, y3) = pts[0], pts[3]
    return (x3 - x0, y3 - y0)


def plate_reference_angle(pts_list: list[list[Point]]) -> float | None:
    """Mittlere Orientierung der Oberkanten (Grad, Abweichung von der Bild-
    Horizontalen). Vektormittel der Einheitsvektoren; ``None`` wenn nicht bestimmbar."""
    sx = sy = 0.0
    for pts in pts_list:
        tx, ty = top_edge_vector(pts)
        n = math.hypot(tx, ty)
        if n:
            sx += tx / n
            sy += ty / n
    if sx == 0.0 and sy == 0.0:
        return None
    return math.degrees(math.atan2(sy, sx))


def baseline_reference_angle(lines: list[dict]) -> float | None:
    """Mittlere Orientierung der Schriftlinien (Baselines) – längengewichtet über
    die rohen Baseline-Vektoren. Nur nutzbare Zeilen mit Baseline; jede Baseline
    wird einheitlich nach rechts orientiert (Δx ≥ 0). ``None`` wenn keine
    verwertbare Baseline vorliegt."""
    sx = sy = 0.0
    for ln in lines:
        if not ln.get('usable'):
            continue
        bl = ln.get('baseline')
        if not bl:
            continue
        p = parse_points(bl)
        if len(p) < 2:
            continue
        dx = p[-1][0] - p[0][0]      # erster -> letzter Punkt (Gesamtrichtung)
        dy = p[-1][1] - p[0][1]
        if dx < 0:                    # einheitlich nach rechts orientieren
            dx, dy = -dx, -dy
        sx += dx                      # unnormiert summieren = Längengewichtung
        sy += dy
    if sx == 0.0 and sy == 0.0:
        return None
    return math.degrees(math.atan2(sy, sx))


def tilt_deg(pts: list[Point], reference_horizontal_deg: float) -> float:
    """Neigung der linken Kante gegen die um ``reference_horizontal_deg`` gedrehte
    Senkrechte. Positiv = untere Kante nach links versetzt."""
    lx, ly = left_edge_vector(pts)
    a = math.radians(reference_horizontal_deg)
    vx, vy = -math.sin(a), math.cos(a)   # Lot-Richtung (nach unten), um a gedreht
    return _signed_angle_deg(vx, vy, lx, ly)


def measure_plate_tilt(entry: dict) -> None:
    """Berechnet die Neigungswinkel der nutzbaren Kolumnen einer Platte (in-place)."""
    cols = entry.get('column_data', [])
    usable = [(c, parse_points(c['polygon'])) for c in cols if c.get('usable')]

    # Variante 2: Ideal-Horizontale aus den Oberkanten der nutzbaren Kolumnen
    alpha_top = plate_reference_angle([pts for _, pts in usable]) if usable else None
    # Plattenweite Baseline-Horizontale (zum Vergleich mit dem Oberkanten-Proxy)
    all_lines = [ln for c, _ in usable for ln in c.get('lines', [])]
    alpha_base_plate = baseline_reference_angle(all_lines)

    n_with_base = 0
    for col in cols:
        if not col.get('usable'):
            col['tilt'] = None
            continue
        pts = parse_points(col['polygon'])
        t_vert = tilt_deg(pts, 0.0)
        t_ideal = tilt_deg(pts, alpha_top) if alpha_top is not None else None
        # Variante 3: Baseline-Horizontale der jeweiligen Kolumne (Johnson)
        alpha_base = baseline_reference_angle(col.get('lines', []))
        t_base = tilt_deg(pts, alpha_base) if alpha_base is not None else None
        if alpha_base is not None:
            n_with_base += 1
        col['tilt'] = {
            'tilt_vs_vertical_deg': round(t_vert, 3),
            'tilt_vs_ideal_deg': round(t_ideal, 3) if t_ideal is not None else None,
            'tilt_vs_baseline_deg': round(t_base, 3) if t_base is not None else None,
        }

    entry['tilt_reference'] = {
        'plate_skew_deg': round(alpha_top, 3) if alpha_top is not None else None,
        'baseline_skew_deg': round(alpha_base_plate, 3) if alpha_base_plate is not None else None,
        'n_columns_used': len(usable),
        'n_columns_with_baseline': n_with_base,
    }


def measure_tilt(layout_data: dict, data_file=None,
                 save: bool = True, verbose: bool = True) -> dict:
    """Berechnet die Kolumnenneigung für alle Platten und schreibt sie zurück.

    Args:
        layout_data: Dict ``{key: entry}`` (Kolumnen mit ``polygon``).
        data_file: JSON-Zielpfad (erforderlich, wenn ``save=True``).
        save: Ergebnis nach ``data_file`` schreiben.
        verbose: Fortschritt/Kurzstatistik ausgeben.

    Returns:
        Das aktualisierte ``layout_data``-Dict.
    """
    n_cols = 0
    for key, entry in layout_data.items():
        measure_plate_tilt(entry)
        ref = entry.get('tilt_reference', {})
        used = ref.get('n_columns_used', 0)
        n_cols += used
        if verbose and used:
            msg = f"[{key}] {used} nutzbare Kolumnen, Plattenschiefe {ref['plate_skew_deg']}°"
            bskew = ref.get('baseline_skew_deg')
            if bskew is not None:
                diff = round(ref['plate_skew_deg'] - bskew, 3)
                msg += (f" | Baseline-Horizontale {bskew}° "
                        f"(Δ Oberkante−Baseline {diff:+}°, {ref['n_columns_with_baseline']} Kol. mit Zeilen)")
            print(msg)

    if save:
        if data_file is None:
            raise ValueError("data_file required when save=True.")
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(layout_data, f, indent=2, ensure_ascii=False)
        if verbose:
            print(f"\n{n_cols} Kolumnen vermessen -> {data_file}")

    return layout_data
