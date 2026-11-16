"""FAHES | Arabic, non-diagnostic photographic eye-screening prototype.

Photo quality is checked technically; medical routing comes ONLY from declared
symptoms/history. No clinical classifier, refraction estimate or diabetes
prediction is performed. Streamlit processes uploads on the app server.
"""
from __future__ import annotations

import html
import json
from io import BytesIO

import numpy as np
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

from eye_quality import assess_photo_quality
from triage import SYMPTOMS, triage
from triage_export import build_triage_bundle


MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 24_000_000
PHOTO_OPTIONS = {
    "صورة مقدمة العين بكاميرا الجوال": "external",
    "صورة قاع العين باستخدام ملحق بصري": "fundus",
}

st.set_page_config(page_title="فاحص | فرز أعراض العين", page_icon="👁️", layout="wide")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    html, body, [class*="css"] {font-family:'Tajawal',sans-serif; direction:rtl; text-align:right;}
    h1,h2,h3 {font-family:'Tajawal',sans-serif;}
    .block-container {max-width:1120px; padding-top:1.5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def decode_image(payload: bytes) -> Image.Image:
    if len(payload) > MAX_FILE_BYTES:
        raise ValueError("حجم الملف أكبر من 10 ميجابايت.")
    if not payload:
        raise ValueError("لم يتم استلام صورة.")
    try:
        with Image.open(BytesIO(payload)) as source:
            if source.width * source.height > MAX_PIXELS:
                raise ValueError("دقة الصورة كبيرة جدًا؛ الحد الأقصى 24 مليون بكسل.")
            if source.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError("صيغة الصورة غير مدعومة؛ استخدم JPG أو PNG أو WebP.")
            return ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("تعذر فتح الصورة؛ أعد حفظها بصيغة JPG أو PNG.") from exc


def parse_age(value: str):
    if not value.strip():
        return None
    try:
        years = int(value.strip())
    except ValueError as exc:
        raise ValueError("العمر يجب أن يكون رقمًا صحيحًا.") from exc
    if years < 1 or years > 120:
        raise ValueError("أدخل عمرًا بين 1 و120 سنة، أو اترك الحقل فارغًا.")
    return years


def report_markdown(result: dict, quality: dict | None, age, declared_type: str) -> str:
    if quality is None:
        image_lines = ["- لا توجد صورة مرفوعة؛ لم يُجرَ فحص جودة الصورة."]
    else:
        image_lines = [
            f"- نتيجة فحص الجودة التجريبي: {'استوفت العتبات' if quality['ok'] else 'تحتاج إعادة التصوير'}",
            f"- المتوسط التقريبي للإضاءة: {quality['brightness']}/255",
            f"- تباين حواف الصورة (مؤشر حدة غير سريري): {quality['sharpness']}",
            *["- ملاحظة: " + msg for msg in quality["warnings"]],
        ]
    lines = [
        "# فاحص — تقرير توجيه أولي تجريبي",
        "",
        "**تنبيه:** ليس تشخيصًا، ولا تقديرًا لاحتمال السكري أو اعتلال الشبكية.",
        f"**نوع الصورة المُعلن من المستخدم:** {declared_type}",
        f"**العمر:** {age if age is not None else 'غير مدخل'}",
        f"**أولوية التوجيه بناءً على الاستبيان:** {result['title']}",
        "",
        "## التوصية",
        result["action"],
        "",
        "## البيانات المبلّغ عنها",
        *["- " + reason for reason in result["reasons"]],
        "",
        "## الفحص التقني للصورة",
        *image_lines,
        "",
        "## حدود التحليل",
        result["image_note"],
        "فحص الجودة لا يتأكد من وجود عين بالصورة أو خلوها من الأمراض. لم يُطبق نموذج تشخيصي.",
        "الرفع عبر Streamlit يُعالَج على خادم التطبيق، وليس داخل الهاتف فقط.",
    ]
    return "\n".join(lines) + "\n"


def report_html(result: dict, quality: dict | None, age, declared_type: str) -> str:
    """Standalone printable HTML, suitable for browser Print > Save as PDF."""
    escape = lambda value: html.escape(str(value), quote=True)
    reasons = "".join("<li>" + escape(x) + "</li>" for x in result["reasons"])
    if quality is None:
        warnings = ""
        state = "لم تُرفع صورة"
        metrics = "لم يُجرَ فحص تقني للصورة"
    else:
        warnings = "".join("<li>" + escape(x) + "</li>" for x in quality["warnings"])
        state = "استوفت العتبات التقنية" if quality["ok"] else "تحتاج إعادة تصوير"
        metrics = f"الإضاءة: {quality['brightness']}/255 | مؤشر الحدة: {quality['sharpness']}"
    return f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<title>تقرير فاحص التجريبي</title><style>
body{{font-family:Tahoma,Arial,sans-serif;max-width:800px;margin:32px auto;color:#192b3b;line-height:1.8;padding:0 18px}}
h1{{color:#126079}}.note{{border-right:4px solid #c67b00;background:#fff7ed;padding:12px}}
.box{{border:1px solid #d8e3e8;border-radius:10px;padding:14px;margin:16px 0}}
@media print{{body{{margin:10mm auto}}}}
</style></head><body><h1>فاحص | تقرير توجيه أولي</h1>
<p class="note"><strong>بحثي وغير تشخيصي.</strong> لا يقيس النظر أو HbA1c ولا يتحقق من أمراض الشبكية.</p>
<div class="box"><p><b>الصورة المُعلنة:</b> {escape(declared_type)}</p>
<p><b>العمر:</b> {escape(age if age is not None else "غير مدخل")}</p>
<p><b>أولوية التوجيه:</b> {escape(result['title'])}</p>
<p><b>التوصية:</b> {escape(result['action'])}</p></div>
<h2>المعلومات المُبلّغ عنها</h2><ul>{reasons}</ul>
<h2>جودة الصورة التقنية (تجريبية)</h2>
<p>{state} | {metrics}</p>
<ul>{warnings}</ul>
<h2>حدود التحليل</h2><p>{escape(result['image_note'])}</p>
<p>الصورة لا تُدرج داخل التقرير. لا تمثل النتيجة إحالة صادرة عن منشأة صحية.</p>
</body></html>"""


st.title("👁️ فاحص | FAHES")
st.subheader("التصوير بالجوال وفرز أعراض العين — نموذج أولي")
st.warning(
    "هذا التطبيق لا يشخّص السكري أو اعتلال الشبكية، ولا يقيس قوة النظر. "
    "تحليل الصورة هنا تقني (إضاءة وحدّة)، أما التوجيه فيعتمد على الأعراض التي تدخلها. "
    "عند فقدان مفاجئ للنظر أو ألم شديد أو إصابة، اطلب المساعدة الطبية العاجلة دون انتظار الصورة."
)
st.caption(
    "الخصوصية: تُرسل الصور إلى خادم Streamlit لمعالجتها أثناء الجلسة. "
    "لا يحفظ التطبيق الصور في قاعدة بيانات ولا يرسلها لخدمات ذكاء اصطناعي خارجية. "
    "تجنب رفع بيانات تعريفية غير لازمة، ولا تستخدمه على بيانات مرضى حقيقية دون الموافقات والضوابط اللازمة."
)

image_col, form_col = st.columns([1.05, 1], gap="large")
with image_col:
    st.markdown("### ١ — التقاط الصورة وفحص الجودة")
    selected_label = st.radio("نوع الصورة (حدده يدويًا)", list(PHOTO_OPTIONS), horizontal=False)
    image_type = PHOTO_OPTIONS[selected_label]
    if image_type == "external":
        st.info("كاميرا الجوال العادية تصور الجزء الخارجي من العين فقط؛ لا تُظهر الشبكية.")
    else:
        st.info("تحتاج صورة قاع العين إلى ملحق تصوير مناسب أو كاميرا مخصصة. اختيار النوع لا يتحقق من محتوى الصورة.")
    capture_mode = st.radio("مصدر الصورة", ["رفع صورة", "التقاط بالكاميرا"], horizontal=True)
    if capture_mode == "التقاط بالكاميرا":
        uploaded = st.camera_input("التقط صورة العين", key="live_capture")
    else:
        uploaded = st.file_uploader(
            "ارفع صورة العين (JPG أو PNG أو WebP)",
            type=["jpg", "jpeg", "png", "webp"],
            key="uploaded_eye",
        )

    quality = None
    if uploaded is not None:
        try:
            photo = decode_image(uploaded.getvalue())
            st.image(photo, caption="معاينة الصورة (غير محللة طبيًا)", use_column_width=True)
            quality = assess_photo_quality(np.asarray(photo), image_type)
            a, b = st.columns(2)
            a.metric("الإضاءة التقريبية", f"{quality['brightness']}/255")
            b.metric("مؤشر الحدة", f"{quality['sharpness']:.0f}")
            if quality["ok"]:
                st.success("الصورة اجتازت عتبات الجودة التقنية التجريبية، ولا يعني ذلك صلاحيتها للتشخيص.")
            else:
                for warning in quality["warnings"]:
                    st.warning(warning)
            with st.expander("تفاصيل قياس جودة الصورة"):
                st.json(quality)
                st.caption("العتبات غير معايرة على أجهزة أو صور سريرية، ولا تتحقق من أن الصورة تُظهر عينًا.")
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("تعذرت معالجة الصورة. جرّب صورة أخرى.")
    else:
        st.info("يمكن البدء باستبيان الأعراض حتى دون صورة، لأن أعراض الطوارئ أهم من نتيجة التصوير.")

with form_col:
    st.markdown("### ٢ — استبيان الأعراض")
    st.caption("هذه الإجابات للتوجيه العام، وليست أداة تقدير احتمال مرض.")
    selected_symptoms = st.multiselect(
        "حدد الأعراض التي تنطبق (إن وُجدت)",
        options=list(SYMPTOMS),
        format_func=lambda code: SYMPTOMS[code],
        placeholder="اختر الأعراض أو اترك الحقل فارغًا",
    )
    diabetes_answer = st.radio(
        "هل شُخّصت سابقًا بالسكري؟",
        ["لا أرغب بالإجابة", "نعم", "لا"],
        horizontal=True,
    )
    has_diabetes = diabetes_answer == "نعم"
    age_string = st.text_input("العمر (اختياري)", placeholder="مثال: 42")
    st.caption("لا يلزم إدخال اسم أو رقم هوية لإصدار التقرير.")

    try:
        age = parse_age(age_string)
    except ValueError as exc:
        age = None
        st.error(str(exc))

st.divider()
st.markdown("### ٣ — نتيجة توجيه أولي")
result = triage(
    selected_symptoms,
    has_diabetes=has_diabetes,
    image_quality_ok=bool(quality and quality["ok"]),
    image_type=image_type,
)
if result["priority"] == "urgent":
    st.error("**" + result["title"] + "** — " + result["action"])
elif result["priority"] == "appointment":
    st.warning("**" + result["title"] + "** — " + result["action"])
else:
    st.info("**" + result["title"] + "** — " + result["action"])

if result["needs_retake"]:
    st.caption("ملاحظة التصوير: " + (
        "لم تُرفع صورة بعد؛ " if uploaded is None else "لم تجتز الصورة فحص الجودة؛ "
    ) + "يمكن تحسين الصورة وإعادة الالتقاط، لكن لا تؤخر طلب المساعدة عند وجود أعراض طارئة.")
else:
    st.caption("اجتازت الصورة العتبات التقنية فقط؛ لا تدل النتيجة على سلامة العين.")
st.caption(result["image_note"])

with st.expander("لماذا ظهرت هذه التوصية؟"):
    for reason in result["reasons"]:
        st.write("• " + reason)
    st.write("لا يُستنتج التشخيص أو درجة خطورة عددية من صورة العين في هذه النسخة.")

if age_string.strip() == "" or age is not None:
    st.markdown("### ٤ — تنزيل التقرير والتكامل التجريبي")
    markdown = report_markdown(result, quality, age, selected_label)
    exported = build_triage_bundle(
        result, quality, age=age, symptoms=selected_symptoms
    )
    c1, c2, c3 = st.columns(3)
    c1.download_button(
        "تنزيل التقرير (Markdown)",
        data=markdown.encode("utf-8"), file_name="fahes_report.md",
        mime="text/markdown", use_container_width=True,
    )
    c2.download_button(
        "تنزيل نسخة للطباعة (HTML)",
        data=report_html(result, quality, age, selected_label).encode("utf-8"),
        file_name="fahes_report.html", mime="text/html",
        use_container_width=True,
    )
    c3.download_button(
        "تنزيل FHIR تجريبي (JSON)",
        data=json.dumps(exported, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="fahes_fhir.json", mime="application/fhir+json",
        use_container_width=True,
    )
    st.caption("لفظ «FHIR تجريبي» يعني صيغة تبادل معلومات أولية، ولا يُعد تقريرًا تشخيصيًا.")
else:
    st.caption("صحّح العمر المدخل، أو اتركه فارغًا، لإتاحة تنزيل التقرير.")

st.divider()
with st.expander("عن النموذج الأولي وخارطة التحقق"):
    st.markdown(
        "• لا يُشغَّل CLIP لتشخيص اعتلال الشبكية؛ النموذج السابق غير معتمد لهذا الغرض.\n"
        "• لا توجد دقة سريرية أو حساسية ونوعية مثبتة في هذه النسخة.\n"
        "• فحص الجوال الخارجي منفصل عن تصوير قاع العين بملحق بصري.\n"
        "• قبل أي استخدام سريري: يلزم نموذج مناسب، مجموعة تحقق مستقلة، "
        "تحليل حساسية ونوعية، ومراجعة المتطلبات التنظيمية وحماية البيانات."
    )
