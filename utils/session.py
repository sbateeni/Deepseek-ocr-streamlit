"""
إدارة حالة الجلسة (Session State)
Session state management for the Streamlit app
"""

import streamlit as st


def init_session_state():
    """تهيئة جميع متغيرات الجلسة"""
    defaults = {
        # طريقة OCR
        "ocr_method": "Tesseract (محلي)",

        # إعدادات Tesseract
        "tess_language": "إنجليزي",
        "tess_psm": "تلقائي كامل (مُوصى)",
        "show_confidence": True,

        # إعدادات HF API
        "hf_token": "",
        "hf_model": "TrOCR Large Printed",
        "hf_model_ready": False,
        "hf_api_status": "غير معروف",

        # إعدادات معالجة الصور
        "enable_enhancement": True,
        "contrast": 1.3,
        "brightness": 1.05,
        "sharpness": 1.5,
        "grayscale": True,
        "denoise": True,
        "binarize": False,

        # إعدادات PDF
        "pdf_dpi": "جيد (200 DPI)",

        # نتائج
        "all_results": [],
        "processing_complete": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_results():
    """مسح النتائج السابقة"""
    st.session_state.all_results = []
    st.session_state.processing_complete = False


def add_result(page_num: int, text: str, confidence: float = None, engine: str = ""):
    """إضافة نتيجة جديدة"""
    st.session_state.all_results.append(
        {
            "page": page_num,
            "text": text,
            "confidence": confidence,
            "engine": engine,
        }
    )


def get_full_text() -> str:
    """الحصول على النص الكامل من جميع النتائج"""
    parts = []
    for r in st.session_state.all_results:
        if len(st.session_state.all_results) > 1:
            parts.append(f"--- الصفحة {r['page']} ---")
        parts.append(r["text"])
    return "\n\n".join(parts)
