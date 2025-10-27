import streamlit as st
import requests
import json
from PIL import Image
import io
import fitz  # PyMuPDF
import tempfile
import os
import time

# إعدادات الصفحة
st.set_page_config(
    page_title="OCR System",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="expanded"
)

# نماذج OCR مع endpoints الجديدة
OCR_MODELS = {
    "Microsoft TrOCR Printed": {
        "model_id": "microsoft/trocr-base-printed",
        "description": "مناسب للنصوص المطبوعة"
    },
    "Microsoft TrOCR Handwritten": {
        "model_id": "microsoft/trocr-base-handwritten", 
        "description": "مناسب للنصوص المكتوبة بخط اليد"
    },
    "Donut OCR": {
        "model_id": "naver-clova-ix/donut-base-finetuned-cord-v2",
        "description": "نموذج متقدم للوثائق المنظمة"
    },
    "PaddleOCR En": {
        "model_id": "paddlepaddle/paddleocr-en",
        "description": "نموذج PaddleOCR للغة الإنجليزية"
    }
}

# قاعدة URL الجديدة
HF_BASE_URL = "https://router.huggingface.co/hf-inference/"
HF_STATUS_URL = "https://router.huggingface.co/hf-inference/status/"

def init_session_state():
    """تهيئة حالة الجلسة"""
    if 'hf_token' not in st.session_state:
        st.session_state.hf_token = ""
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "Microsoft TrOCR Printed"
    if 'api_status' not in st.session_state:
        st.session_state.api_status = "غير معروف"
    if 'model_ready' not in st.session_state:
        st.session_state.model_ready = False
    if 'last_check' not in st.session_state:
        st.session_state.last_check = None

def get_api_url():
    """الحصول على عنوان API الجديد للنموذج المحدد"""
    model_info = OCR_MODELS.get(st.session_state.selected_model, OCR_MODELS["Microsoft TrOCR Printed"])
    model_id = model_info["model_id"]
    return f"{HF_BASE_URL}models/{model_id}"

def get_status_url():
    """الحصول على عنوان حالة النموذج"""
    model_info = OCR_MODELS.get(st.session_state.selected_model, OCR_MODELS["Microsoft TrOCR Printed"])
    model_id = model_info["model_id"]
    return f"{HF_STATUS_URL}{model_id}"

def check_model_status():
    """فحص حالة النموذج باستخدام endpoint الجديد"""
    if not st.session_state.hf_token:
        return {"error": "⚠️ يرجى إدخال Hugging Face Token أولاً"}
    
    headers = {"Authorization": f"Bearer {st.session_state.hf_token}"}
    
    try:
        # فحص حالة النموذج باستخدام API الجديد
        status_url = get_status_url()
        response = requests.get(status_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            status_data = response.json()
            loaded = status_data.get('loaded', False)
            state = status_data.get('state', 'Unknown')
            
            if loaded:
                return {
                    "status": "success", 
                    "message": "✅ النموذج جاهز للاستخدام",
                    "ready": True,
                    "state": state
                }
            else:
                return {
                    "status": "loading",
                    "message": "🔄 النموذج قيد التحميل، يرجى استخدام زر تحميل النموذج",
                    "ready": False,
                    "state": state
                }
                
        elif response.status_code == 404:
            return {
                "status": "error",
                "message": "❌ النموذج غير موجود في النظام الجديد",
                "ready": False
            }
        else:
            return {
                "status": "error",
                "message": f"❌ خطأ في التحقق: {response.status_code}",
                "ready": False
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "⏰ انتهت مهلة الاتصال",
            "ready": False
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"❌ خطأ في الاتصال: {str(e)}",
            "ready": False
        }

def force_load_model():
    """إجبار تحميل النموذج باستخدام endpoint الجديد"""
    if not st.session_state.hf_token:
        return {"error": "⚠️ يرجى إدخال Hugging Face Token أولاً"}
    
    api_url = get_api_url()
    headers = {"Authorization": f"Bearer {st.session_state.hf_token}"}
    
    try:
        # إرسال طلب تجريبي لتحميل النموذج
        test_input = {"inputs": "test image data"}
        response = requests.post(api_url, headers=headers, json=test_input, timeout=60)
        
        if response.status_code == 200:
            return {
                "status": "success",
                "message": "✅ تم تحميل النموذج بنجاح"
            }
        elif response.status_code in [503, 422]:
            return {
                "status": "loading", 
                "message": "🔄 النموذج قيد التحميل، يرجى الانتظار 20-30 ثانية"
            }
        else:
            return {
                "status": "error",
                "message": f"❌ فشل في تحميل النموذج: {response.status_code}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ خطأ في تحميل النموذج: {str(e)}"
        }

def query_ocr_api(image_bytes):
    """دالة لإرسال الصورة إلى OCR API باستخدام endpoint الجديد"""
    if not st.session_state.hf_token:
        return {"error": "⚠️ يرجى إدخال Hugging Face Token أولاً"}
    
    headers = {"Authorization": f"Bearer {st.session_state.hf_token}"}
    api_url = get_api_url()
    
    try:
        # استخدام multipart/form-data لإرسال الصورة
        files = {'data': image_bytes}
        response = requests.post(api_url, headers=headers, files=files, timeout=60)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503:
            return {"error": "النموذج قيد التحميل، يرجى استخدام زر 'تحميل النموذج' أولاً"}
        elif response.status_code == 401:
            return {"error": "Token غير صالح أو منتهي الصلاحية"}
        elif response.status_code == 404:
            return {"error": "النموذج غير متاح في النظام الجديد"}
        elif response.status_code == 422:
            return {"error": "تنسيق الصورة غير مدعوم أو هناك مشكلة في معالجة النموذج"}
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

def preprocess_image(image):
    """معالجة مسبقة للصورة لتحسين جودة OCR"""
    # تحويل إلى رمادي إذا كانت ملونة
    if image.mode != 'L':
        image = image.convert('L')
    
    # تحسين الحجم للحفاظ على الجودة
    width, height = image.size
    if width > 1200 or height > 1200:
        ratio = min(1200/width, 1200/height)
        new_size = (int(width * ratio), int(height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    return image

# تهيئة حالة الجلسة
init_session_state()

# الشريط الجانبي للإعدادات
with st.sidebar:
    st.title("⚙️ إعدادات API")
    st.markdown("---")
    
    # إدخال Hugging Face Token
    st.subheader("🔑 Hugging Face Token")
    token = st.text_input(
        "أدخل Hugging Face Token",
        value=st.session_state.hf_token,
        key="hf_token_input",
        type="password",
        help="احصل على Token من: https://huggingface.co/settings/tokens",
        label_visibility="collapsed"
    )
    
    if token != st.session_state.hf_token:
        st.session_state.hf_token = token
        st.session_state.api_status = "غير معروف"
        st.session_state.model_ready = False
    
    # اختيار النموذج
    st.subheader("🤖 اختيار النموذج")
    selected_model = st.selectbox(
        "اختر نموذج OCR",
        options=list(OCR_MODELS.keys()),
        index=list(OCR_MODELS.keys()).index(st.session_state.selected_model),
        help="اختر النموذج المناسب لنوع النص المطلوب"
    )
    
    if selected_model != st.session_state.selected_model:
        st.session_state.selected_model = selected_model
        st.session_state.api_status = "غير معروف"
        st.session_state.model_ready = False
    
    # عرض معلومات النموذج
    if st.session_state.selected_model in OCR_MODELS:
        model_info = OCR_MODELS[st.session_state.selected_model]
        st.caption(f"📝 {model_info['description']}")
        st.caption(f"🔗 {model_info['model_id']}")
    
    st.markdown("---")
    
    # إدارة النموذج
    st.subheader("🔍 إدارة النموذج")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📡 فحص الحالة", use_container_width=True):
            if st.session_state.hf_token:
                with st.spinner("جاري فحص حالة النموذج..."):
                    status_result = check_model_status()
                
                st.session_state.api_status = status_result["status"]
                st.session_state.model_ready = status_result.get("ready", False)
                st.session_state.last_check = time.time()
                
                if status_result["status"] == "success":
                    st.success(status_result["message"])
                elif status_result["status"] == "loading":
                    st.warning(status_result["message"])
                else:
                    st.error(status_result["message"])
            else:
                st.error("⚠️ يرجى إدخال Token أولاً")
    
    with col2:
        if st.button("🔄 تحميل النموذج", use_container_width=True):
            if st.session_state.hf_token:
                with st.spinner("جاري تحميل النموذج..."):
                    load_result = force_load_model()
                
                if load_result["status"] == "success":
                    st.success(load_result["message"])
                    st.session_state.model_ready = True
                elif load_result["status"] == "loading":
                    st.warning(load_result["message"])
                    st.info("⏳ انتظر 30 ثانية ثم افحص الحالة مرة أخرى")
                else:
                    st.error(load_result["message"])
            else:
                st.error("⚠️ يرجى إدخال Token أولاً")
    
    # عرض حالة النموذج
    if st.session_state.api_status != "غير معروف":
        status_colors = {
            "success": "🟢",
            "loading": "🟡", 
            "error": "🔴"
        }
        status_color = status_colors.get(st.session_state.api_status, "⚪")
        st.metric("حالة النموذج", f"{status_color} {st.session_state.api_status}")
    
    st.markdown("---")
    
    # معلومات عن النظام الجديد
    st.info("""
    **✨ النظام الجديد:**
    - استخدام Inference Providers API
    - endpoints محدثة
    - دعم أفضل للنماذج
    """)

# الواجهة الرئيسية
st.title("🔍 نظام استخراج النص من الصور وPDF")
st.write("استخدم نماذج Hugging Face مع نظام Inference Providers الجديد")

# عرض حالة النظام
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"**النموذج:** {st.session_state.selected_model}")
with col2:
    status_display = {
        "success": "🟢 جاهز",
        "loading": "🟡 قيد التحميل", 
        "error": "🔴 خطأ",
        "غير معروف": "⚪ غير معروف"
    }
    current_status = status_display.get(st.session_state.api_status, "⚪ غير معروف")
    st.info(f"**الحالة:** {current_status}")
with col3:
    if st.session_state.hf_token:
        st.success("🔑 Token متوفر")
    else:
        st.error("🔑 Token مطلوب")

# معلومات عن التحديث
st.success("""
**🔄 تم التحديث إلى نظام Hugging Face الجديد**
- استخدام `router.huggingface.co/hf-inference/` بدلاً من `api-inference.huggingface.co`
- دعم Inference Providers API
- استمرارية أفضل للخدمة
""")

# تحذيرات
if not st.session_state.hf_token:
    st.error("""
    **⚠️ يرجى إدخال Hugging Face Token في الشريط الجانبي**
    
    - اذهب إلى [Hugging Face Settings](https://huggingface.co/settings/tokens)
    - أنشئ Token جديد (Role: Write)
    - أدخله في الحقل المخصص
    """)

elif not st.session_state.model_ready:
    st.warning("""
    **⚠️ النموذج غير جاهز للاستخدام**
    
    - اضغط على زر **"تحميل النموذج"** في الشريط الجانبي
    - انتظر حتى تظهر رسالة التأكيد
    - قد تستغرق العملية 20-30 ثانية لأول مرة
    """)

# قسم رفع الملف
st.subheader("📁 رفع الملف")
uploaded_file = st.file_uploader(
    "اختر صورة أو ملف PDF", 
    type=["jpg", "jpeg", "png", "bmp", "pdf"],
    label_visibility="collapsed",
    disabled=not st.session_state.model_ready
)

if uploaded_file is not None and st.session_state.hf_token and st.session_state.model_ready:
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
                    if st.button(f"استخراج النص من الصفحة {i+1}", key=f"btn_{i}"):
                        with st.spinner(f"جاري معالجة الصفحة {i+1}..."):
                            # معالجة مسبقة للصورة
                            processed_img = preprocess_image(img)
                            
                            img_bytes = io.BytesIO()
                            processed_img.save(img_bytes, format='PNG')
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
                            elif isinstance(result, dict) and 'text' in result:
                                extracted_text = result['text']
                                st.text_area(
                                    f"النص من الصفحة {i+1}",
                                    extracted_text,
                                    height=150,
                                    key=f"text_{i}"
                                )
                                all_extracted_text.append(f"--- الصفحة {i+1} ---\n{extracted_text}\n")
            
            if all_extracted_text:
                st.subheader("📝 النص الكامل المستخرج")
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
            if st.button("🎯 استخراج النص", type="primary", use_container_width=True):
                with st.spinner("جاري معالجة الصورة وتحليل النص..."):
                    # معالجة مسبقة للصورة
                    processed_image = preprocess_image(image)
                    
                    img_bytes = io.BytesIO()
                    processed_image.save(img_bytes, format='PNG')
                    img_bytes = img_bytes.getvalue()
                    
                    result = query_ocr_api(img_bytes)
                
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success("✅ تم استخراج النص بنجاح!")
                    
                    extracted_text = ""
                    if isinstance(result, list) and len(result) > 0:
                        extracted_text = result[0].get('generated_text', '')
                    elif isinstance(result, dict) and 'text' in result:
                        extracted_text = result['text']
                    
                    if extracted_text:
                        st.text_area("النص المستخرج", extracted_text, height=200)
                        
                        st.download_button(
                            label="📥 تحميل النص",
                            data=extracted_text,
                            file_name="النص_المستخرج.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

# قسم المعلومات
with st.expander("ℹ️ معلومات عن النظام الجديد"):
    st.markdown("""
    ### 🚀 Hugging Face Inference Providers API الجديد
    
    **ما الجديد:**
    - ✅ نظام serverless محسن
    - ✅ وصول إلى المزيد من النماذج
    - ✅ API موحد لجميع النماذج
    - ✅ أداء أفضل وموثوقية أعلى
    
    **التغييرات:**
    - 🔄 `api-inference.huggingface.co` → `router.huggingface.co/hf-inference/`
    - 🔄 دعم أفضل لتنسيقات البيانات
    - 🔄 إدارة محسنة للنماذج
    
    **الفوائد:**
    - ⚡ استجابة أسرع
    - 🔄 تحديثات تلقائية
    - 📈 قابلة للتوسع بشكل أفضل
    
    للمزيد: [Inference Providers Documentation](https://huggingface.co/docs/inference-providers)
    """)

# تذييل الصفحة
st.markdown("---")
st.caption("Powered by Hugging Face Inference Providers API | تم التحديث للنظام الجديد")