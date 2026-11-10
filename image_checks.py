"""
فحوصات الصورة قبل التحليل — جودة الصورة داخل منطقة الشبكية فقط.

لماذا القناع؟ صور قاع العين فيها خلفية سوداء واسعة وحافة حادة بين الدائرة
والخلفية؛ حساب Laplacian على الصورة كاملة يقيس هذه الحافة لا وضوح الشبكية.
ولماذا التصغير إلى 512؟ ليصبح المقياس مستقلًا عن دقة الكاميرا.
"""
import cv2
import numpy as np

# مرجع التطبيع: تباين Laplacian ≥ 100 (داخل القناع، على 512px) = جودة 1.0
# عُيّر على sample_images: الصور الأصلية 181–1593، وبعد تمويه Gaussian σ=2
# تهبط الصور منخفضة الدقة إلى 9–28 (تُرفض). العتبة 0.6 ⇐ تباين ≥ 60.
QUALITY_REFERENCE = 100.0
WORK_SIZE = 512
BACKGROUND_THRESHOLD = 20      # بكسلات أغمق من هذا تُعدّ خلفية
MIN_RETINA_FRACTION = 0.25     # أقل من ربع الصورة شبكية ⇐ الجودة صفر


def assess_quality(rgb: np.ndarray) -> dict:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    scale = WORK_SIZE / max(h, w)
    small = cv2.resize(gray, (max(1, int(w * scale)), max(1, int(h * scale))),
                       interpolation=cv2.INTER_AREA)

    mask = (small > BACKGROUND_THRESHOLD).astype(np.uint8)
    # تآكل القناع لإبعاد حافة الدائرة عن الحساب
    mask = cv2.erode(mask, np.ones((15, 15), np.uint8)).astype(bool)
    retina_fraction = float(mask.mean())

    if retina_fraction < MIN_RETINA_FRACTION:
        return {"quality": 0.0, "laplacian_var": 0.0,
                "retina_fraction": round(retina_fraction, 3)}

    lap_var = float(cv2.Laplacian(small, cv2.CV_64F)[mask].var())
    return {
        "quality": float(min(lap_var / QUALITY_REFERENCE, 1.0)),
        "laplacian_var": round(lap_var, 1),
        "retina_fraction": round(retina_fraction, 3),
    }
