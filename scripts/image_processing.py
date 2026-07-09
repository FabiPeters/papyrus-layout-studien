"""
image_processing.py
-------------------
Bildverarbeitung für die Papyrus-Layoutstudien.

Segmentiert ein auf einem Leuchttisch fotografiertes Papyrusfragment vom hellen
Hintergrund, erzeugt eine Binärmaske und leitet daraus die Bounding-Box sowie
Flächen- und Randmaße ab. Alternativ kann eine manuell in ``layout_data.json``
hinterlegte Bounding-Box verwendet werden (``bbox_measurement: "manual"``).

Aufbau des Moduls
-----------------
1. Parameter        – :class:`SegmentationParams` bündelt alle Stellschrauben.
2. Kern-CV-Funktionen – Streifenerkennung, Maskenerzeugung, Komponentenfilter.
3. Messfunktionen    – :func:`compute_measurements`, :func:`merge_measurements`.
4. Orchestrierung    – :func:`process_entry` (eine Datei) und
   :func:`process_layout_data` (kompletter Lauf inkl. I/O).

Typische Nutzung aus dem Notebook::

    import image_processing as ip
    layout_data = ip.process_layout_data(layout_data, PROJECT_ROOT, DATA_FILE)

Zum Tunen einzelner Bilder lassen sich die Parameter überschreiben::

    params = ip.SegmentationParams(min_component_ratio=0.05)
    layout_data = ip.process_layout_data(layout_data, PROJECT_ROOT, DATA_FILE,
                                         params=params, overwrite_masks=True)

Abhängigkeiten: ``opencv-python``, ``numpy``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# 1. Parameter
# ---------------------------------------------------------------------------

@dataclass
class SegmentationParams:
    """Stellschrauben der Segmentierungs-Pipeline.

    Die Segmentierung hängt von der Bildqualität und den Lichtverhältnissen ab;
    die folgenden Werte können je nach Fragment angepasst werden.

    Attributes:
        strip_threshold_factor: Steuert die Erkennung des Info-Streifens am
            unteren Bildrand. Bei nicht sauber entferntem Streifen senken.
        strip_min_height: Mindesthöhe (px) eines erkannten Streifens; kürzere
            dunkle Läufe werden als Papyruskante gewertet, nicht als Streifen.
        gray_close_kernel_size: Überbrückt helle Stellen innerhalb des
            Fragments. Vergrößern, wenn das Fragment von hellen Flecken
            „aufgefressen“ wird.
        binary_fill_kernel_size: Füllt kleine Löcher und Risse in der Maske.
        min_component_ratio: Rauschfilter. Behält Komponenten, deren Fläche
            mindestens diesen Anteil der größten Komponente erreicht. Bei vielen
            kleinen Artefakten erhöhen (z. B. 0.05 oder 0.1).
    """

    strip_threshold_factor: float = 0.85
    strip_min_height: int = 10
    gray_close_kernel_size: tuple[int, int] = (51, 51)
    binary_fill_kernel_size: tuple[int, int] = (15, 15)
    min_component_ratio: float = 0.02


#: Voreingestellte Parameter, falls keine eigenen übergeben werden.
DEFAULT_PARAMS = SegmentationParams()


# ---------------------------------------------------------------------------
# 2. Kern-CV-Funktionen
# ---------------------------------------------------------------------------

def detect_strip_row(gray: np.ndarray, params: SegmentationParams = DEFAULT_PARAMS) -> int | None:
    """Erkennt die Oberkante des Info-Streifens am unteren Bildrand.

    Returns:
        Zeilenindex der Streifen-Oberkante oder ``None``, wenn kein Streifen
        gefunden wird.
    """
    h = gray.shape[0]
    row_mean = gray.mean(axis=1).astype(float)  # (h,)

    # Hintergrundhelligkeit aus den obersten 10 Zeilen schätzen
    top_n = 10  # max(1, h // 10)
    bg_brightness = float(row_mean[:top_n].mean())
    dark_threshold = bg_brightness * params.strip_threshold_factor

    is_dark = row_mean < dark_threshold  # True dort, wo es streifenartig dunkel ist

    # Von unten nach oben laufen, helle Randzeilen zunächst überspringen
    run_end = h - 1
    while run_end >= 0 and not is_dark[run_end]:
        run_end -= 1

    if run_end < 0:
        return None  # unten bereits hell — kein Streifen

    # Lauf nach oben ausdehnen, solange Zeilen dunkel bleiben
    run_start = run_end
    while run_start > 0 and is_dark[run_start - 1]:
        run_start -= 1

    strip_height = run_end - run_start + 1
    if strip_height < params.strip_min_height:
        return None  # zu kurz für einen echten Streifen — vermutlich Papyruskante

    return int(run_start)


def blank_strip(gray: np.ndarray, strip_row: int) -> np.ndarray:
    """Gibt eine Kopie von ``gray`` zurück, in der alle Zeilen ab ``strip_row``
    auf 255 (weiß / Hintergrundniveau) gesetzt sind."""
    cleaned = gray.copy()
    cleaned[strip_row:, :] = 255
    return cleaned


def filter_components(binary: np.ndarray, params: SegmentationParams = DEFAULT_PARAMS,
                     verbose: bool = True) -> np.ndarray:
    """Behält alle zusammenhängenden Komponenten, deren Fläche mindestens
    ``params.min_component_ratio`` mal der Fläche der größten Komponente beträgt."""
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary, connectivity=8
    )
    if num_labels < 2:
        return binary  # nur Hintergrund — nichts zu filtern

    areas = stats[1:, cv2.CC_STAT_AREA]
    largest_area = int(areas.max())
    size_cutoff = largest_area * params.min_component_ratio

    mask = np.zeros_like(binary)
    kept = 0
    for label_idx, area in enumerate(areas, start=1):
        if area >= size_cutoff:
            mask[labels == label_idx] = 255
            kept += 1

    if verbose:
        n_total = num_labels - 1
        print(f"  Components       : {kept} kept / {n_total} total  "
              f"(cutoff: {int(size_cutoff):,} px,  largest: {largest_area:,} px)")

    return mask


def create_binary_mask(img: np.ndarray, params: SegmentationParams = DEFAULT_PARAMS,
                      verbose: bool = True) -> np.ndarray:
    """Segmentiert das/die Fragment(e) vom hellen Leuchttisch-Hintergrund."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # --- Schritt 1: Info-Streifen ausblenden, damit er die Schwellung nicht verzerrt
    strip_row = detect_strip_row(gray, params)
    if strip_row is not None:
        strip_h = gray.shape[0] - strip_row
        if verbose:
            print(f"  Strip detected   : row {strip_row}  ({strip_h} px tall) — blanked")
        gray = blank_strip(gray, strip_row)
    elif verbose:
        print(f"  Strip detected   : none")

    # --- Schritt 2: Grauwert-Closing, um helle Stellen auf dem Fragment auszugleichen
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, params.gray_close_kernel_size)
    gray_closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, close_kernel)

    # --- Schritt 3: Otsu-Schwelle aus geglättetem Bild, angewandt auf das Original
    otsu_thresh, _ = cv2.threshold(
        gray_closed, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    _, binary = cv2.threshold(gray, int(otsu_thresh), 255, cv2.THRESH_BINARY_INV)

    # --- Schritt 4: Binär-Closing, um verbliebene Löcher im Fragment zu schließen
    fill_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, params.binary_fill_kernel_size)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, fill_kernel)

    # --- Schritt 5: Komponenten filtern, alle bedeutsamen Fragmentteile behalten
    binary = filter_components(binary, params, verbose=verbose)

    return binary


# ---------------------------------------------------------------------------
# 3. Messfunktionen
# ---------------------------------------------------------------------------

#: Schlüssel, die aus den Messungen in die JSON-Einträge geschrieben werden.
MEASUREMENT_KEYS = (
    "bbox_origin", "bbox_w", "bbox_h", "bbox_w_cm", "bbox_h_cm", "bbox_area_px",
    "extant_area_px", "coverage_pct",
    "margin_top", "margin_right", "margin_bottom", "margin_left",
    "n_mask_components",
)


def _px_to_cm(px: float, px_per_cm: float | None) -> float | None:
    """Rechnet einen px-Wert in cm um. Gibt ``None`` zurück, wenn keine Skala
    vorliegt (``px_per_cm`` ist ``None`` oder 0) — cm ist dann nicht bestimmbar."""
    if not px_per_cm:
        return None
    # 1 Nachkommastelle (mm): feinere Werte sind bei manueller Bbox Scheingenauigkeit.
    return round(px / px_per_cm, 1) + 0.0   # + 0.0 normalisiert -0.0 -> 0.0


def _measurements_from_bbox(x: int, y: int, w: int, h: int,
                            img_w: int, img_h: int,
                            extant_area: int, coverage: float,
                            px_per_cm: float | None = None) -> dict:
    """Baut das einheitliche Mess-Dict aus Bounding-Box und Flächenwerten.

    cm-Werte sind abgeleitet (px / px_per_cm) und werden hier — an der einzigen
    Stelle, an der die px-Maße entstehen — mitberechnet; ``None`` ohne Skala.
    """
    return {
        "bbox_origin":    [x, y],
        "bbox_w":         w,
        "bbox_h":         h,
        "bbox_w_cm":      _px_to_cm(w, px_per_cm),
        "bbox_h_cm":      _px_to_cm(h, px_per_cm),
        "bbox_area_px":   int(w * h),
        "extant_area_px": int(extant_area),
        "coverage_pct":   round(coverage, 2),
        "margin_top":     y,
        "margin_right":   img_w - (x + w),
        "margin_bottom":  img_h - (y + h),
        "margin_left":    x,
    }


def compute_measurements(binary: np.ndarray | None = None, entry: dict | None = None,
                        img_dims: tuple[int, int] | None = None) -> dict:
    """Leitet räumliche Maße aus der Binärmaske oder aus manuellen Bbox-Daten ab.

    Args:
        binary: Binärmaske aus der Segmentierung. ``None``, wenn manuelle Daten
            aus ``entry`` genutzt werden.
        entry: Layout-Daten-Eintrag (optional). Prüft auf manuelle Bbox-Konfiguration.
        img_dims: ``(img_width, img_height)``. Erforderlich, wenn ``entry`` übergeben wird.

    Returns:
        Dict mit Bbox-Maßen und abgeleiteten Werten.
    """
    # --- Manueller Bbox-Modus ---
    if entry is not None and entry.get('bbox_measurement') == 'manual':
        if 'bbox_manual' not in entry:
            raise ValueError("bbox_measurement set to 'manual' but bbox_manual data missing.")
        if img_dims is None:
            raise ValueError("img_dims required for manual bbox mode.")

        img_w, img_h = img_dims
        manual_data = entry['bbox_manual']

        x, y = manual_data['origin']
        w = manual_data['width']
        h = manual_data['height']
        bbox_area = int(w * h)

        # Im manuellen Modus wird coverage_pct auf 100 % gesetzt
        # (es wird angenommen, dass die gesamte Bbox Fragment ist).
        return _measurements_from_bbox(x, y, w, h, img_w, img_h,
                                       extant_area=bbox_area, coverage=100.0,
                                       px_per_cm=entry.get('px/cm'))

    # --- Automatischer Modus: aus Binärmaske berechnen ---
    if binary is None:
        raise ValueError("Either binary mask or manual bbox data must be provided.")

    coords = cv2.findNonZero(binary)
    if coords is None:
        raise ValueError("No fragment pixels found in the binary mask.")

    x, y, w, h = cv2.boundingRect(coords)
    img_h, img_w = binary.shape[:2]
    extant_area = int(np.count_nonzero(binary))
    bbox_area = int(w * h)
    coverage = 100.0 * extant_area / bbox_area if bbox_area > 0 else 0.0

    return _measurements_from_bbox(x, y, w, h, img_w, img_h,
                                   extant_area=extant_area, coverage=coverage,
                                   px_per_cm=(entry or {}).get('px/cm'))


def merge_measurements(entry: dict, measurements: dict) -> dict:
    """Schreibt Messwerte in den JSON-Eintrag, ohne andere Felder zu verändern."""
    for key in MEASUREMENT_KEYS:
        if key in measurements:
            entry[key] = measurements[key]
    return entry


# ---------------------------------------------------------------------------
# 4. Orchestrierung
# ---------------------------------------------------------------------------

def save_preview(img: np.ndarray, meas: dict, preview_path: Path,
                 params: SegmentationParams = DEFAULT_PARAMS) -> None:
    """Speichert ein Vorschaubild mit eingezeichneter Bounding-Box und – falls
    vorhanden – der erkannten Streifen-Oberkante."""
    preview = img.copy()
    x, y = meas["bbox_origin"]
    w, h = meas["bbox_w"], meas["bbox_h"]
    cv2.rectangle(preview, (x, y), (x + w, y + h), color=(0, 0, 255), thickness=3)

    gray_raw = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    strip_row = detect_strip_row(gray_raw, params)
    if strip_row is not None:
        cv2.line(preview, (0, strip_row), (preview.shape[1], strip_row),
                 color=(255, 80, 0), thickness=2)

    cv2.imwrite(str(preview_path), preview)


def process_entry(key: str, entry: dict, project_root: Path, masks_dir: Path,
                  params: SegmentationParams = DEFAULT_PARAMS,
                  overwrite_masks: bool = False, save_preview_img: bool = True,
                  verbose: bool = True) -> dict | None:
    """Verarbeitet einen einzelnen Layout-Eintrag.

    Wählt zwischen manuellem und automatischem Bbox-Modus, erzeugt bei Bedarf
    die Binärmaske (mit Caching) und schreibt die Messwerte in ``entry`` zurück.

    Returns:
        Den aktualisierten ``entry`` oder ``None``, wenn das Bild fehlt/unlesbar ist.
    """
    image_path = project_root / entry['image_file']
    mask_path = masks_dir / (image_path.stem + "_mask.png")

    if not image_path.exists():
        if verbose:
            print(f"MISSING image: {image_path}")
        return None

    img = cv2.imread(str(image_path))
    if img is None:
        if verbose:
            print(f"  ERROR: Could not read image '{image_path}'")
        return None

    img_h, img_w = img.shape[:2]
    use_manual_bbox = entry.get('bbox_measurement') == 'manual'

    if use_manual_bbox:
        if verbose:
            print(f"  Measurement mode: MANUAL (using bbox_manual data)")
        binary = None  # im manuellen Modus keine Maske
        meas = compute_measurements(entry=entry, img_dims=(img_w, img_h))
    else:
        # Vorhandene Maske wiederverwenden, falls Überschreiben deaktiviert ist
        skip_mask_generation = mask_path.exists() and not overwrite_masks
        if skip_mask_generation:
            if verbose:
                print(f"  Measurement mode: AUTOMATIC (using cached mask)")
            binary = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            meas = compute_measurements(binary=binary, entry=entry, img_dims=(img_w, img_h))
        else:
            if verbose:
                print(f"  Measurement mode: AUTOMATIC (segmentation)")
            binary = create_binary_mask(img, params, verbose=verbose)
            meas = compute_measurements(binary=binary, entry=entry, img_dims=(img_w, img_h))
            cv2.imwrite(str(mask_path), binary)

    # Bei mehreren Fragmenten (z. B. Platte T) umschliesst die Bbox den ganzen
    # Streubereich -> Hoehe/Breite sind nicht aussagekraeftig und werden unterdrueckt.
    if len(entry.get('fragment_data', [])) > 1:
        meas['bbox_w_cm'] = meas['bbox_h_cm'] = None

    # Fragmentierungsmaß: Zahl zusammenhaengender Maskenteile (nach Filterung).
    # 1 = zusammenhaengendes Blatt, >1 = physisch getrennte Stuecke. Im manuellen
    # Modus (keine Maske) nicht bestimmbar -> None.
    if binary is not None:
        n_labels, _ = cv2.connectedComponents(binary, connectivity=8)
        meas['n_mask_components'] = int(n_labels) - 1  # ohne Hintergrund
    else:
        meas['n_mask_components'] = None

    merge_measurements(entry, meas)

    if save_preview_img:
        preview_path = masks_dir / (image_path.stem + "_bbox_preview.png")
        save_preview(img, meas, preview_path, params)

    if verbose:
        print(f"  Done. Bbox area: {meas['bbox_area_px']:,} px2")

    return entry


def process_layout_data(data_file: Path | str | None, project_root: Path | str,
                        layout_data: dict | None = None,
                        params: SegmentationParams = DEFAULT_PARAMS,
                        overwrite_masks: bool = False, save_preview_img: bool = True,
                        save: bool = True, verbose: bool = True) -> dict:
    """Verarbeitet alle Einträge in ``layout_data`` und schreibt die Maße zurück.

    Dateibasiert: Ohne ``layout_data`` wird ``data_file`` selbst eingelesen und
    nach der Berechnung wieder geschrieben. Erzeugt den Maskenordner
    ``<project_root>/images/masks``, ruft für jeden Eintrag :func:`process_entry`
    auf und speichert das Ergebnis optional als JSON.

    Voraussetzung: ``collect_layout_data(...)`` muss gelaufen sein (liefert
    ``image_file`` je Platte). Schreibt Bbox-/Flächen-/Randmaße auf Platten-Ebene.

    Args:
        data_file: JSON-Datei zum Einlesen und Speichern. Erforderlich, wenn
            ``layout_data`` nicht übergeben oder ``save=True`` ist.
        project_root: Projektwurzel (Basis für ``image_file``-Pfade).
        layout_data: Optionales Override-Dict; wenn ``None``, aus ``data_file`` geladen.
        params: Segmentierungsparameter.
        overwrite_masks: ``True`` regeneriert alle Masken; ``False`` nutzt Cache.
        save_preview_img: Vorschaubilder mit Bbox/Streifen speichern.
        save: Ergebnis nach ``data_file`` schreiben.
        verbose: Fortschritt ausgeben.

    Returns:
        Das aktualisierte ``layout_data``-Dict.
    """
    if layout_data is None:
        if data_file is None or not Path(data_file).exists():
            raise FileNotFoundError(
                f"layout_data nicht übergeben und '{data_file}' nicht gefunden – "
                "zuerst collect_layout_data(...) ausführen.")
        with open(data_file, encoding='utf-8') as f:
            layout_data = json.load(f)
    project_root = Path(project_root)
    masks_dir = project_root / 'images' / 'masks'
    masks_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Processing images for {len(layout_data)} entries...")

    for key, entry in layout_data.items():
        if verbose:
            print(f"\n[{key}]")
        try:
            updated = process_entry(
                key, entry, project_root, masks_dir, params=params,
                overwrite_masks=overwrite_masks, save_preview_img=save_preview_img,
                verbose=verbose,
            )
            if updated is not None:
                layout_data[key] = updated
        except Exception as e:
            if verbose:
                print(f"  ERROR processing {key}: {e}")

    if save:
        if data_file is None:
            raise ValueError("data_file required when save=True.")
        data_file = Path(data_file)
        if verbose:
            print(f"\nWriting updated data to {data_file}")
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(layout_data, f, indent=2, ensure_ascii=False)

    return layout_data
