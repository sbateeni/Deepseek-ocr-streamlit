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

# عناوين API محتملة لـ DeepSeek OCR
DEFAULT_API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-ocr"

# نماذج OCR بديلة إذا كان النموذج الأساسي غير متاح
ALTERNATE_MODELS = {
    "DeepSeek OCR": "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-ocr",
    "Microsoft TrOCR": "https://api-inference.huggingface.co/models/microsoft/trocr-base-printed",
    "Google T5 OCR": "https://api-inference.huggingface.co/models/microsoft/trocr-base-handwritten",
}

def init_session_state():
    """تهيئة حالة الجلسة"""
    if 'hf_token' not in st.session_state:
        st.session_state.hf_token = ""
    if 'api_url' not in st.session_state:
        st.session_state.api_url = DEFAULT_API_URL
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "DeepSeek OCR"

def save_api_config():
    """حفظ إعدادات API في session state"""
    st.session_state.hf_token = st.session_state.hf_token_input
    st.session_state.api_url = st.session_state.api_url_input
    st.session_state.selected_model = st.session_state.model_selector

def query_deepseek_ocr(image_bytes):
    """دالة لإرسال الصورة إلى OCR API"""
    if not st.session_state.hf_token:
        return {"error": "⚠️ يرجى إدخال Hugging Face Token أولاً"}
    
    headers = {"Authorization": f"Bearer {st.session_state.hf_token}"}
    
    try:
        response = requests.post(st.session_state.api_url, headers=headers, data=image_bytes, timeout=60)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503:
            return {"error": "النموذج قيد التحميل، يرجى المحاولة مرة أخرى بعد 10-20 ثانية"}
        elif response.status_code == 401:
            return {"error": "Token غير صالح أو منتهي الصلاحية"}
        elif response.status_code == 404:
            return {"error": "النموذج غير موجود. جرب نموذجاً آخر من القائمة."}
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
        # حفظ الملف المؤقت
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_file.getvalue())
            tmp_path = tmp_file.name
        
        # فتح PDF باستخدام PyMuPDF
        doc = fitz.open(tmp_path)
        images = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # زيادة الدقة
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        
        doc.close()
        os.unlink(tmp_path)  # حذف الملف المؤقت
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
        help="احصل على Token من: https://huggingface.co/settings/tokens",
        on_change=save_api_config
    )
    
    # اختيار النموذج
    st.subheader("🤖 اختيار النموذج")
    st.selectbox(
        "اختر نموذج OCR",
        options=list(ALTERNATE_MODELS.keys()),
        key="model_selector",
        index=list(ALTERNATE_MODELS.keys()).index(st.session_state.selected_model),
        on_change=save_api_config,
        help="إذا لم يعمل نموذج DeepSeek، جرب نماذج أخرى"
    )
    
    # إدخال عنوان API مخصص
    st.subheader("🌐 عنوان API مخصص")
    st.text_input(
        "أدخل عنوان API مخصص (اختياري)",
        value=st.session_state.api_url,
        key="api_url_input",
        help=f"اتركه فارغاً للاستخدام الافتراضي",
        on_change=save_api_config
    )
    
    # تحديث عنوان API بناءً على النموذج المختار
    if st.session_state.selected_model in ALTERNATE_MODELS:
        st.session_state.api_url = ALTERNATE_MODELS[st.session_state.selected_model]
    
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
        for key in ['hf_token', 'api_url', 'selected_model']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# الواجهة الرئيسية
st.title("🔍 DeepSeek OCR - استخراج النص من الصور وPDF")
st.write("رفع صورة أو ملف PDF لاستخراج النص باستخدام نماذج OCR")

# عرض النموذج المختار
if st.session_state.get('selected_model'):
    st.info(f"**النموذج المختار:** {st.session_state.selected_model}")

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
                    # التحديث: استخدام use_container_width بدلاً من use_column_width
                    st.image(img, use_container_width=True, caption=f"الصفحة {i+1}")
                
                with col2:
                    if st.button(f"استخراج النص من الصفحة {i+1}", key=f"btn_{i}"):
                        with st.spinner(f"جاري معالجة الصفحة {i+1}..."):
                            # تحويل الصورة إلى bytes
                            img_bytes = io.BytesIO()
                            img.save(img_bytes, format='PNG')
                            img_bytes = img_bytes.getvalue()
                            
                            result = query_deepseek_ocr(img_bytes)
                        
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
            
            # عرض كل النصوص معاً
            if all_extracted_text:
                st.subheader("📝 كل النصوص المستخرجة")
                full_text = "\n".join(all_extracted_text)
                st.text_area("النص الكامل", full_text, height=300)
                
                # تحميل النص كملف
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
            # التحديث: استخدام use_container_width بدلاً من use_column_width
            st.image(image, use_container_width=True)
        
        with col2:
            st.subheader("النتائج")
            if st.button("🎯 استخراج النص", type="primary", use_container_width=True):
                with st.spinner("جاري معالجة الصورة وتحليل النص..."):
                    img_bytes = uploaded_file.getvalue()
                    result = query_deepseek_ocr(img_bytes)
                
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                    
                    # اقتراحات استكشاف الأخطاء
                    if "غير موجود" in result["error"]:
                        st.info("💡 **حل مقترح:** جرب تغيير النموذج من القائمة في الشريط الجانبي")
                    elif "قيد التحميل" in result["error"]:
                        st.info("💡 **حل مقترح:** انتظر 20 ثانية ثم حاول مرة أخرى")
                        
                else:
                    st.success("✅ تم استخراج النص بنجاح!")
                    
                    if isinstance(result, list) and len(result) > 0:
                        extracted_text = result[0].get('generated_text', '')
                        if extracted_text:
                            st.text_area("النص المستخرج", extracted_text, height=200)
                            
                            # تحميل النص كملف
                            st.download_button(
                                label="📥 تحميل النص",
                                data=extracted_text,
                                file_name="النص_المستخرج.txt",
                                mime="text/plain",
                                use_container_width=True
                            )

# قسم التعليمات
with st.expander("📚 تعليمات الاستخدام واستكشاف الأخطاء"):
    st.markdown("""
    ### 🚀 كيفية الاستخدام:
    1. **أدخل Hugging Face Token** في الشريط الجانبي
    2. **اختر نموذج OCR** من القائمة
    3. **اختر ملف** (صورة أو PDF)
    4. **انقر على استخراج النص**
    5. **انسخ أو حمّل** النتائج

    ### 🔑 الحصول على Token:
    1. اذهب إلى [Hugging Face Settings](https://huggingface.co/settings/tokens)
    2. سجّل الدخول بحسابك
    3. أنشئ Token جديد (Role: Write)
    4. انسخه وأدخله في التطبيق

    ### 🛠️ استكشاف الأخطاء:
    
    **"النموذج غير موجود":**
    - جرب نموذجاً آخر من القائمة
    - تأكد من كتابة عنوان API بشكل صحيح
    
    **"النموذج قيد التحميل":**
    - انتظر 20-30 ثانية
    - حاول مرة أخرى
    
    **"Token غير صالح":**
    - تأكد من صحة Token
    - أنشئ Token جديد
    
    **📁 الملفات المدعومة:**
    - **الصور:** JPG, JPEG, PNG, BMP
    - **PDF:** متعدد الصفحات
    """)

# تذييل الصفحة
st.markdown("---")
st.caption("Powered by DeepSeek OCR & Hugging Face | تم التطوير للعمل على Streamlit Cloud")