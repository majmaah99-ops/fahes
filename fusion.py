"""
منطق الدمج لـ«فاحص» — ثلاث بوابات + إعادة توزيع آمنة.
"""
from typing import Optional

def calculate_risk(
    image_score: float,
    image_quality: float,
    model_confidence: float,
    wearable_score: float,
    ehr_score: float,
) -> dict:
    """
    image_score       : 0–1 (احتمال اعتلال شبكية)
    image_quality     : 0–1 (Laplacian variance مُطبَّع)
    model_confidence  : 0–1 (ثقة النموذج — بافتراض المعايرة)
    wearable_score    : 0–1 (خطر من بيانات الساعة)
    ehr_score         : 0–1 (خطر من السجل)
    """
    # بوابة 1: جودة الصورة
    if image_quality < 0.6:
        return {
            "status": "indeterminate_image",
            "risk_score": None,
            "partial_signal": round(0.5 * wearable_score + 0.5 * ehr_score, 3),
            "color": "gray",
            "color_ar": "رمادي",
            "message": "تقييم الشبكية غير متاح — أعد التصوير",
            "reasons": ["جودة الصورة منخفضة"],
            "requires_human_review": True,
            "components": {
                "image": None,
                "wearable": round(wearable_score, 3),
                "ehr": round(ehr_score, 3),
            },
        }

    # بوابة 2: ثقة النموذج
    if model_confidence < 0.7:
        return {
            "status": "indeterminate_confidence",
            "risk_score": None,
            "partial_signal": None,
            "color": "gray",
            "color_ar": "رمادي",
            "message": "غير حاسم — النموذج غير واثق، مراجعة بشرية",
            "reasons": ["ثقة النموذج منخفضة"],
            "requires_human_review": True,
            "components": {
                "image": round(image_score, 3),
                "wearable": round(wearable_score, 3),
                "ehr": round(ehr_score, 3),
            },
        }

    # بوابة 3: الحساب الطبيعي
    risk = 0.6 * image_score + 0.2 * wearable_score + 0.2 * ehr_score

    if risk < 0.35:
        color, color_ar = "green", "أخضر"
        message = "خطر منخفض — متابعة روتينية سنوية"
    elif risk <= 0.65:
        color, color_ar = "yellow", "أصفر"
        message = "يستدعي تقييمًا — مراجعة طبيب خلال أسبوعين"
    else:
        color, color_ar = "red", "أحمر"
        message = "خطر مرتفع — إحالة عاجلة لطبيب عيون"

    # الأسباب الثلاثة (مفسَّرة)
    reasons = []
    if image_score > 0.6:
        reasons.append(f"مؤشرات اعتلال شبكية في الصورة ({image_score:.2f})")
    if wearable_score > 0.5:
        reasons.append(f"مؤشرات سلوكية غير مستقرة من الساعة ({wearable_score:.2f})")
    if ehr_score > 0.5:
        reasons.append(f"عوامل خطر مرتفعة في السجل ({ehr_score:.2f})")
    if not reasons:
        reasons.append("لا توجد مؤشرات خطر جوهرية")

    return {
        "status": "computed",
        "risk_score": round(risk, 3),
        "partial_signal": None,
        "color": color,
        "color_ar": color_ar,
        "message": message,
        "reasons": reasons,
        "requires_human_review": color in ("red",),
        "components": {
            "image": round(image_score, 3),
            "wearable": round(wearable_score, 3),
            "ehr": round(ehr_score, 3),
        },
    }
