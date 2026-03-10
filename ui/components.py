"""
مكونات واجهة المستخدم المشتركة
Shared UI components
"""

import streamlit as st


def render_status_bar():
    """عرض شريط حالة النظام في أعلى الصفحة"""
    from core.ocr_engine import TesseractOCR

    col1, col2, col3 = st.columns(3)

    with col1:
        method = st.session_state.ocr_method
        icon = "🖥️" if "Tesseract" in method else "☁️"
        st.info(f"**المحرك:** {icon} {method}")

    with col2:
        if "Tesseract" in st.session_state.ocr_method:
            if TesseractOCR.is_available():
                st.success("🟢 Tesseract جاهز")
            else:
                st.error("🔴 Tesseract غير مثبّت")
        else:
            status_map = {
                "success": "🟢 جاهز",
                "loading": "🟡 قيد التحميل",
                "error": "🔴 خطأ",
                "غير معروف": "⚪ غير معروف",
            }
            st.info(
                f"**الحالة:** "
                f"{status_map.get(st.session_state.hf_api_status, '⚪')}"
            )

    with col3:
        lang = st.session_state.get("tess_language", "إنجليزي")
        st.info(f"**اللغة:** {lang}")


def render_result_card(page_num: int, text: str, confidence: float = None):
    """عرض بطاقة نتيجة واحدة"""
    with st.container():
        header = f"📄 الصفحة {page_num}"
        if confidence is not None:
            # لون حسب نسبة الثقة
            if confidence >= 80:
                header += f" — 🟢 الثقة: {confidence}%"
            elif confidence >= 50:
                header += f" — 🟡 الثقة: {confidence}%"
            else:
                header += f" — 🔴 الثقة: {confidence}%"

        st.markdown(f"**{header}**")

        if text:
            word_count = len(text.split())
            st.caption(f"📊 {word_count} كلمة  |  {len(text)} حرف")
            st.text_area(
                f"نص الصفحة {page_num}",
                text,
                height=150,
                key=f"result_text_{page_num}",
                label_visibility="collapsed",
            )
        else:
            st.warning("لم يتم العثور على نص في هذه الصفحة")

        st.markdown("---")


def render_export_section(results: list):
    """عرض قسم التصدير"""
    from utils.export import get_export_data
    from config import EXPORT_FORMATS

    if not results:
        return

    st.subheader("📥 تصدير النتائج")

    col1, col2 = st.columns([1, 2])

    with col1:
        export_format = st.selectbox(
            "صيغة التصدير",
            options=EXPORT_FORMATS,
            index=0,
            key="export_format_select",
        )

    with col2:
        data, filename, mime = get_export_data(results, export_format)

        st.download_button(
            label=f"📥 تحميل ({export_format})",
            data=data,
            file_name=filename,
            mime=mime,
            use_container_width=True,
            type="primary",
        )


def render_processing_stats(results: list):
    """عرض إحصائيات المعالجة"""
    if not results:
        return

    total_words = sum(
        len(r["text"].split()) for r in results if r.get("text")
    )
    total_chars = sum(len(r["text"]) for r in results if r.get("text"))
    avg_confidence = None

    confidences = [r["confidence"] for r in results if r.get("confidence")]
    if confidences:
        avg_confidence = round(sum(confidences) / len(confidences), 1)

    cols = st.columns(4 if avg_confidence else 3)

    with cols[0]:
        st.metric("📄 الصفحات", len(results))
    with cols[1]:
        st.metric("📝 الكلمات", f"{total_words:,}")
    with cols[2]:
        st.metric("🔤 الأحرف", f"{total_chars:,}")

    if avg_confidence and len(cols) > 3:
        with cols[3]:
            st.metric("🎯 متوسط الثقة", f"{avg_confidence}%")
