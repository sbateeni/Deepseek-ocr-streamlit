"""
الصفحة الرئيسية — رفع الملفات ومعالجتها وعرض النتائج
Main page — file upload, processing, and results display
"""

import streamlit as st
from PIL import Image
import io

from config import (
    SUPPORTED_FILE_TYPES,
    TESSERACT_LANGUAGES,
    TESSERACT_PSM_MODES,
)
from core.ocr_engine import TesseractOCR, HFInferenceOCR
from core.image_processor import ImageProcessor
from core.pdf_handler import PDFHandler
from ui.components import (
    render_result_card,
    render_export_section,
    render_processing_stats,
)
from utils.session import reset_results, add_result, get_full_text


def render_main_page():
    """رسم محتوى الصفحة الرئيسية"""
    st.title("🔍 نظام استخراج النص من الصور و PDF")
    st.caption(
        "Tesseract OCR (محلي، مجاني، يدعم العربية) "
        "أو HF Inference API (سحابي)"
    )

    # عرض معلومات النظام
    _render_system_info()

    st.markdown("---")

    # رفع الملف
    uploaded_file = st.file_uploader(
        "📁 ارفع صورة أو ملف PDF",
        type=SUPPORTED_FILE_TYPES,
        help="صيغ مدعومة: JPG, PNG, BMP, TIFF, WebP, PDF",
        key="file_uploader",
    )

    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            _handle_pdf(uploaded_file)
        else:
            _handle_image(uploaded_file)


def _render_system_info():
    """عرض معلومات مختصرة عن النظام"""
    if "Tesseract" in st.session_state.ocr_method:
        if TesseractOCR.is_available():
            st.success(
                "✅ **Tesseract OCR جاهز** — "
                "ارفع صورة أو PDF لاستخراج النص مباشرة"
            )
        else:
            st.error(
                "❌ **Tesseract غير مثبّت** — "
                "تأكد من وجود `packages.txt` مع `tesseract-ocr`"
            )
    else:
        if not st.session_state.hf_token:
            st.warning(
                "🔑 **أدخل HF Token** من الشريط الجانبي لاستخدام النماذج السحابية"
            )
        elif not st.session_state.hf_model_ready:
            st.warning(
                "⚠️ **حمّل النموذج** — اضغط 'تحميل' في الشريط الجانبي"
            )
        else:
            st.success("✅ **النموذج جاهز** — ارفع صورة أو PDF")


def _process_single_image(image: Image.Image, page_num: int = 1) -> dict:
    """
    معالجة صورة واحدة — تطبيق التحسينات واستخراج النص

    Returns:
        dict مع text, confidence (اختياري), engine
    """
    # 1. تحسين الصورة إذا مفعّل
    if st.session_state.enable_enhancement:
        processed = ImageProcessor.full_pipeline(
            image.copy(),
            contrast=st.session_state.contrast,
            brightness=st.session_state.brightness,
            sharpness=st.session_state.sharpness,
            grayscale=st.session_state.grayscale,
            denoise=st.session_state.denoise,
            binarize=st.session_state.binarize,
        )
    else:
        processed = image.copy()

    # 2. استخراج النص حسب المحرك المختار
    if "Tesseract" in st.session_state.ocr_method:
        lang_code = TESSERACT_LANGUAGES.get(
            st.session_state.tess_language, "eng"
        )
        psm_code = TESSERACT_PSM_MODES.get(
            st.session_state.tess_psm, 3
        )

        if st.session_state.show_confidence:
            result = TesseractOCR.extract_with_confidence(
                processed, lang=lang_code, psm=psm_code
            )
        else:
            result = TesseractOCR.extract_text(
                processed, lang=lang_code, psm=psm_code
            )
    else:
        # HF API
        img_bytes = ImageProcessor.image_to_bytes(processed)
        result = HFInferenceOCR.extract_text(
            img_bytes,
            st.session_state.hf_model,
            st.session_state.hf_token,
        )

    return result


def _handle_image(uploaded_file):
    """معالجة صورة مرفوعة"""
    image = Image.open(uploaded_file)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🖼️ الصورة")
        st.image(image, use_container_width=True, caption="الصورة الأصلية")
        
        # عرض الصورة المعالجة إذا مفعّل
        if st.session_state.get("show_processed"):
            st.markdown("---")
            st.subheader("✨ المعالجة")
            # نحاكي المعالجة للعرض
            processed_preview = ImageProcessor.full_pipeline(
                image.copy(),
                contrast=st.session_state.contrast,
                brightness=st.session_state.brightness,
                sharpness=st.session_state.sharpness,
                grayscale=st.session_state.grayscale,
                denoise=st.session_state.denoise,
                binarize=st.session_state.binarize,
            )
            st.image(processed_preview, use_container_width=True, caption="كيف يراها النظام")

        st.caption(
            f"الحجم: {image.size[0]}×{image.size[1]}px | "
            f"النوع: {image.mode}"
        )

    with col2:
        st.subheader("📝 النتائج")

        # زر الاستخراج
        can_process = _can_process()

        if st.button(
            "🎯 استخراج النص",
            type="primary",
            use_container_width=True,
            disabled=not can_process,
            key="extract_single_btn",
        ):
            reset_results()

            with st.spinner("⏳ جاري معالجة الصورة..."):
                result = _process_single_image(image)

            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                text = result.get("text", "")
                confidence = result.get("avg_confidence")
                engine = result.get("engine", "")

                add_result(1, text, confidence, engine)
                st.session_state.processing_complete = True

        # عرض النتائج
        if st.session_state.processing_complete and st.session_state.all_results:
            r = st.session_state.all_results[0]
            render_result_card(1, r["text"], r.get("confidence"))

    # قسم التصدير
    if st.session_state.processing_complete and st.session_state.all_results:
        render_processing_stats(st.session_state.all_results)
        render_export_section(st.session_state.all_results)


def _handle_pdf(uploaded_file):
    """معالجة ملف PDF"""
    st.info(f"📄 ملف PDF: **{uploaded_file.name}**")

    # معلومات الملف
    pdf_info = PDFHandler.get_pdf_info(uploaded_file)
    if "error" in pdf_info:
        st.error(f"❌ {pdf_info['error']}")
        return

    page_count = pdf_info["page_count"]
    st.success(f"📖 عدد الصفحات: **{page_count}**")

    # تحويل PDF إلى صور
    with st.spinner(f"جاري تحويل {page_count} صفحة إلى صور..."):
        pdf_result = PDFHandler.pdf_to_images(
            uploaded_file,
            dpi_label=st.session_state.pdf_dpi,
        )

    if isinstance(pdf_result, dict) and "error" in pdf_result:
        st.error(f"❌ {pdf_result['error']}")
        return

    images = pdf_result  # list of (page_num, image)

    # زر المعالجة الدفعية
    can_process = _can_process()

    col1, col2 = st.columns([2, 1])

    with col1:
        batch_btn = st.button(
            f"🚀 استخراج النص من جميع الصفحات ({page_count})",
            type="primary",
            use_container_width=True,
            disabled=not can_process,
            key="batch_extract_btn",
        )

    with col2:
        st.caption(f"DPI: {st.session_state.pdf_dpi}")

    # معالجة دفعية
    if batch_btn:
        reset_results()

        progress_bar = st.progress(0, text="جاري المعالجة...")

        for idx, (page_num, img) in enumerate(images):
            progress_bar.progress(
                (idx + 1) / len(images),
                text=f"معالجة الصفحة {page_num} من {page_count}...",
            )

            result = _process_single_image(img, page_num)

            if "error" not in result:
                text = result.get("text", "")
                confidence = result.get("avg_confidence")
                engine = result.get("engine", "")
                add_result(page_num, text, confidence, engine)
            else:
                add_result(page_num, f"[خطأ: {result['error']}]")

        progress_bar.progress(1.0, text="✅ اكتملت المعالجة!")
        st.session_state.processing_complete = True

    # عرض الصفحات والنتائج
    if images:
        st.markdown("---")
        st.subheader("📑 صفحات الملف")

        for page_num, img in images:
            with st.expander(
                f"📄 الصفحة {page_num}",
                expanded=False,
            ):
                img_col, result_col = st.columns(2)

                with img_col:
                    st.image(
                        img,
                        use_container_width=True,
                        caption=f"صفحة {page_num} — "
                                f"{img.size[0]}×{img.size[1]}px",
                    )

                with result_col:
                    # عرض النتيجة إذا موجودة
                    page_results = [
                        r
                        for r in st.session_state.all_results
                        if r["page"] == page_num
                    ]

                    if page_results:
                        r = page_results[0]
                        render_result_card(
                            page_num, r["text"], r.get("confidence")
                        )
                    else:
                        # زر استخراج فردي
                        if st.button(
                            f"🎯 استخراج",
                            key=f"extract_page_{page_num}",
                            disabled=not can_process,
                        ):
                            with st.spinner(f"معالجة الصفحة {page_num}..."):
                                result = _process_single_image(img, page_num)

                            if "error" not in result:
                                add_result(
                                    page_num,
                                    result.get("text", ""),
                                    result.get("avg_confidence"),
                                    result.get("engine", ""),
                                )
                                st.rerun()
                            else:
                                st.error(f"❌ {result['error']}")

    # عرض النتائج الكاملة
    if st.session_state.processing_complete and st.session_state.all_results:
        st.markdown("---")
        st.subheader("📊 ملخص النتائج")

        render_processing_stats(st.session_state.all_results)

        # النص الكامل
        with st.expander("📝 النص الكامل المستخرج", expanded=True):
            full_text = get_full_text()
            st.text_area(
                "النص الكامل",
                full_text,
                height=400,
                key="full_text_area",
                label_visibility="collapsed",
            )

        render_export_section(st.session_state.all_results)


def _can_process() -> bool:
    """فحص إمكانية المعالجة"""
    if "Tesseract" in st.session_state.ocr_method:
        return TesseractOCR.is_available()
    else:
        return bool(
            st.session_state.hf_token and st.session_state.hf_model_ready
        )
