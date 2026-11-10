"""
منطق الدمج لـ«فاحص» — بوابة الصلاحية + ثلاث بوابات.

المبدأ: كل حالة رمادية تعني «لا نعرف» وليست «سليم»؛ لذلك risk_score = None
فيها دائمًا، ولا يجوز لأي طبقة لاحقة (العرض، FHIR) أن تحوّلها إلى صفر.
"""

QUALITY_THRESHOLD = 0.6
CONFIDENCE_THRESHOLD = 0.7
GREEN_MAX = 0.35
YELLOW_MAX = 0.65


def _components(image, wearable, ehr):
    return {
        "image": None if image is None else round(image, 3),
        "wearable": round(wearable, 3),
        "ehr": round(ehr, 3),
    }


def _gray(status, message, reason, image, wearable, ehr, partial=None):
    return {
        "status": status,
        "risk_score": None,
        "partial_signal": partial,
        "color": "gray",
        "color_ar": "رمادي",
        "message": message,
        "reasons": [reason],
        "requires_human_review": True,
        "components": _components(image, wearable, ehr),
    }


def calculate_risk(
    image_score: float,
    image_quality: float,
    model_confidence: float,
    wearable_score: float,
    ehr_score: float,
    is_fundus: bool = True,
) -> dict:
    """
    image_score       : 0–1 (احتمال اعتلال شبكية)
    image_quality     : 0–1 (تباين Laplacian داخل منطقة الشبكية، مُطبَّع)
    model_confidence  : 0–1 (ثقة النموذج — بافتراض المعايرة)
    wearable_score    : 0–1 (خطر من بيانات الساعة)
    ehr_score         : 0–1 (خطر من السجل)
    is_fundus         : هل الصورة صورة قاع عين أصلًا؟
    """
    # إشارة جزئية من الساعة والسجل فقط — للعرض المساند، ليست درجة خطر
    partial = round(0.5 * wearable_score + 0.5 * ehr_score, 3)

    # بوابة 0: صلاحية الصورة
    if not is_fundus:
        return _gray("invalid_image",
                     "الصورة المرفوعة ليست صورة قاع عين — ارفع صورة شبكية",
                     "الصورة لا تبدو صورة قاع عين",
                     None, wearable_score, ehr_score, partial)

    # بوابة 1: جودة الصورة
    if image_quality < QUALITY_THRESHOLD:
        return _gray("indeterminate_image",
                     "تقييم الشبكية غير متاح — أعد التصوير",
                     f"جودة الصورة منخفضة ({image_quality:.2f})",
                     None, wearable_score, ehr_score, partial)

    # بوابة 2: ثقة النموذج
    if model_confidence < CONFIDENCE_THRESHOLD:
        return _gray("indeterminate_confidence",
                     "غير حاسم — النموذج غير واثق، مراجعة بشرية",
                     f"ثقة النموذج منخفضة ({model_confidence:.2f})",
                     image_score, wearable_score, ehr_score, partial)

    # بوابة 3: الحساب الطبيعي
    risk = 0.6 * image_score + 0.2 * wearable_score + 0.2 * ehr_score

    if risk < GREEN_MAX:
        color, color_ar = "green", "أخضر"
        message = "خطر منخفض — متابعة روتينية سنوية"
    elif risk <= YELLOW_MAX:
        color, color_ar = "yellow", "أصفر"
        message = "يستدعي تقييمًا — مراجعة طبيب خلال أسبوعين"
    else:
        color, color_ar = "red", "أحمر"
        message = "خطر مرتفع — إحالة عاجلة لطبيب عيون"

    # الأسباب (مفسَّرة)
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
        "requires_human_review": color == "red",
        "components": _components(image_score, wearable_score, ehr_score),
    }
