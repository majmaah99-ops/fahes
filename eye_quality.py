"""Heuristic photograph quality checks; NOT proof of ocular anatomy or diagnostic value."""
from __future__ import annotations

import cv2
import numpy as np

MAX_DIMENSION = 512
MIN_SOURCE_SIDE = 320


def assess_photo_quality(rgb: np.ndarray, image_type: str) -> dict:
    """Check exposure, blur and resolution with explicitly experimental thresholds.

    Input: H x W x 3 uint8 RGB. No eye recognition or disease detection occurs.
    """
    if image_type not in {"external", "fundus"}:
        raise ValueError("image_type must be 'external' or 'fundus'")
    if not isinstance(rgb, np.ndarray) or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("Expected an RGB image array")
    if rgb.dtype != np.uint8:
        raise ValueError("Expected uint8 pixel values")
    height, width = rgb.shape[:2]
    if height < 1 or width < 1:
        raise ValueError("Empty image")

    scale = min(1.0, MAX_DIMENSION / max(height, width))
    sw, sh = max(1, int(width * scale)), max(1, int(height * scale))
    small = cv2.resize(rgb, (sw, sh), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)

    # Exclude the very edges: fundus photos typically have dark framing.
    y0, y1 = int(sh * 0.1), max(int(sh * 0.9), int(sh * 0.1) + 1)
    x0, x1 = int(sw * 0.1), max(int(sw * 0.9), int(sw * 0.1) + 1)
    roi = gray[y0:y1, x0:x1]

    if image_type == "fundus":
        mask = roi > 20
        coverage = float(np.mean(mask))
        pixels = roi[mask] if np.any(mask) else roi.reshape(-1)
        lap = cv2.Laplacian(roi, cv2.CV_64F)
        edge_pixels = lap[mask] if np.any(mask) else lap.reshape(-1)
    else:
        coverage = 1.0
        pixels = roi.reshape(-1)
        edge_pixels = cv2.Laplacian(roi, cv2.CV_64F).reshape(-1)

    brightness = float(pixels.mean()) if pixels.size else 0.0
    highlight_fraction = float(np.mean(pixels >= 248)) if pixels.size else 0.0
    sharpness = float(np.var(edge_pixels)) if edge_pixels.size else 0.0

    warnings = []
    if min(height, width) < MIN_SOURCE_SIDE:
        warnings.append("دقة الصورة منخفضة؛ اقترب من العين دون استخدام فلاش قوي.")
    if brightness < 45:
        warnings.append("الإضاءة منخفضة؛ أعد التصوير بضوء موزع.")
    if brightness > 215 or highlight_fraction > 0.25:
        warnings.append("هناك إضاءة مفرطة أو انعكاس قوي؛ تجنب الفلاش المباشر.")
    if sharpness < 35:
        warnings.append("التفاصيل تبدو غير حادة؛ ثبّت الهاتف وأعد التركيز.")
    if image_type == "fundus" and coverage < 0.25:
        warnings.append("منطقة الصورة الظاهرة صغيرة جدًا أو مظلمة؛ تأكد من المحاذاة.")

    return {
        "ok": not warnings,
        "brightness": round(brightness, 1),
        "sharpness": round(sharpness, 1),
        "highlight_fraction": round(highlight_fraction, 3),
        "visible_fraction": round(coverage, 3),
        "source_width": width,
        "source_height": height,
        "warnings": warnings,
        "quality_rule": "experimental_heuristic_v1",
        "anatomy_verified": False,
    }
