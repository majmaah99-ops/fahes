"""
توليد FHIR R4 Bundle من نتيجة فاحص.
"""
import uuid
from datetime import datetime

def build_fhir_bundle(result: dict, patient_info: dict) -> dict:
    now = datetime.utcnow().isoformat() + "Z"
    pid = str(uuid.uuid4())
    obs_ids = [str(uuid.uuid4()) for _ in range(6)]
    ra_id = str(uuid.uuid4())
    dr_id = str(uuid.uuid4())

    entries = []

    # Patient
    entries.append({
        "fullUrl": f"urn:uuid:{pid}",
        "resource": {
            "resourceType": "Patient",
            "id": pid,
            "name": [{"text": patient_info.get("name", "خالد")}],
            "gender": patient_info.get("gender", "male"),
            "birthDate": patient_info.get("birth_date", "1973-01-01"),
        },
    })

    comp = result["components"]
    # Observation 1: جودة الصورة
    entries.append({
        "fullUrl": f"urn:uuid:{obs_ids[0]}",
        "resource": {
            "resourceType": "Observation",
            "id": obs_ids[0],
            "status": "final",
            "code": {"coding": [{"system": "http://fahes.local/CodeSystem",
                                 "code": "fa7es-image-quality",
                                 "display": "Image Quality Score"}]},
            "subject": {"reference": f"urn:uuid:{pid}"},
            "effectiveDateTime": now,
            "valueQuantity": {"value": patient_info.get("image_quality", 0.85),
                              "unit": "score"},
        },
    })

    # Observation 2: تحليل الشبكية
    entries.append({
        "fullUrl": f"urn:uuid:{obs_ids[1]}",
        "resource": {
            "resourceType": "Observation",
            "id": obs_ids[1],
            "status": "final",
            "code": {"coding": [{"system": "http://snomed.info/sct",
                                 "code": "3081002",
                                 "display": "Retinal assessment"}]},
            "subject": {"reference": f"urn:uuid:{pid}"},
            "effectiveDateTime": now,
            "valueQuantity": {"value": comp.get("image") or 0,
                              "unit": "probability"},
        },
    })

    # Observations 3-5: الساعة
    wearable_codes = [
        ("8867-4", "Heart rate", "beats/min", patient_info.get("hr", 78)),
        ("55423-8", "Steps in 24h", "steps", patient_info.get("steps", 4200)),
        ("80404-7", "Heart rate variability", "ms", patient_info.get("hrv", 32)),
    ]
    for i, (code, display, unit, value) in enumerate(wearable_codes, start=2):
        entries.append({
            "fullUrl": f"urn:uuid:{obs_ids[i]}",
            "resource": {
                "resourceType": "Observation",
                "id": obs_ids[i],
                "status": "final",
                "code": {"coding": [{"system": "http://loinc.org",
                                     "code": code, "display": display}]},
                "subject": {"reference": f"urn:uuid:{pid}"},
                "effectiveDateTime": now,
                "valueQuantity": {"value": value, "unit": unit},
            },
        })

    # RiskAssessment
    entries.append({
        "fullUrl": f"urn:uuid:{ra_id}",
        "resource": {
            "resourceType": "RiskAssessment",
            "id": ra_id,
            "status": "final",
            "subject": {"reference": f"urn:uuid:{pid}"},
            "occurrenceDateTime": now,
            "method": {"text": "FAHES multi-signal fusion"},
            "prediction": [{
                "outcome": {"text": "Diabetic retinopathy risk"},
                "probabilityDecimal": result.get("risk_score") or 0,
                "qualitativeRisk": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/risk-probability",
                                "code": result["color"]}]
                },
            }],
            "note": [{"text": r} for r in result.get("reasons", [])],
        },
    })

    # DiagnosticReport
    entries.append({
        "fullUrl": f"urn:uuid:{dr_id}",
        "resource": {
            "resourceType": "DiagnosticReport",
            "id": dr_id,
            "status": "preliminary",
            "subject": {"reference": f"urn:uuid:{pid}"},
            "effectiveDateTime": now,
            "code": {"text": "FAHES Retinal Screening Report"},
            "conclusion": result.get("message", ""),
            "basedOn": [{"reference": f"urn:uuid:{ra_id}"}],
        },
    })

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": now,
        "entry": entries,
    }
