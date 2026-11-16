"""Minimal FHIR R4 research export; no invented diagnosis or risk probability."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def _uid():
    return str(uuid.uuid4())


def build_triage_bundle(triage_result, quality, *, age=None, name="", symptoms=()):
    """Bundle: Patient, non-clinical quality Observation, QuestionnaireResponse,
    and a Communication containing informational guidance only.
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    pid, qid, qrid, cid = (_uid() for _ in range(4))
    patient = {"resourceType": "Patient", "id": pid}
    if name and name.strip():
        patient["name"] = [{"text": name.strip()}]
    items = [
        {"linkId": "symptom-" + code, "text": code,
         "answer": [{"valueBoolean": True}]} for code in sorted(set(symptoms))
    ]
    if age is not None:
        items.append({"linkId": "age", "text": "Age in years",
                      "answer": [{"valueInteger": int(age)}]})
    qr = {
        "resourceType": "QuestionnaireResponse", "id": qrid,
        "status": "completed", "subject": {"reference": "urn:uuid:" + pid},
        "authored": now, "item": items,
    }
    obs = {
        "resourceType": "Observation", "id": qid, "status": "preliminary",
        "code": {"text": "Experimental technical photograph quality gate"},
        "subject": {"reference": "urn:uuid:" + pid}, "effectiveDateTime": now,
        "valueBoolean": bool(quality["ok"]),
        "note": [{"text": (
            "Technical photo quality only; anatomy and disease not assessed. "
            "Blur variance: " + str(quality["sharpness"]) +
            "; brightness: " + str(quality["brightness"])
        )}],
    }
    comm = {
        "resourceType": "Communication", "id": cid, "status": "completed",
        "subject": {"reference": "urn:uuid:" + pid}, "sent": now,
        "payload": [{"contentString": (
            "Prototype, non-diagnostic symptom guidance. " +
            triage_result["title"] + ". " + triage_result["action"] +
            " " + triage_result["image_note"]
        )}],
    }
    resources = [patient, obs, qr, comm]
    return {
        "resourceType": "Bundle", "type": "collection", "timestamp": now,
        "entry": [{"fullUrl": "urn:uuid:" + r["id"], "resource": r}
                  for r in resources],
    }
