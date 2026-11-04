"""
فاحص — نموذج أولي قابل للعرض
تشغيل: streamlit run app.py
"""
import io
import json
import numpy as np
import streamlit as st
import cv2
from PIL import Image
from fusion import calculate_risk
from fhir_export import build_fhir_bundle

# ─────────────────────── إعداد الصفحة ───────────────────────
st.set_page_config(
    page_title="فاحص — درجة خطر واحدة",
    page_icon="👁️",
    layout="wide",
)

# CSS لدعم RTL والخط العربي
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    .risk-card { padding: 2rem; border-radius: 1rem; color: white; text-align: center; }
    .risk-green  { background: #2E7D32; }
    .risk-yellow { background: #F9A825; color: #000; }
    .risk-red    { background: #C62828; }
    .risk-gray   { background: #616161; }
    .risk-score  { font-size: 4rem; font-weight: 700; margin: 0; }
    .reason-box  { padding: 0.75rem 1rem; background: #F5F7FA; border-right: 4px solid #1B9AAA;
                   margin-bottom: 0.5rem; border-radius: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────── العنوان ───────────────────────
st.markdown("# 👁️ فاحص")
st.markdown("### درجة خطر واحدة، مفسَّرة بالعربية")
st.markdown("---")

# ─────────────────────── الشريط الجانبي: المدخلات ───────────────────────
with st.sidebar:
    st.header("📋 بيانات المريض")

    name = st.text_input("الاسم", "خالد")
    age = st.number_input("العمر", 30, 90, 52)
    dm_years = st.number_input("سنوات السكري", 0, 40, 7)
    hba1c = st.slider("HbA1c (%)", 5.0, 14.0, 8.5, 0.1)
    sbp = st.number_input("الضغط الانقباضي (mmHg)", 90, 200, 145)

    st.header("⌚ بيانات الساعة الذكية")
    hr = st.number_input("متوسط النبض (bpm)", 40, 150, 82)
    hrv = st.number_input("HRV (ms)", 5, 100, 28)
    steps = st.number_input("خطوات اليوم", 0, 30000, 3200)
    sleep_h = st.slider("ساعات النوم", 3.0, 10.0, 5.2, 0.1)

# ─────────────────────── المحتوى الرئيسي ───────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🖼️ صورة قاع العين")
    uploaded = st.file_uploader("ارفع صورة", type=["jpg", "jpeg", "png"])
    if uploaded:
        img = Image.open(uploaded).convert("RGB")
        st.image(img, caption="الصورة المرفوعة", use_column_width=True)

with col2:
    st.subheader("📊 النتيجة")

    if uploaded:
        img_array = np.array(img)

        # ─── بوابة الجودة: Laplacian variance ───
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        image_quality = min(laplacian_var / 500.0, 1.0)  # تطبيع تقديري

        # ─── نموذج الشبكية (محاكاة — استبدله بنموذجك الحقيقي) ───
        # ⚠️ هذا محاكاة بسيطة للعرض. استبدله بـ EfficientNet أو CLIP.
        red_channel = img_array[:, :, 0].mean() / 255.0
        # خطر أعلى = احمرار أكثر + تباين أقل
        image_score = float(np.clip(red_channel * 0.8 + (1 - image_quality) * 0.4, 0, 1))
        model_confidence = 0.85 if image_quality > 0.6 else 0.5

        # ─── بيانات الساعة → درجة خطر ───
        hr_risk = np.clip(abs(hr - 75) / 50, 0, 1)
        hrv_risk = np.clip((40 - hrv) / 40, 0, 1)
        steps_risk = np.clip((8000 - steps) / 8000, 0, 1)
        sleep_risk = np.clip((7 - sleep_h) / 4, 0, 1)
        wearable_score = float(0.3 * hr_risk + 0.3 * hrv_risk + 0.2 * steps_risk + 0.2 * sleep_risk)

        # ─── السجل → درجة خطر ───
        ehr_score = float(np.clip(
            0.4 * (dm_years / 20) + 0.4 * ((hba1c - 6) / 6) + 0.2 * ((sbp - 120) / 60),
            0, 1
        ))

        # ─── الدمج ───
        result = calculate_risk(
            image_score=image_score,
            image_quality=image_quality,
            model_confidence=model_confidence,
            wearable_score=wearable_score,
            ehr_score=ehr_score,
        )

        # ─── عرض النتيجة ───
        color_class = f"risk-{result['color']}"
        score_display = (
            f"{result['risk_score']:.2f}"
            if result["risk_score"] is not None
            else "—"
        )
        st.markdown(f"""
        <div class="risk-card {color_class}">
            <div class="risk-score">{score_display}</div>
            <div style="font-size:1.2rem; margin-top:0.5rem;">{result['message']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### الأسباب")
        for r in result["reasons"]:
            st.markdown(f'<div class="reason-box">{r}</div>', unsafe_allow_html=True)

        with st.expander("🔍 تفاصيل المكوّنات"):
            st.json(result["components"])

        # ─── FHIR ───
        patient_info = {
            "name": name, "birth_date": f"{2026-age}-01-01",
            "hr": hr, "steps": steps, "hrv": hrv,
            "image_quality": round(image_quality, 3),
        }
        bundle = build_fhir_bundle(result, patient_info)

        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                "📄 تنزيل FHIR JSON",
                data=json.dumps(bundle, ensure_ascii=False, indent=2),
                file_name="fahes_fhir_bundle.json",
                mime="application/json",
            )
        with col_b:
            report_md = f"""# تقرير فاحص
**المريض:** {name} · **العمر:** {age}
**النتيجة:** {score_display} ({result['color_ar']})
**الرسالة:** {result['message']}

## الأسباب
{chr(10).join('- ' + r for r in result['reasons'])}

## المكوّنات
- درجة الصورة: {result['components']['image']}
- درجة الساعة: {result['components']['wearable']}
- درجة السجل: {result['components']['ehr']}

---
*أداة دعم قرار — لا تُصدر تشخيصًا. الطبيب المختص هو المرجع.*
"""
            st.download_button(
                "📋 تنزيل التقرير (Markdown)",
                data=report_md.encode("utf-8"),
                file_name="fahes_report.md",
                mime="text/markdown",
            )
    else:
        st.info("👈 ارفع صورة قاع العين للبدء")

# ─────────────────────── تذييل ───────────────────────
st.markdown("---")
st.caption(
    "⚠️ نموذج أولي لأغراض الهاكاثون. الصور من بيانات APTOS المفتوحة. "
    "النموذج التشخيصي محاكى — الاستبدال بنموذج مُصادق شرط قبل الاستخدام السريري."
)
