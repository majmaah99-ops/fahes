"""FAHES Vercel entrypoint: FastAPI + Arabic mobile frontend.

The API analyses only technical image quality. It does NOT detect diabetes,
retinopathy, visual acuity or other diseases. Symptom guidance is separate.
"""
from __future__ import annotations

import json
from io import BytesIO

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from PIL import Image, ImageOps, UnidentifiedImageError

from eye_quality import assess_photo_quality
from triage import triage
from triage_export import build_triage_bundle
from web_ui import PAGE

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 24_000_000
SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}

app = FastAPI(
    title="FAHES - Non-Diagnostic Eye Photo Triage",
    version="1.1.0",
    description="Experimental technical photo check and symptom-based advice, not a medical device.",
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def homepage():
    return HTMLResponse(PAGE, headers={"Cache-Control": "no-store"})


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "fahes", "diagnostic_model": False}


def _decode_image(raw: bytes) -> np.ndarray:
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("حجم الصورة يتجاوز 10 ميجابايت.")
    if not raw:
        raise ValueError("لم تُرسل صورة.")
    try:
        with Image.open(BytesIO(raw)) as source:
            if source.format not in SUPPORTED_IMAGE_FORMATS:
                raise ValueError("الصيغة غير مدعومة؛ استخدم JPG أو PNG أو WebP.")
            if source.width * source.height > MAX_PIXELS:
                raise ValueError("أبعاد الصورة كبيرة جدًا (الحد الأقصى 24 مليون بكسل).")
            img = ImageOps.exif_transpose(source).convert("RGB")
            return np.asarray(img)
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError("تعذّر قراءة الصورة؛ تأكد من أنها صورة سليمة.") from exc


@app.post("/api/screen")
async def screen(
    image_type: str = Form("external"),
    symptoms: str = Form("[]"),
    has_diabetes: bool = Form(False),
    age: str = Form(""),
    file: UploadFile | None = File(None),
):
    if image_type not in {"external", "fundus"}:
        raise HTTPException(status_code=422, detail="نوع الصورة غير مدعوم.")
    try:
        parsed = json.loads(symptoms)
        if not isinstance(parsed, list) or len(parsed) > 20 or not all(
            isinstance(value, str) for value in parsed
        ):
            raise ValueError("قائمة الأعراض غير صحيحة.")
        age_num = int(age.strip()) if age.strip() else None
        if age_num is not None and not (1 <= age_num <= 120):
            raise ValueError("العمر يجب أن يكون بين 1 و120 سنة.")
        if file is not None:
            raw = await file.read(MAX_IMAGE_BYTES + 1)
            array = _decode_image(raw)
            quality = assess_photo_quality(array, image_type)
        else:
            quality = None
        result = triage(
            parsed, has_diabetes=has_diabetes, image_type=image_type,
            image_quality_ok=bool(quality and quality["ok"])
        )
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        if file is not None:
            await file.close()

    bundle = build_triage_bundle(result, quality, age=age_num, symptoms=parsed)
    return {
        "triage": result,
        "quality": quality,
        "fhir": bundle,
        "notice": "نموذج بحثي غير تشخيصي؛ لا يقيس السكري أو قوة النظر ولا يفحص الشبكية.",
    }
