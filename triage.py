"""Non-diagnostic, symptom-based routing for the FAHES research prototype.

This module does NOT infer diabetes, refraction, retinal pathology, or clinical
risk from photographs. Urgent symptoms always override a failed image-quality gate.
"""
from __future__ import annotations

SYMPTOMS = {
    "sudden_loss": "فقدان مفاجئ أو انخفاض حاد في النظر",
    "severe_pain": "ألم شديد في العين",
    "curtain": "ظهور ستار أو ظل جديد يحجب جزءًا من الرؤية",
    "chemical": "تعرض العين لمادة كيميائية",
    "trauma": "إصابة مباشرة أو نافذة في العين",
    "flashes_floaters": "ومضات جديدة أو زيادة مفاجئة في العوائم",
    "blur": "تشوش مستمر أو متكرر في الرؤية",
    "redness": "احمرار أو انزعاج مستمر في العين",
    "thirst": "عطش زائد وتبول متكرر",
}

URGENT = frozenset({"sudden_loss", "severe_pain", "curtain", "chemical", "trauma", "flashes_floaters"})
FOLLOW_UP = frozenset({"blur", "redness", "thirst"})


def triage(symptoms, has_diabetes=False, image_quality_ok=False, image_type="external"):
    """Return a guidance priority, never a medical diagnosis or a disease score.

    The image-quality flag affects photo recapture advice only; it must not hide
    a symptom-triggered urgent referral. Image type is user-declared, not inferred.
    """
    selected = set(symptoms or [])
    unknown = selected - SYMPTOMS.keys()
    if unknown:
        raise ValueError("Unknown symptom code(s): " + ", ".join(sorted(unknown)))
    if image_type not in {"external", "fundus"}:
        raise ValueError("Image type must be external or fundus")

    reasons = [SYMPTOMS[s] for s in SYMPTOMS if s in selected]
    urgent = bool(selected & URGENT)
    follow_up = bool(selected & FOLLOW_UP) or bool(has_diabetes)

    if urgent:
        priority = "urgent"
        title = "أعراض إنذار — اطلب تقييمًا عاجلًا"
        action = "توجّه إلى الطوارئ أو خدمة عيون عاجلة الآن، ولا تنتظر نتيجة تحليل الصورة."
        if "chemical" in selected:
            action += " إذا تعرضت العين لمادة كيميائية فابدأ غسلها فورًا بماء جارٍ، مع طلب المساعدة العاجلة."
    elif follow_up:
        priority = "appointment"
        title = "يُنصح بالتواصل مع مختص صحي"
        action = "احجز تقييمًا لدى طبيب العيون أو الرعاية الأولية وفق الأعراض والتاريخ المرضي."
        if "thirst" in selected:
            action += " ناقش إجراء قياس سكر الدم أو HbA1c؛ صورة العين لا تقيس السكر."
        if has_diabetes:
            action += " وجود السكري يستلزم متابعة الشبكية حسب خطة الفريق المعالج."
    else:
        priority = "informational"
        title = "لا توجد أعراض إنذار مُبلّغ عنها"
        action = "هذه ليست شهادة بسلامة العين؛ احتفظ بمواعيد فحوص النظر والشبكية الموصى بها طبيًا."

    if has_diabetes:
        reasons.append("إبلاغ المستخدم بوجود تشخيص سابق بالسكري")
    if not reasons:
        reasons.append("لم يُبلَّغ عن أعراض أو تشخيص سكري في الاستبيان")

    return {
        "priority": priority,
        "title": title,
        "action": action,
        "reasons": reasons,
        "needs_retake": not image_quality_ok,
        "image_type": image_type,
        "image_note": (
            "الصورة الخارجية لا تُظهر الشبكية ولا تُحدد قوة النظر أو HbA1c."
            if image_type == "external" else
            "يتطلب تفسير صورة قاع العين اختصاصيًا أو نموذجًا سريريًا متحققًا؛ لم يجرِ هذا التطبيق كشف الآفات."
        ),
        "disease_probability": None,
        "medical_diagnosis": None,
        "validated_model": False,
    }
