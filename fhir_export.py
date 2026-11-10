"""
توليد FHIR R4 Bundle من نتيجة فاحص.

قواعد الأمان:
- الحالة الرمادية لا تُكتب أبدًا كاحتمال 0؛ يُحذف الاحتمال ويُوضَّح السبب.
- القيمة الغائبة في Observation تُكتب بـ dataAbsentReason لا بصفر.
"""
import uuid
from datetime import datetime, timezone

UCUM = "http://unitsofmeasure.org"
LOINC = "http://loinc.org"
LOCAL_CS = "http://fahes.local/CodeSystem"
RISK_PROB_CS = "http://terminology.hl7.org/CodeSystem/risk-probability"
DATA_ABSENT_CS = "http://terminology.hl7.org/CodeSystem/data-absent-reason"

# ترجمة ألوان فاحص إلى رموز risk-probability المعتمدة في FHIR
COLOR_TO_RISK = {
    "green": ("low", "Low likelihood"),
    "yellow": ("moderate", "Moderate likelihood"),
    "red": ("high", "High likelihood"),
}


def _uid() -> str:
    return str(uuid.uuid4())


def _observation(oid, pid, now, code, value=None, unit=None, ucum=None,
                 absent_text=None, status="final"):
    res = {
        "resourceType": "Observation",
        "id": oid,
        "status": status,
        "code": code,
        "subject": {"reference": f"urn:uuid:{pid}"},
        "effectiveDateTime": now,
    }
    if value is None:
        res["dataAbsentReason"] = {
            "coding": [{"system": DATA_ABSENT_CS, "code": "unknown",
                        "display": "Unknown"}],
            "text": absent_text or "القيمة غير متاحة",
        }
    else:
        q = {"value": value, "unit": unit}
        if ucum:
            q.update({"system": UCUM, "code": ucum})
        res["valueQuantity"] = q
    return {"fullUrl": f"urn:uuid:{oid}", "resource": res}


def build_fhir_bundle(result: dict, patient_info: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    pid, ra_id, dr_id = _uid(), _uid(), _uid()
    comp = result["components"]
    is_gray = result.get("risk_score") is None

    # Patient
    patient = {"resourceType": "Patient", "id": pid}
    if patient_info.get("name"):
        patient["name"] = [{"text": patient_info["name"]}]
    if patient_info.get("gender"):
        patient["gender"] = patient_info["gender"]
    if patient_info.get("birth_date"):
        patient["birthDate"] = patient_info["birth_date"]
    entries = [{"fullUrl": f"urn:uuid:{pid}", "resource": patient}]

    obs_entries = []

    # جودة الصورة
    obs_entries.append(_observation(
        _uid(), pid, now,
        {"coding": [{"system": LOCAL_CS, "code": "fahes-image-quality",
                     "display": "Fundus image quality score"}]},
        value=patient_info.get("image_quality"), unit="score", ucum="1",
        absent_text="لم تُحسب جودة الصورة"))

    # تقييم الشبكية — غائب عند رفض الصورة، و«مبدئي» عند انخفاض الثقة
    image_val = comp.get("image")
    obs_entries.append(_observation(
        _uid(), pid, now,
        {"coding": [{"system": LOCAL_CS, "code": "fahes-dr-image-probability",
                     "display": "Diabetic retinopathy probability from fundus image"}]},
        value=image_val, unit="probability", ucum="1",
        absent_text=result.get("message"),
        status="preliminary" if result.get("status") == "indeterminate_confidence" else "final"))

    # بيانات الساعة
    wearable = [
        ("8867-4", "Heart rate", patient_info.get("hr"), "beats/min", "/min"),
        ("55423-8", "Number of steps", patient_info.get("steps"), "steps", "{steps}"),
        ("80404-7", "Heart rate variability", patient_info.get("hrv"), "ms", "ms"),
        ("93832-4", "Sleep duration", patient_info.get("sleep_h"), "h", "h"),
    ]
    for code, display, value, unit, ucum in wearable:
        if value is None:
            continue
        obs_entries.append(_observation(
            _uid(), pid, now,
            {"coding": [{"system": LOINC, "code": code, "display": display}]},
            value=value, unit=unit, ucum=ucum))

    entries.extend(obs_entries)
    obs_refs = [{"reference": e["fullUrl"]} for e in obs_entries]

    # RiskAssessment
    prediction = {"outcome": {"text": "Diabetic retinopathy risk"}}
    if is_gray:
        prediction["rationale"] = ("Indeterminate — no risk estimate issued. "
                                   "This is NOT a low-risk result. " + result.get("message", ""))
    else:
        code, display = COLOR_TO_RISK[result["color"]]
        prediction["probabilityDecimal"] = result["risk_score"]
        prediction["qualitativeRisk"] = {
            "coding": [{"system": RISK_PROB_CS, "code": code, "display": display}],
            "text": result.get("color_ar"),
        }
    entries.append({
        "fullUrl": f"urn:uuid:{ra_id}",
        "resource": {
            "resourceType": "RiskAssessment",
            "id": ra_id,
            "status": "preliminary" if is_gray else "final",
            "subject": {"reference": f"urn:uuid:{pid}"},
            "occurrenceDateTime": now,
            "method": {"text": "FAHES multi-signal fusion (0.6 image + 0.2 wearable + 0.2 EHR)"},
            "basis": obs_refs,
            "prediction": [prediction],
            "note": [{"text": r} for r in result.get("reasons", [])],
        },
    })

    # DiagnosticReport — يشير إلى الملاحظات عبر result (basedOn للطلبات فقط)
    entries.append({
        "fullUrl": f"urn:uuid:{dr_id}",
        "resource": {
            "resourceType": "DiagnosticReport",
            "id": dr_id,
            "status": "preliminary",
            "code": {"text": "FAHES Retinal Screening Report"},
            "subject": {"reference": f"urn:uuid:{pid}"},
            "effectiveDateTime": now,
            "issued": now,
            "result": obs_refs,
            "conclusion": result.get("message", ""),
        },
    })

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": now,
        "entry": entries,
    }
