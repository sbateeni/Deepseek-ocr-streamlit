"""
صفحة تحويل الصور إلى PDF
Image to PDF conversion page
"""

import streamlit as st
from PIL import Image
from core.pdf_handler import PDFHandler
from config import SUPPORTED_IMAGE_TYPES

def render_img_to_pdf_page():
    st.title("🖼️ تحويل الصور إلى PDF")
    st.write("ارفع مجموعة من الصور لدمجها في ملف PDF واحد عالي الجودة.")
    
    st.markdown("---")
    
    # رفع ملفات متعددة
    uploaded_images = st.file_uploader(
        "📁 ارفع الصور",
        type=SUPPORTED_IMAGE_TYPES,
        accept_multiple_files=True,
        help="يمكنك اختيار عدة صور في وقت واحد",
        key="multi_image_uploader"
    )
    
    if uploaded_images:
        st.success(f"✅ تم رفع {len(uploaded_images)} صورة")
        
        # عرض الصور وتجهيزها
        images = []
        
        st.subheader("🖼️ معاينة وترتيب")
        st.caption("سيتم حفظ الصور في الـ PDF بنفس ترتيب رفعها.")
        
        # عرض الصور في شبكة (Grid)
        cols = st.columns(4)
        for idx, uploaded_file in enumerate(uploaded_images):
            with cols[idx % 4]:
                img = Image.open(uploaded_file)
                st.image(img, use_container_width=True, caption=f"صورة {idx+1}")
                images.append(img)
        
        st.markdown("---")
        
        # خيارات الملف
        col1, col2 = st.columns(2)
        with col1:
            pdf_name = st.text_input("📝 اسم ملف PDF", value="merged_images.pdf")
            if not pdf_name.endswith('.pdf'):
                pdf_name += '.pdf'
        
        with col2:
            st.write("") # موازنة المحاذاة
            st.write("")
            if st.button("🚀 إنشاء ملف PDF", type="primary", use_container_width=True):
                with st.spinner("جاري إنشاء ملف PDF..."):
                    pdf_data = PDFHandler.images_to_pdf(images)
                    
                if pdf_data:
                    st.success("✨ تم إنشاء ملف PDF بنجاح!")
                    st.download_button(
                        label="📥 تحميل ملف PDF",
                        data=pdf_data,
                        file_name=pdf_name,
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.error("❌ فشل تحويل الصور إلى PDF.")

    else:
        # عرض تعليمات إذا لم يتم رفع صور
        st.info("""
        **💡 كيف تستخدم هذه الصفحة:**
        1. حدد مجموعة من الصور من جهازك.
        2. ارفعها جميعاً مرة واحدة.
        3. راجع الصور في المعاينة.
        4. اضغط على 'إنشاء ملف PDF' ثم قم بتحميل النتيجة.
        """)
