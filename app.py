"""
🔍 نظام استخراج النص من الصور و PDF
OCR System — Tesseract (local) + HF Inference API (cloud)

نقطة الدخول الرئيسية
"""

import streamlit as st

# إعدادات الصفحة — يجب أن تكون أول أمر Streamlit
st.set_page_config(
    page_title="نظام OCR — استخراج النص",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════
# تحميل الوحدات بعد set_page_config
# ═══════════════════════════════════════════════════════════
from utils.session import init_session_state
from ui.sidebar import render_sidebar
from ui.main_page import render_main_page
from ui.img_to_pdf_page import render_img_to_pdf_page  # جديد
from ui.components import render_status_bar


def main():
    """نقطة الدخول الرئيسية"""
    # 1. تهيئة حالة الجلسة
    init_session_state()

    # 2. رسم الشريط الجانبي (الإعدادات العامة لم تظهر هنا بل في sidebar.py)
    render_sidebar()

    # 3. اختيار الصفحة (إما من الجلسة أو السحب المباشر)
    with st.sidebar:
        st.markdown("---")
        st.subheader("📑 التنقل")
        app_page = st.selectbox(
            "اختر الصفحة",
            ["🔍 استخراج النص (OCR)", "🖼️ تحويل الصور لـ PDF"],
            key="navigation_selector"
        )
    
    # 4. عرض الصفحة المختارة
    if app_page == "🔍 استخراج النص (OCR)":
        render_status_bar()
        render_main_page()
    else:
        render_img_to_pdf_page()

    # 5. التذييل
    st.markdown("---")
    st.caption(
        "🔍 OCR System | "
        "Tesseract + HF Inference API | "
        "Image to PDF Tools"
    )


if __name__ == "__main__":
    main()
