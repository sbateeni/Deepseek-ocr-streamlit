"""
الشريط الجانبي — إعدادات OCR ومعالجة الصور
Sidebar — OCR settings and image processing options
"""

import streamlit as st
import time

from config import (
    TESSERACT_LANGUAGES,
    TESSERACT_PSM_MODES,
    HF_OCR_MODELS,
    ENHANCEMENT_DEFAULTS,
    PDF_DPI_OPTIONS,
    DEFAULT_PDF_DPI,
)
from core.ocr_engine import TesseractOCR, HFInferenceOCR


def render_sidebar():
    """رسم الشريط الجانبي بجميع الإعدادات"""
    with st.sidebar:
        st.title("⚙️ إعدادات النظام")
        st.markdown("---")

        # ═══════════════════════════════════════════════════
        # اختيار طريقة OCR
        # ═══════════════════════════════════════════════════
        st.subheader("🔍 محرك OCR")

        ocr_method = st.radio(
            "اختر طريقة استخراج النص",
            options=["Tesseract (محلي)", "HF Inference API (سحابي)"],
            index=0,
            help="Tesseract: مجاني، محلي، يدعم العربية\n"
                 "HF API: يحتاج Token، نماذج متقدمة",
            key="ocr_method_radio",
        )
        st.session_state.ocr_method = ocr_method

        st.markdown("---")

        # ═══════════════════════════════════════════════════
        # إعدادات حسب المحرك المختار
        # ═══════════════════════════════════════════════════
        if "Tesseract" in ocr_method:
            _render_tesseract_settings()
        else:
            _render_hf_settings()

        st.markdown("---")

        # ═══════════════════════════════════════════════════
        # إعدادات معالجة الصور
        # ═══════════════════════════════════════════════════
        _render_image_settings()

        st.markdown("---")

        # ═══════════════════════════════════════════════════
        # إعدادات PDF
        # ═══════════════════════════════════════════════════
        _render_pdf_settings()


def _render_tesseract_settings():
    """إعدادات Tesseract"""
    st.subheader("🖥️ إعدادات Tesseract")

    # حالة Tesseract
    if TesseractOCR.is_available():
        st.success("✅ Tesseract مثبّت وجاهز")

        # اللغات المتاحة
        available = TesseractOCR.get_available_languages()
        if available:
            st.caption(f"اللغات المثبتة: {', '.join(available)}")
    else:
        st.error(
            "❌ Tesseract غير مثبّت\n\n"
            "على Streamlit Cloud: أضف `packages.txt` مع `tesseract-ocr`"
        )

    # اختيار اللغة
    lang = st.selectbox(
        "🌍 لغة النص",
        options=list(TESSERACT_LANGUAGES.keys()),
        index=list(TESSERACT_LANGUAGES.keys()).index(
            st.session_state.tess_language
        ),
        key="tess_language_select",
    )
    st.session_state.tess_language = lang

    # وضع تقسيم الصفحة
    psm = st.selectbox(
        "📐 وضع تقسيم الصفحة",
        options=list(TESSERACT_PSM_MODES.keys()),
        index=list(TESSERACT_PSM_MODES.keys()).index(
            st.session_state.tess_psm
        ),
        help="يُحدد كيف يقرأ Tesseract الصفحة:\n"
             "- تلقائي: الأفضل لمعظم الحالات\n"
             "- سطر واحد: لقراءة سطر فقط\n"
             "- كلمة واحدة: لقراءة كلمة فقط",
        key="tess_psm_select",
    )
    st.session_state.tess_psm = psm

    # عرض نسبة الثقة
    st.session_state.show_confidence = st.checkbox(
        "📊 عرض نسبة الثقة لكل كلمة",
        value=st.session_state.show_confidence,
        key="show_conf_check",
    )


def _render_hf_settings():
    """إعدادات HF Inference API"""
    st.subheader("☁️ إعدادات HF API")

    # إدخال Token
    token = st.text_input(
        "🔑 Hugging Face Token",
        value=st.session_state.hf_token,
        type="password",
        help="احصل على Token من: https://huggingface.co/settings/tokens",
        key="hf_token_input",
    )

    if token != st.session_state.hf_token:
        st.session_state.hf_token = token
        st.session_state.hf_api_status = "غير معروف"
        st.session_state.hf_model_ready = False

    # اختيار النموذج
    model_names = list(HF_OCR_MODELS.keys())
    selected = st.selectbox(
        "🤖 النموذج",
        options=model_names,
        index=model_names.index(st.session_state.hf_model),
        key="hf_model_select",
    )

    if selected != st.session_state.hf_model:
        st.session_state.hf_model = selected
        st.session_state.hf_api_status = "غير معروف"
        st.session_state.hf_model_ready = False

    # وصف النموذج
    model_info = HF_OCR_MODELS.get(selected, {})
    st.caption(model_info.get("description", ""))

    # أزرار إدارة النموذج
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📡 فحص", use_container_width=True, key="hf_check_btn"):
            if st.session_state.hf_token:
                with st.spinner("جاري الفحص..."):
                    result = HFInferenceOCR.check_model_status(
                        st.session_state.hf_model,
                        st.session_state.hf_token,
                    )
                st.session_state.hf_api_status = result.get("status", "error")
                st.session_state.hf_model_ready = result.get("ready", False)

                if result["status"] == "success":
                    st.success(result["message"])
                elif result["status"] == "loading":
                    st.warning(result["message"])
                else:
                    st.error(result.get("message", "خطأ"))
            else:
                st.error("⚠️ أدخل Token أولاً")

    with col2:
        if st.button("🔄 تحميل", use_container_width=True, key="hf_load_btn"):
            if st.session_state.hf_token:
                with st.spinner("جاري التحميل..."):
                    result = HFInferenceOCR.force_load_model(
                        st.session_state.hf_model,
                        st.session_state.hf_token,
                    )
                if result["status"] == "success":
                    st.success(result["message"])
                    st.session_state.hf_model_ready = True
                elif result["status"] == "loading":
                    st.warning(result["message"])
                else:
                    st.error(result["message"])
            else:
                st.error("⚠️ أدخل Token أولاً")

    # تحذير إذا لم يكن Token موجوداً
    if not st.session_state.hf_token:
        st.warning(
            "🔑 أدخل [HF Token](https://huggingface.co/settings/tokens) "
            "لاستخدام النماذج السحابية"
        )


def _render_image_settings():
    """إعدادات معالجة الصور"""
    st.subheader("🖼️ معالجة الصور")

    st.session_state.enable_enhancement = st.checkbox(
        "✨ تفعيل تحسين الصور",
        value=st.session_state.enable_enhancement,
        help="يحسّن جودة الصورة قبل استخراج النص",
        key="enhance_check",
    )

    if st.session_state.enable_enhancement:
        st.session_state.contrast = st.slider(
            "التباين",
            min_value=0.5,
            max_value=3.0,
            value=st.session_state.contrast,
            step=0.1,
            key="contrast_slider",
        )

        st.session_state.brightness = st.slider(
            "السطوع",
            min_value=0.5,
            max_value=2.0,
            value=st.session_state.brightness,
            step=0.05,
            key="brightness_slider",
        )

        st.session_state.sharpness = st.slider(
            "الحدة",
            min_value=0.5,
            max_value=3.0,
            value=st.session_state.sharpness,
            step=0.1,
            key="sharpness_slider",
        )

        # خيارات متقدمة
        with st.expander("⚙️ خيارات متقدمة"):
            st.session_state.grayscale = st.checkbox(
                "تحويل للرمادي",
                value=st.session_state.grayscale,
                help="يحسّن الدقة لـ Tesseract",
                key="grayscale_check",
            )

            st.session_state.denoise = st.checkbox(
                "إزالة الضوضاء",
                value=st.session_state.denoise,
                help="يزيل التشويش من الصورة",
                key="denoise_check",
            )

            st.session_state.binarize = st.checkbox(
                "تحويل ثنائي (أبيض/أسود)",
                value=st.session_state.binarize,
                help="يحوّل الصورة لأبيض وأسود فقط",
                key="binarize_check",
            )
            
            st.session_state.show_processed = st.checkbox(
                "👁️ عرض الصورة المعالجة",
                value=st.session_state.get("show_processed", False),
                help="يعرض الصورة كما يراها محرك OCR",
                key="show_processed_check",
            )

        # زر إعادة الإعدادات الافتراضية
        if st.button("🔄 إعادة الافتراضي", key="reset_enhance_btn"):
            st.session_state.contrast = ENHANCEMENT_DEFAULTS["contrast"]
            st.session_state.brightness = ENHANCEMENT_DEFAULTS["brightness"]
            st.session_state.sharpness = ENHANCEMENT_DEFAULTS["sharpness"]
            st.session_state.grayscale = True
            st.session_state.denoise = True
            st.session_state.binarize = False
            st.rerun()


def _render_pdf_settings():
    """إعدادات PDF"""
    st.subheader("📄 إعدادات PDF")

    dpi = st.selectbox(
        "جودة التحويل (DPI)",
        options=list(PDF_DPI_OPTIONS.keys()),
        index=list(PDF_DPI_OPTIONS.keys()).index(st.session_state.pdf_dpi),
        help="DPI أعلى = جودة أفضل لكن أبطأ",
        key="pdf_dpi_select",
    )
    st.session_state.pdf_dpi = dpi
