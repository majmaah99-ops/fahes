"""
فاحص (FAHES) — نموذج أولي تفاعلي
تشغيل: streamlit run app.py
"""

import io
import json
import numpy as np
import streamlit as st
import cv2
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

# استيراد المنطق من الملفات الخارجية
from fusion import calculate_risk
from fhir_export import build_fhir_bundle

# ─────────────────────── إعداد الصفحة والستايل ───────────────────────
st.set_page_config(
    page_title="فاحص — درجة خطر واحدة",
    page_icon="👁️",
    layout="wide",
)

# دعم اللغة العربية والتصميم
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    .risk-card {
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .risk-green  { background-color: #2E7D32; }
    .risk-yellow { background-color: #F9A825; color: #000; }
    .risk-red    { background-color: #C62828; }
    .risk-gray   { background-color: #616161; }
    
    .risk-score  { font-size: 4rem; font-weight: 700; margin: 0; line-height: 1.2; }
    .risk-label  { font-size: 1.2rem; margin-top: 0.5rem; }
    
    .reason-box  {
        padding: 0.75rem 1rem;
        background: #F5F7FA;
        border-right: 4px solid #1B9AAA;
        margin-bottom: 0.5rem;
        border-radius: 0.5rem;
        font-size: 1.1rem;
    }
    
    .stButton>button {
        background-color: #1B9AAA;
        color: white;
        border-radius: 8px;
        font-family: 'Tajawal', sans-serif;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────── تحميل نموذج CLIP ───────────────────────
@st.cache_resource(show_spinner="جاري تحميل نموذج تحليل الشبكية...")
def load_clip_model():
    model_name = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_name)
    processor = CLIPProcessor.from_pretrained(model_name)
    return model, processor

# ─────────────────────── واجهة المستخدم: الشريط الجانبي ───────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/eye-care.png", width=80)
    st.title("بيانات المريض")
    
    with st.expander("👤 معلومات أساسية", expanded=True):
        name = st.text_input("اسم المريض", "خالد")
        age = st.number_input("العمر", min_value=1, max_value=120, value=52)
        gender = st.selectbox("الجنس", ["ذكر", "أنثى"])
        
    with st.expander("🏥 السجل السريري", expanded=True):
        dm_years = st.number_input("سنوات الإصابة بالسكري", min_value=0, max_value=50, value=7)
        hba1c = st.slider("مستوى HbA1c (%)", min_value=4.0, max_value=15.0, value=8.5, step=0.1)
        sbp = st.number_input("ضغط الدم الانقباضي (mmHg)", min_value=80, max_value=220, value=145)
        
    with st.expander("⌚ بيانات الساعة الذكية", expanded=True):
        hr = st.number_input("متوسط النبض (نبضة/دقيقة)", min_value=30, max_value=200, value=82)
        hrv = st.number_input("تقلب معدل النبض HRV (ms)", min_value=5, max_value=150, value=28)
        steps = st.number_input("عدد الخطوات اليومية", min_value=0, max_value=50000, value=3200)
        sleep_h = st.slider("ساعات النوم", min_value=2.0, max_value=12.0, value=5.2, step=0.1)

# ─────────────────────── واجهة المستخدم: الصفحة الرئيسية ───────────────────────
st.title("👁️ فاحص")
st.markdown("### درجة خطر واحدة، مفسَّرة بالعربية")
st.markdown("---")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("🖼️ صورة قاع العين")
    uploaded_file = st.file_uploader("ارفع صورة قاع العين (JPG, PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        img = Image.open(uploaded_file).convert("RGB")
        st.image(img, caption="الصورة المرفوعة", use_column_width=True)

with col2:
    st.subheader("📊 نتيجة التحليل")
    
    if uploaded_file is not None:
        # 1. معالجة الصورة وبوابة الجودة
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # تطبيع الجودة (تجريبي: قيمة > 500 تعتبر جودة ممتازة)
        image_quality = float(min(laplacian_var / 500.0, 1.0))
        
        # 2. تحليل الشبكية باستخدام CLIP
        clip_model, clip_processor = load_clip_model()
        
        texts = [
            "a retinal fundus photo showing severe diabetic retinopathy with hemorrhages and exudates",
            "a normal healthy retinal fundus photo"
        ]
        
        inputs = clip_processor(text=texts, images=img, return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = clip_model(**inputs).logits_per_image.softmax(dim=1)
            
        image_score = float(logits[0][0])          # احتمال وجود اعتلال
        model_confidence = float(max(logits[0]))   # ثقة النموذج
        
        # 3. حساب درجات الساعة الذكية والسجل
        # (منطق تجريبي — يمكن استبداله بنموذج انحدار لوجستي حقيقي)
        hr_risk = min(abs(hr - 75) / 50.0, 1.0)
        hrv_risk = min(max((40 - hrv) / 40.0, 0), 1.0)
        steps_risk = min(max((8000 - steps) / 8000.0, 0), 1.0)
        sleep_risk = min(max((7 - sleep_h) / 4.0, 0), 1.0)
        wearable_score = float(0.3*hr_risk + 0.3*hrv_risk + 0.2*steps_risk + 0.2*sleep_risk)
        
        ehr_score = float(min(max(
            0.4*(dm_years/20.0) + 0.4*((hba1c-6)/6.0) + 0.2*((sbp-120)/60.0), 
            0), 1))
        
        # 4. الدمج (استدعاء fusion.py)
        result = calculate_risk(
            image_score=image_score,
            image_quality=image_quality,
            model_confidence=model_confidence,
            wearable_score=wearable_score,
            ehr_score=ehr_score
        )
        
        # 5. عرض النتيجة
        color_class = f"risk-{result['color']}"
        score_display = f"{result['risk_score']:.2f}" if result["risk_score"] is not None else "—"
        
        st.markdown(f"""
        <div class="risk-card {color_class}">
            <div class="risk-score">{score_display}</div>
            <div class="risk-label">{result['message']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 🔍 الأسباب:")
        for reason in result["reasons"]:
            st.markdown(f'<div class="reason-box">• {reason}</div>', unsafe_allow_html=True)
            
        with st.expander("⚙️ تفاصيل المكونات (للمراجعة)"):
            st.json(result["components"])
            st.caption(f"جودة الصورة: {image_quality:.2f} | ثقة النموذج: {model_confidence:.2f}")
            
        # 6. مخرجات FHIR والتقرير
        st.markdown("---")
        st.subheader("📄 المخرجات والتكامل")
        
        patient_info = {
            "name": name,
            "gender": "male" if gender == "ذكر" else "female",
            "birth_date": f"{2026 - age}-01-01",
            "hr": hr,
            "steps": steps,
            "hrv": hrv,
            "image_quality": round(image_quality, 3)
        }
        
        fhir_bundle = build_fhir_bundle(result, patient_info)
        
        # تقرير Markdown
        report_md = f"""# تقرير فاحص
**المريض:** {name} · **العمر:** {age}
**النتيجة:** {score_display} ({result['color_ar']})
**الرسالة:** {result['message']}

## الأسباب
{chr(10).join('- ' + r for r in result['reasons'])}

## المكونات
- درجة الصورة: {result['components'].get('image')}
- درجة الساعة: {result['components'].get('wearable')}
- درجة السجل: {result['components'].get('ehr')}

---
*أداة دعم قرار — لا تُصدر تشخيصًا. الطبيب المختص هو المرجع.*
"""
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.download_button(
                label="📥 تنزيل FHIR JSON",
                data=json.dumps(fhir_bundle, ensure_ascii=False, indent=2),
                file_name=f"fahes_fhir_{name}.json",
                mime="application/json",
                use_container_width=True
            )
        with btn_col2:
            st.download_button(
                label="📋 تنزيل التقرير (Markdown)",
                data=report_md.encode("utf-8"),
                file_name=f"fahes_report_{name}.md",
                mime="text/markdown",
                use_container_width=True
            )

    else:
        st.info("👈 يرجى رفع صورة قاع العين للبدء في التحليل.")

# ─────────────────────── تذييل الصفحة ───────────────────────
st.markdown("---")
st.caption(
    "⚠️ نموذج أولي لأغراض هاكاثون نبض الابتكار. "
    "الصور من بيانات APTOS المفتوحة. "
    "نموذج الشبكية (CLIP) ليس معتمدًا سريريًا — النموذج الحقيقي (EfficientNet-B3) جاهز للاستبدال."
)
