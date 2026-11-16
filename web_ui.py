"""Self-contained, Arabic responsive frontend for the Vercel FastAPI app.

All UI interactions call /api/screen and use the same Python triage/quality
engines as the Streamlit version. No external JS, fonts or third-party APIs.
"""

PAGE = r'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#0b2739">
  <meta name="description" content="فاحص: نموذج تجريبي لقياس جودة صورة العين وفرز الأعراض، لا يقدم تشخيصًا طبيًا.">
  <title>فاحص | تصوير العين وفرز الأعراض</title>
  <style>
  :root{--ink:#142e41;--muted:#607587;--blue:#127c9c;--line:#dbe7ed;--bg:#f4f8fa;--white:#fff}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI",Tahoma,Arial,sans-serif;line-height:1.7}
  button,input,select{font:inherit} button{cursor:pointer}
  .wrap{max-width:1120px;margin:auto;padding:0 20px}
  .head{background:#fff;border-bottom:1px solid #e1eaf0;box-shadow:0 3px 22px #12344d08}
  .head-inner{min-height:72px;display:flex;align-items:center;justify-content:space-between;gap:16px}
  .brand{display:flex;align-items:center;gap:12px;font-size:22px;font-weight:850}
  .logo{width:43px;height:43px;display:grid;place-items:center;background:#0e748f;color:#fff;border-radius:14px}
  .brand small{font-size:12px;background:#dff3f8;padding:4px 8px;border-radius:999px;color:#085e7b;font-weight:700}
  .head-note{font-size:13px;color:#5e7181}
  .hero{margin:30px 0 20px;padding:34px;border-radius:22px;color:#fff;background:radial-gradient(circle at 7% 80%,#177a89 0%,transparent 36%),linear-gradient(115deg,#0e556f,#0c2c42 70%);position:relative;overflow:hidden}
  .hero h1{font-size:clamp(25px,3vw,36px);margin:10px 0 7px;max-width:800px;line-height:1.4}
  .hero p{color:#d1e6ed;max-width:785px;margin:0;font-size:15px}
  .eyebrow{display:inline-block;font-size:12px;border:1px solid #ffffff62;border-radius:100px;padding:3px 13px;color:#e4f6ff}
  .notice{padding:15px 18px;border:1px solid #f2d197;border-radius:15px;background:#fff9ec;color:#785018;margin-bottom:22px;font-size:14px}
  .layout{display:grid;grid-template-columns:1.12fr 1fr;gap:20px;align-items:start}
  .card{background:#fff;border:1px solid var(--line);border-radius:19px;padding:24px;box-shadow:0 6px 26px #193b5108}
  .card h2{font-size:20px;margin:0 0 3px}
  .card .subtitle{font-size:13px;color:var(--muted);margin:0 0 22px}
  .step{display:inline-grid;place-items:center;width:31px;height:31px;border-radius:50%;background:#087a9a;color:#fff;font-size:14px;margin-left:8px}
  label.group-label{font-size:14px;display:block;font-weight:750;margin-bottom:9px}
  select,input[type=number]{width:100%;border:1px solid #cbdbe5;border-radius:11px;background:#fbfdff;padding:11px;color:var(--ink)}
  .choice-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}
  .choice{display:flex;gap:9px;align-items:center;min-height:55px;border:1px solid #d7e5e9;border-radius:12px;padding:9px 12px;background:#f8fbfc;font-size:13px;font-weight:650;cursor:pointer}
  .choice:has(input:checked){border-color:#0885a2;background:#eaf8fc;box-shadow:0 0 0 1px #0885a22d}
  .choice input{accent-color:#087d9d}
  .tools{display:flex;gap:10px;flex-wrap:wrap;margin:15px 0}
  .btn{border:1px solid #bbd1dc;background:#fff;color:#1b5268;border-radius:11px;padding:10px 16px;font-weight:750;display:inline-flex;align-items:center;justify-content:center;gap:7px}
  .btn:hover{background:#ecf7fa}
  .btn.primary{border-color:#087b99;background:#087b99;color:white}
  .btn.primary:hover{background:#086c88}
  .btn.dark{background:#122f44;color:white;border-color:#122f44}
  .btn:disabled{opacity:.55;cursor:not-allowed}
  .hidden{display:none!important}
  .preview{background:#f5f9fa;border:1px dashed #bbd1db;border-radius:15px;min-height:260px;display:grid;place-items:center;overflow:hidden;text-align:center;color:#678090}
  .preview img,.preview video{width:100%;height:290px;object-fit:contain;background:#0d283a}
  .preview-empty{padding:25px}
  .preview-empty svg{opacity:.6}
  .camera-actions{display:flex;justify-content:center;gap:10px;margin-top:12px;flex-wrap:wrap}
  .hint{color:#6a7f8f;font-size:12px;line-height:1.7;margin:8px 0}
  .section{border-top:1px solid #e8eff2;padding-top:17px;margin-top:18px}
  .symptoms{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:9px}
  .symptom{display:flex;align-items:start;gap:8px;padding:11px;border:1px solid #e0e8ed;border-radius:12px;background:#fbfcfd;font-size:12.5px;cursor:pointer}
  .symptom:has(input:checked){border-color:#3889a0;background:#edf8fb}
  .symptom input{margin:5px 0 0;accent-color:#067d9d}
  .submit{display:block;width:100%;border:0;background:linear-gradient(90deg,#0d8b95,#086884);color:white;font-weight:800;border-radius:12px;padding:14px;margin-top:20px;font-size:16px}
  .submit:hover{filter:brightness(.94)}.submit:disabled{opacity:.5}
  .progress{height:4px;background:linear-gradient(90deg,#1cb8a9,#1684b9);border-radius:10px;margin-top:10px;animation:pulse 1.2s infinite alternate}
  @keyframes pulse{from{opacity:.3}to{opacity:1}}
  .feedback{margin-top:14px;font-size:14px;line-height:1.8}
  .feedback.error{background:#fff0f0;border:1px solid #f1b9b9;color:#a02733;padding:12px;border-radius:11px}
  .result{margin:22px 0 40px}
  .result-header{display:flex;align-items:center;justify-content:space-between;gap:15px;flex-wrap:wrap;margin-bottom:14px}
  .result-header h2{margin:0;font-size:22px}
  .risk{border-radius:15px;padding:21px 23px;background:#e6f4fc;border:1px solid #9acae2;margin:0 0 16px}
  .risk.urgent{background:#fff0ed;border-color:#e6a79e;color:#8b302c}
  .risk.appointment{background:#fff8e8;border-color:#e9cb92;color:#785017}
  .risk.informational{background:#eaf7f9;border-color:#b4dce4;color:#165a71}
  .risk h3{margin:0 0 7px;font-size:20px}
  .risk p{margin:0}
  .detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:13px}
  .detail{background:#f8fbfc;border:1px solid #e2ebee;padding:15px;border-radius:12px}
  .detail b{display:block;font-size:14px;margin-bottom:6px}
  .detail p{margin:0;color:#4e697b;font-size:13px}
  .tags{margin-top:8px;padding:0 18px}
  .tags li{margin-bottom:5px}
  .footer{padding:30px 10px;color:#758696;text-align:center;font-size:12px}
  @media(max-width:790px){.layout,.detail-grid{grid-template-columns:1fr}.card{padding:18px}.hero{padding:25px 20px}.head-note{display:none}}
  @media(max-width:510px){.symptoms{grid-template-columns:1fr}.choice-grid{grid-template-columns:1fr}.brand{font-size:19px}.brand small{font-size:10px}.tools .btn{flex:1}}
  @media print{body{background:white}.head,.hero,.notice,.layout,.footer,.actions,.head-note{display:none!important}.result{margin:0;padding:0}.result .card{border:0;box-shadow:none}.result-header{margin:0 0 12px}.btn{display:none!important}}
  </style>
</head>
<body>
<header class="head"><div class="wrap head-inner">
 <div class="brand"><span class="logo" aria-hidden="true">
 <svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M2.2 12s3.6-6.5 9.8-6.5 9.8 6.5 9.8 6.5-3.6 6.5-9.8 6.5S2.2 12 2.2 12Z"/><circle cx="12" cy="12" r="3.2"/></svg>
 </span> فاحص <small>FAHES • نسخة تجريبية</small></div>
 <div class="head-note">فرز الأعراض • جودة الصورة التقنية • تقرير أولي</div>
</div></header>
<main class="wrap">
 <section class="hero">
  <span class="eyebrow">تطبيق عربي متوافق مع الهاتف — لا يحتاج إلى أجهزة عيادات</span>
  <h1>صورة العين، بداية أوضح للمتابعة</h1>
  <p>التقط صورة للجزء الخارجي من العين أو ارفع صورة لقاع العين، وتعرف على جودة الصورة التقنية. أجب عن أسئلة الأعراض للحصول على توجيه أولي، وليس تشخيصًا طبيًا.</p>
 </section>
 <div class="notice"><strong>تنبيه طبي:</strong> لا يقيس هذا التطبيق قوة النظر أو السكر التراكمي، ولا يشخّص اعتلال الشبكية. أعراض مثل فقدان النظر المفاجئ، الألم الشديد، أو ظهور ستار على الرؤية تستدعي رعاية عاجلة دون انتظار التصوير.</div>
 <div class="layout">
 <section class="card" aria-labelledby="photo-title">
  <h2 id="photo-title"><span class="step">١</span> تصوير العين</h2>
  <p class="subtitle">فحص تقني للإضاءة والوضوح فقط، دون استنتاج وجود مرض.</p>
  <label class="group-label">ما نوع الصورة؟</label>
  <div class="choice-grid">
   <label class="choice"><input type="radio" name="image_type" value="external" checked> مقدمة العين (كاميرا الجوال)</label>
   <label class="choice"><input type="radio" name="image_type" value="fundus"> قاع العين (بملحق بصري)</label>
  </div>
  <p id="type-hint" class="hint">كاميرا الهاتف العادية لا تُظهر الشبكية. يرجى تصوير مقدمة العين بإضاءة طبيعية.</p>
  <div class="tools">
   <label class="btn" for="upload">⬆ رفع صورة</label>
   <input id="upload" class="hidden" type="file" accept="image/jpeg,image/png,image/webp">
   <button id="camera-start" class="btn primary" type="button">◉ فتح الكاميرا</button>
   <button id="photo-clear" class="btn hidden" type="button">مسح الصورة</button>
  </div>
  <div class="preview" id="preview">
   <div class="preview-empty" id="preview-empty">
    <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#638b9b" stroke-width="1.2"><rect x="2" y="4" width="20" height="16" rx="3"/><circle cx="8" cy="9" r="2"/><path d="m3 18 6-6 4 4 3-3 5 5"/></svg>
    <div>لم تُرفق صورة بعد</div>
    <small>يمكن إجراء استبيان الأعراض دون صورة</small>
   </div>
   <img id="preview-img" alt="معاينة الصورة" class="hidden">
   <video id="camera-video" autoplay playsinline muted class="hidden"></video>
  </div>
  <div id="camera-actions" class="camera-actions hidden">
   <button class="btn primary" id="capture" type="button">التقاط الآن</button>
   <button class="btn" id="camera-stop" type="button">إلغاء الكاميرا</button>
  </div>
  <p class="hint">الصور تُرسل إلى خادم التطبيق مؤقتًا لفحص الجودة ولا تُحفظ في قاعدة بيانات. لا ترفع صورًا تحتوي على معلومات شخصية إضافية.</p>
 </section>
 <section class="card" aria-labelledby="symptoms-title">
  <h2 id="symptoms-title"><span class="step">٢</span> استبيان الأعراض</h2>
  <p class="subtitle">تحدد هذه الإجابات أولوية التوجيه، بغض النظر عن نجاح الصورة.</p>
  <label class="group-label">حدد ما ينطبق عليك (اختياري)</label>
  <div class="symptoms" id="symptoms">
    <label class="symptom"><input type="checkbox" value="sudden_loss"> فقدان أو انخفاض مفاجئ في النظر</label>
    <label class="symptom"><input type="checkbox" value="severe_pain"> ألم شديد في العين</label>
    <label class="symptom"><input type="checkbox" value="curtain"> ستار أو ظل جديد على الرؤية</label>
    <label class="symptom"><input type="checkbox" value="chemical"> تعرض العين لمادة كيميائية</label>
    <label class="symptom"><input type="checkbox" value="trauma"> إصابة مباشرة في العين</label>
    <label class="symptom"><input type="checkbox" value="flashes_floaters"> ومضات أو عوائم مفاجئة</label>
    <label class="symptom"><input type="checkbox" value="blur"> تشوش مستمر أو متكرر</label>
    <label class="symptom"><input type="checkbox" value="redness"> احمرار أو انزعاج مستمر</label>
    <label class="symptom"><input type="checkbox" value="thirst"> عطش زائد وتبول متكرر</label>
  </div>
  <div class="section">
   <label class="group-label" for="diabetes">هل شُخّصت سابقًا بالسكري؟</label>
   <select id="diabetes"><option value="unknown">لا أرغب بالإجابة</option><option value="yes">نعم</option><option value="no">لا</option></select>
  </div>
  <div class="section">
   <label class="group-label" for="age">العمر (اختياري)</label>
   <input id="age" type="number" min="1" max="120" placeholder="مثال: 42" inputmode="numeric">
  </div>
  <button class="submit" id="submit" type="button">إجراء الفرز الأولي</button>
  <div class="progress hidden" id="progress"></div>
  <p id="feedback" class="feedback hidden" role="alert" aria-live="polite"></p>
 </section>
 </div>
 <section class="result hidden" id="result" aria-live="polite">
 <div class="card">
  <div class="result-header">
   <h2><span class="step">٣</span> نتيجة الفرز الأولي</h2>
   <div class="actions">
    <button class="btn dark" type="button" id="print">طباعة / حفظ PDF</button>
    <button class="btn" type="button" id="download-md">تنزيل التقرير</button>
    <button class="btn" type="button" id="download-fhir">تنزيل FHIR JSON</button>
   </div>
  </div>
  <div id="risk" class="risk"><h3 id="risk-title"></h3><p id="risk-action"></p></div>
  <div class="detail-grid">
   <div class="detail"><b>جودة الصورة التقنية</b><p id="quality-text"></p></div>
   <div class="detail"><b>المعلومات المُبلّغ عنها</b><ul class="tags" id="reasons"></ul></div>
  </div>
  <p class="hint" id="eye-note"></p>
  <p class="hint"><strong>إخلاء مسؤولية:</strong> النتيجة توجيه عام مبني على الإجابات، وليست إثباتًا لسلامة العين أو تقرير إحالة صادرًا عن منشأة صحية.</p>
 </div></section>
 <footer class="footer">فاحص FAHES — نموذج بحثي أولي غير معتمد للاستخدام السريري. لا تحفظ الخدمة الصورة أو سجلات الفحوص في قاعدة بيانات.</footer>
</main>
<script>
(function(){
"use strict";
const $=id=>document.getElementById(id);
let currentFile=null,stream=null,previewURL=null,last=null;
function feedback(message,isError=true){
 const box=$("feedback");box.textContent=message;box.className="feedback"+(isError?" error":"");
}
function stopCamera(){
 if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}
 $("camera-video").srcObject=null;$("camera-video").classList.add("hidden");
 $("camera-actions").classList.add("hidden");
}
function showPreview(file){
 if(previewURL)URL.revokeObjectURL(previewURL);
 currentFile=file;previewURL=URL.createObjectURL(file);
 $("preview-img").src=previewURL;$("preview-img").classList.remove("hidden");
 $("preview-empty").classList.add("hidden");$("photo-clear").classList.remove("hidden");
 $("result").classList.add("hidden");
}
$("upload").addEventListener("change",e=>{
 const file=e.target.files?.[0];if(!file)return;
 if(!["image/jpeg","image/png","image/webp"].includes(file.type)){feedback("يرجى اختيار صورة JPG أو PNG أو WebP.");return;}
 if(file.size>10485760){feedback("الصورة أكبر من 10 ميجابايت.");return;}
 stopCamera();showPreview(file);$("feedback").classList.add("hidden");
});
$("camera-start").addEventListener("click",async()=>{
 if(!navigator.mediaDevices?.getUserMedia){feedback("الكاميرا تحتاج إلى متصفح يدعمها واتصال HTTPS. يمكنك رفع صورة بدلًا منها.");return;}
 stopCamera();
 try{
  stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:"user",width:{ideal:1280}},audio:false});
  $("preview-img").classList.add("hidden");$("preview-empty").classList.add("hidden");
  $("camera-video").srcObject=stream;$("camera-video").classList.remove("hidden");
  $("camera-actions").classList.remove("hidden");$("feedback").classList.add("hidden");
 }catch(e){feedback("تعذر فتح الكاميرا؛ اسمح للمتصفح بالوصول إليها أو استخدم رفع الصورة.");}
});
$("capture").addEventListener("click",()=>{
 const video=$("camera-video");if(!video.videoWidth){feedback("الكاميرا لم تبدأ بعد.");return;}
 const canvas=document.createElement("canvas");canvas.width=video.videoWidth;canvas.height=video.videoHeight;
 canvas.getContext("2d").drawImage(video,0,0);
 canvas.toBlob(blob=>{
  if(!blob){feedback("فشل التقاط الصورة.");return;}
  const f=new File([blob],"eye-camera.jpg",{type:"image/jpeg"});
  stopCamera();showPreview(f);
 },"image/jpeg",0.9);
});
$("camera-stop").addEventListener("click",()=>{
 stopCamera();
 if(currentFile){$("preview-img").classList.remove("hidden");}
 else{$("preview-empty").classList.remove("hidden");}
});
$("photo-clear").addEventListener("click",()=>{
 stopCamera();currentFile=null;$("upload").value="";
 if(previewURL)URL.revokeObjectURL(previewURL);previewURL=null;
 $("preview-img").removeAttribute("src");$("preview-img").classList.add("hidden");
 $("preview-empty").classList.remove("hidden");$("photo-clear").classList.add("hidden");
 $("result").classList.add("hidden");
});
document.querySelectorAll('input[name="image_type"]').forEach(el=>el.addEventListener("change",()=>{
 $("type-hint").textContent=document.querySelector('input[name="image_type"]:checked').value==="external"?
 "كاميرا الهاتف العادية لا تُظهر الشبكية. يرجى تصوير مقدمة العين بإضاءة طبيعية.":
 "صور قاع العين تحتاج إلى كاميرا أو ملحق بصري مناسب. لن يقوم النموذج بتشخيص الشبكية.";
}));
$("submit").addEventListener("click",async()=>{
 const age=$("age").value.trim();
 if(age && (!Number.isInteger(Number(age)) || Number(age)<1 || Number(age)>120)){feedback("أدخل عمرًا صحيحًا بين 1 و120، أو اتركه فارغًا.");return;}
 const form=new FormData();
 form.append("image_type",document.querySelector('input[name="image_type"]:checked').value);
 form.append("symptoms",JSON.stringify(Array.from(document.querySelectorAll('#symptoms input:checked')).map(el=>el.value)));
 form.append("has_diabetes",String($("diabetes").value==="yes"));form.append("age",age);
 if(currentFile)form.append("file",currentFile,currentFile.name);
 $("submit").disabled=true;$("progress").classList.remove("hidden");$("feedback").classList.add("hidden");
 try{
  const response=await fetch("/api/screen",{method:"POST",body:form,headers:{"Accept":"application/json"}});
  const body=await response.json();
  if(!response.ok){const d=body.detail;throw Error(typeof d==="string"?d:"تعذر إتمام تحليل البيانات.");}
  last=body;render(body);
  $("result").classList.remove("hidden");
  $("result").scrollIntoView({behavior:"smooth",block:"start"});
 }catch(e){feedback(e.message||"تعذّر الاتصال بالخدمة؛ أعد المحاولة.");}
 finally{$("submit").disabled=false;$("progress").classList.add("hidden");}
});
function render(data){
 const t=data.triage,q=data.quality;
 $("risk").className="risk "+t.priority;
 $("risk-title").textContent=t.title;$("risk-action").textContent=t.action;
 if(q){
  $("quality-text").textContent=(q.ok?"استوفت عتبات الجودة التقنية التجريبية":"تحتاج إعادة تصوير")+
   " | إضاءة: "+q.brightness+"/255 | مؤشر حدة: "+q.sharpness+
   (q.warnings.length?" | "+q.warnings.join("؛ "):"")+" — لا يثبت ذلك صحة العين.";
 }else $("quality-text").textContent="لم تُرفع صورة، ولم تُقَس جودتها. لا يؤثر ذلك على تنبيهات الأعراض العاجلة.";
 const ul=$("reasons");ul.replaceChildren();
 t.reasons.forEach(reason=>{const li=document.createElement("li");li.textContent=reason;ul.appendChild(li);});
 $("eye-note").textContent=t.image_note;
}
function download(text,name,type){
 const blob=new Blob([text],{type});const a=document.createElement("a");
 const url=URL.createObjectURL(blob);a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$("download-fhir").addEventListener("click",()=>{if(last)download(JSON.stringify(last.fhir,null,2),"fahes_fhir.json","application/fhir+json;charset=utf-8");});
$("download-md").addEventListener("click",()=>{
 if(!last)return;const t=last.triage,q=last.quality;
 const parts=["# تقرير فاحص التجريبي","","**غير تشخيصي** — لا يحدد قوة النظر أو السكري أو اعتلال الشبكية.",
 "## أولوية التوجيه",t.title,"",t.action,"","## المعلومات المُبلّغ عنها",...t.reasons.map(r=>"- "+r),
 "","## جودة الصورة التقنية",q?(q.ok?"اجتازت عتبات الجودة التجريبية":"تحتاج إعادة تصوير"):"لا توجد صورة مرفوعة",
 "","## حدود الفحص",t.image_note];
 download(parts.join("\n"),"fahes_report.md","text/markdown;charset=utf-8");
});
$("print").addEventListener("click",()=>{if(last)window.print();});
window.addEventListener("pagehide",()=>{stopCamera();if(previewURL)URL.revokeObjectURL(previewURL);});
})();
</script>
</body></html>
'''
