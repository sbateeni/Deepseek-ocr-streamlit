import streamlit as st
import requests
import json
from PIL import Image
import io
import fitz  # PyMuPDF
import tempfile
import os

# إعدادات الصفحة
st.set_page_config(
    page_title="DeepSeek OCR",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="expanded"
)

# نماذج OCR محتملة
OCR_MODELS = {
    "DeepSeek OCR": "deepseek-ai/deepseek-ocr",
    "Microsoft TrOCR Printed": "microsoft/trocr-base-printed",
    "Microsoft TrOCR Handwritten": "microsoft/trocr-base-handwritten",
    "Donut OCR": "naver-clova-ix/donut-base-finetuned-cord-v2",
    "PaddleOCR": "paddlepaddle/paddleocr",
}

def init_session_state():
    """تهيئة حالة الجلسة"""
    if 'hf_token' not in st.session_state:
        st.session_state.hf_token = ""
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "DeepSeek OCR"
    if 'api_status' not in st.session_state:
        st.session_state.api_status = "غير معروف"
    if 'model_ready' not in st.session_state:
        st.session_state.model_ready = False

def get_api_url(model_name):
    """الحصول على عنوان API للنموذج المحدد"""
    model_id = OCR_MODELS.get(model_name, "deepseek-ai/deepseek-ocr")
    return f"https://api-inference.huggingface.co/models/{model_id}"

def check_model_status():
    """فحص حالة النموذج وAPI"""
    if not st.session_state.hf_token:
        return {"error": "⚠️ يرجى إدخال Hugging Face Token أولاً"}
    
    model_id = OCR_MODELS.get(st.session_state.selected_model, "deepseek-ai/deepseek-ocr")
    api_url = f"https://huggingface.co/api/models/{model_id}"
    
    try:
        # فحص وجود النموذج
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            model_info = response.json()
            
            # فحص إذا كان النموذج متاحاً على Inference API
            headers = {"Authorization": f"Bearer {st.session_state.hf_token}"}
            inference_url = get_api_url(st.session_state.selected_model)
            
            # محاولة استدعاء بسيط لفحص حالة النموذج
            test_response = requests.get(
                f"https://api-inference.huggingface.co/status/{model_id}",
                headers=headers,
                timeout=10
            )
            
            if test_response.status_code == 200:
                status_info = test_response.json()
                loaded = status_info.get('loaded', False)
                state = status_info.get('state', 'Unknown')
                
                return {
                    "status": "success",
                    "model_exists": True,
                    "model_ready": loaded,
                    "model_state": state,
                    "model_name": model_info.get('modelId', ''),
                    "downloads": model_info.get('downloads', 0)
                }
            else:
                return {
                    "status": "warning",
                    "model_exists": True,
                    "model_ready": False,
                    "model_state": "غير معروف",
                    "message": "النموذج موجود ولكن لا يمكن الوصول له عبر API"
                }
                
        elif response.status_code == 404:
            return {
                "status": "error",
                "model_exists": False,
                "message": "النموذج غير موجود على Hugging Face"
            }
        else:
            return {
                "status": "error", 
                "model_exists": False,
                "message": f"خطأ في التحقق: {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "انتهت مهلة الاتصال"}
    except Exception as e:
        return {"status": "error", "message": f"خطأ في التحقق: {str(e)}"}

def query_ocr_api(image_bytes):
    """دالة لإرسال الصورة إلى OCR API"""
    if not st.session_state.hf_token:
        return {"error": "⚠️ يرجى إدخال Hugging Face Token أولاً"}
    
    headers = {"Authorization": f"Bearer {st.session_state.hf_token}"}
    api_url = get_api_url(st.session_state.selected_model)
    
    try:
        response = requests.post(api_url, headers=headers, data=image_bytes, timeout=60)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503:
            # محاولة تحميل النموذج
            load_response = requests.post(api_url, headers=headers, json={"inputs": ""}, timeout=30)
            if load_response.status_code == 200:
                return {"error": "النموذج كان قيد التحميل، يرجى المحاولة مرة أخرى"}
            return {"error": "النموذج قيد التحميل، يرجى المحاولة مرة أخرى بعد 10-20 ثانية"}
        elif response.status_code == 401:
            return {"error": "Token غير صالح أو منتهي الصلاحية"}
        elif response.status_code == 404:
            return {"error": "النموذج غير موجود على Inference API"}
        elif response.status_code == 429:
            return {"error": "تم تجاوز الحد المسموح. حاول مرة أخرى لاحقاً."}
        else:
            return {"error": f"خطأ في API: {response.status_code} - {response.text}"}
            
    except requests.exceptions.Timeout:
        return {"error": "انتهت مهلة الطلب، يرجى المحاولة مرة أخرى"}
    except Exception as e:
        return {"error": f"خطأ في الاتصال: {str(e)}"}

def pdf_to_images(pdf_file):
    """تحويل PDF إلى قائمة من الصور"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_file.getvalue())
            tmp_path = tmp_file.name
        
        doc = fitz.open(tmp_path)
        images = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        
        doc.close()
        os.unlink(tmp_path)
        return images
        
    except Exception as e:
        return {"error": f"خطأ في تحويل PDF: {str(e)}"}

# تهيئة حالة الجلسة
init_session_state()

# الشريط الجانبي للإعدادات
with st.sidebar:
    st.title("⚙️ إعدادات API")
    st.markdown("---")
    
    # إدخال Hugging Face Token
    st.subheader("🔑 Hugging Face Token")
    st.text_input(
        "أدخل Hugging Face Token",
        value=st.session_state.hf_token,
        key="hf_token_input",
        type="password",
        help="احصل على Token من: https://huggingface.co/settings/tokens"
    )
    
    # اختيار النموذج
    st.subheader("🤖 اختيار النموذج")
    selected_model = st.selectbox(
        "اختر نموذج OCR",
        options=list(OCR_MODELS.keys()),
        index=list(OCR_MODELS.keys()).index(st.session_state.selected_model),
        help="اختر النموذج المناسب لنوع النص المطلوب"
    )
    
    # تحديث النموذج المختار
    if selected_model != st.session_state.selected_model:
        st.session_state.selected_model = selected_model
        st.session_state.api_status = "غير معروف"
        st.session_state.model_ready = False
    
    st.markdown("---")
    
    # فحص حالة API
    st.subheader("🔍 فحص حالة النموذج")
    
    if st.button("📡 فحص حالة النموذج", use_container_width=True):
        if st.session_state.hf_token:
            with st.spinner("جاري فحص حالة النموذج..."):
                status_result = check_model_status()
                
            if status_result["status"] == "success":
                st.success("✅ النموذج متاح وجاهز للاستخدام")
                st.session_state.api_status = "نشط"
                st.session_state.model_ready = True
                
                # عرض معلومات إضافية
                with st.expander("معلومات النموذج"):
                    st.write(f"**اسم النموذج:** {status_result.get('model_name', '')}")
                    st.write(f"**الحالة:** {status_result.get('model_state', '')}")
                    st.write(f"**عدد التحميلات:** {status_result.get('downloads', 0)}")
                    
            elif status_result["status"] == "warning":
                st.warning("⚠️ النموذج موجود ولكن قد لا يكون جاهزاً")
                st.session_state.api_status = "تحذير"
                st.session_state.model_ready = False
                st.info(status_result.get("message", ""))
                
            else:
                st.error("❌ مشكلة في النموذج")
                st.session_state.api_status = "خطأ"
                st.session_state.model_ready = False
                st.error(status_result.get("message", ""))
        else:
            st.error("⚠️ يرجى إدخال Token أولاً")
    
    # عرض حالة النموذج الحالية
    if st.session_state.api_status != "غير معروف":
        st.metric("حالة النموذج", st.session_state.api_status)
    
    st.markdown("---")
    
    # معلومات التخزين
    st.info("""
    **معلومات التخزين:**
    - يتم حفظ الإعدادات في جلسة المتصفح الحالية
    - البيانات لا تخزن على السيرفر
    - يتم مسح البيانات عند إغلاق المتصفح
    """)
    
    # زر مسح الإعدادات
    if st.button("🗑️ مسح الإعدادات", use_container_width=True):
        for key in ['hf_token', 'selected_model', 'api_status', 'model_ready']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# الواجهة الرئيسية
st.title("🔍 DeepSeek OCR - استخراج النص من الصور وPDF")
st.write("رفع صورة أو ملف PDF لاستخراج النص باستخدام نماذج OCR")

# عرض معلومات النموذج
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"**النموذج:** {st.session_state.selected_model}")
with col2:
    status_color = "🟢" if st.session_state.api_status == "نشط" else "🟡" if st.session_state.api_status == "تحذير" else "🔴"
    st.info(f"**الحالة:** {status_color} {st.session_state.api_status}")
with col3:
    if st.session_state.hf_token:
        st.success("🔑 Token متوفر")
    else:
        st.error("🔑 Token غير متوفر")

# التحقق من إدخال Token
if not st.session_state.hf_token:
    st.warning("⚠️ يرجى إدخال Hugging Face Token في الشريط الجانبي لبدء الاستخدام")

# قسم رفع الملف
with st.container():
    st.subheader("📁 رفع الملف")
    uploaded_file = st.file_uploader(
        "اختر صورة أو ملف PDF", 
        type=["jpg", "jpeg", "png", "bmp", "pdf"],
        label_visibility="collapsed",
        disabled=not st.session_state.hf_token
    )

if uploaded_file is not None and st.session_state.hf_token:
    if not st.session_state.model_ready:
        st.warning("⚠️ يرجى فحص حالة النموذج أولاً للتأكد من أنه جاهز للاستخدام")
    
    if uploaded_file.type == "application/pdf":
        # معالجة ملف PDF
        st.info("📄 تم رفع ملف PDF - جاري التحويل إلى صور...")
        
        with st.spinner("جاري تحويل PDF إلى صور..."):
            pdf_images = pdf_to_images(uploaded_file)
        
        if isinstance(pdf_images, dict) and "error" in pdf_images:
            st.error(f"❌ {pdf_images['error']}")
        else:
            st.success(f"✅ تم تحويل PDF إلى {len(pdf_images)} صفحة")
            
            all_extracted_text = []
            
            for i, img in enumerate(pdf_images):
                st.subheader(f"الصفحة {i+1}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.image(img, use_container_width=True, caption=f"الصفحة {i+1}")
                
                with col2:
                    if st.button(f"استخراج النص من الصفحة {i+1}", key=f"btn_{i}", 
                               disabled=not st.session_state.model_ready):
                        with st.spinner(f"جاري معالجة الصفحة {i+1}..."):
                            img_bytes = io.BytesIO()
                            img.save(img_bytes, format='PNG')
                            img_bytes = img_bytes.getvalue()
                            
                            result = query_ocr_api(img_bytes)
                        
                        if "error" in result:
                            st.error(f"❌ {result['error']}")
                        else:
                            st.success("✅ تم استخراج النص بنجاح!")
                            
                            if isinstance(result, list) and len(result) > 0:
                                extracted_text = result[0].get('generated_text', '')
                                if extracted_text:
                                    st.text_area(
                                        f"النص من الصفحة {i+1}",
                                        extracted_text,
                                        height=150,
                                        key=f"text_{i}"
                                    )
                                    all_extracted_text.append(f"--- الصفحة {i+1} ---\n{extracted_text}\n")
            
            if all_extracted_text:
                st.subheader("📝 كل النصوص المستخرجة")
                full_text = "\n".join(all_extracted_text)
                st.text_area("النص الكامل", full_text, height=300)
                
                st.download_button(
                    label="📥 تحميل النص كملف",
                    data=full_text,
                    file_name="النص_المستخرج.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    else:
        # معالجة الصور العادية
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("الصورة المرفوعة")
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)
        
        with col2:
            st.subheader("النتائج")
            if st.button("🎯 استخراج النص", type="primary", use_container_width=True,
                       disabled=not st.session_state.model_ready):
                with st.spinner("جاري معالجة الصورة وتحليل النص..."):
                    img_bytes = uploaded_file.getvalue()
                    result = query_ocr_api(img_bytes)
                
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                    
                    if "غير موجود" in result["error"]:
                        st.info("💡 **الحل:** جرب نموذجاً مختلفاً أو تحقق من حالة النموذج")
                    elif "قيد التحميل" in result["error"]:
                        st.info("💡 **الحل:** انتظر 30 ثانية ثم حاول مرة أخرى")
                        
                else:
                    st.success("✅ تم استخراج النص بنجاح!")
                    
                    if isinstance(result, list) and len(result) > 0:
                        extracted_text = result[0].get('generated_text', '')
                        if extracted_text:
                            st.text_area("النص المستخرج", extracted_text, height=200)
                            
                            st.download_button(
                                label="📥 تحميل النص",
                                data=extracted_text,
                                file_name="النص_المستخرج.txt",
                                mime="text/plain",
                                use_container_width=True
                            )

# قسم استكشاف الأخطاء
with st.expander("🛠️ استكشاف الأخطاء والإصلاح"):
    st.markdown("""
    ### 🔍 إذا لم تعمل أي نماذج:
    
    1. **تحقق من صحة Token:**
       - تأكد من أن Token صالح ولم ينتهي
       - تأكد من أن لديك صلاحيات كافية
    
    2. **جرب نماذج مختلفة:**
       - كل نموذج مخصص لنوع معين من النصوص
       - بعض النماذج تحتاج وقت للتحميل أول مرة
    
    3. **تحقق من حالة النموذج:**
       - استخدم زر "فحص حالة النموذج"
       - إذا كان النموذج غير جاهز، انتظر دقيقة وحاول مرة أخرى
    
    4. **المشاكل الشائعة:**
       - **النموذج قيد التحميل:** انتظر 30-60 ثانية
       - **الحد المسموح:** قد تكون وصلت للحد المجاني
       - **مشكلة في الاتصال:** تحقق من اتصال الإنترنت
    
    5. **بدائل:**
       - جرب استخدام نماذج محلية
       - استخدم خدمات OCR أخرى مثل Google Vision أو Azure Computer Vision
    """)

# تذييل الصفحة
st.markdown("---")
st.caption("Powered by Hugging Face Models | تم التطوير للعمل على Streamlit Cloud")