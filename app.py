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
from ui.components import render_status_bar


def main():
    """نقطة الدخول الرئيسية"""
    # 1. تهيئة حالة الجلسة
    init_session_state()

    # 2. رسم الشريط الجانبي
    render_sidebar()

    # 3. شريط الحالة
    render_status_bar()

    # 4. الصفحة الرئيسية
    render_main_page()

    # 5. التذييل
    st.markdown("---")
    st.caption(
        "🔍 OCR System | "
        "Tesseract + HF Inference API | "
        "يدعم العربية والإنجليزية"
    )


if __name__ == "__main__":
    main()
