"""
معالجة ملفات PDF
PDF file handling and conversion
"""

from PIL import Image
import fitz  # PyMuPDF
import tempfile
import os
import io

from config import PDF_DPI_OPTIONS, DEFAULT_PDF_DPI
from utils.logger import get_logger

logger = get_logger(__name__)


class PDFHandler:
    """معالج ملفات PDF — تحويل الصفحات إلى صور عالية الجودة"""

    @staticmethod
    def get_page_count(pdf_file) -> int:
        """الحصول على عدد صفحات الملف"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_file.getvalue())
                tmp_path = tmp.name

            doc = fitz.open(tmp_path)
            count = len(doc)
            doc.close()
            os.unlink(tmp_path)
            return count
        except Exception as e:
            logger.error(f"Page count error: {e}")
            return 0

    @staticmethod
    def pdf_to_images(
        pdf_file,
        dpi_label: str = None,
        page_range: tuple = None,
    ) -> list:
        """
        تحويل PDF إلى قائمة من الصور عالية الجودة

        Args:
            pdf_file: ملف PDF (من Streamlit file_uploader)
            dpi_label: اسم دقة التحويل (من PDF_DPI_OPTIONS)
            page_range: نطاق الصفحات (start, end) — 0-indexed, inclusive

        Returns:
            قائمة من (page_number, PIL.Image) أو dict مع error
        """
        if dpi_label is None:
            dpi_label = DEFAULT_PDF_DPI

        scale = PDF_DPI_OPTIONS.get(dpi_label, 2.0)

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_file.getvalue())
                tmp_path = tmp.name

            doc = fitz.open(tmp_path)
            total_pages = len(doc)
            images = []

            # تحديد نطاق الصفحات
            if page_range:
                start = max(0, page_range[0])
                end = min(total_pages - 1, page_range[1])
            else:
                start = 0
                end = total_pages - 1

            logger.info(
                f"Converting PDF: pages {start+1}-{end+1} of {total_pages}, "
                f"scale={scale}"
            )

            for page_num in range(start, end + 1):
                page = doc.load_page(page_num)

                # تحويل بدقة عالية
                matrix = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=matrix, alpha=False)

                # تحويل إلى PIL Image
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))

                images.append((page_num + 1, img))
                logger.info(
                    f"Page {page_num + 1}: {img.size[0]}x{img.size[1]}px"
                )

            doc.close()
            os.unlink(tmp_path)

            logger.info(f"PDF conversion complete: {len(images)} pages")
            return images

        except Exception as e:
            logger.error(f"PDF conversion error: {e}")
            return {"error": f"خطأ في تحويل PDF: {str(e)}"}

    @staticmethod
    def get_pdf_info(pdf_file) -> dict:
        """الحصول على معلومات تفصيلية عن ملف PDF"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_file.getvalue())
                tmp_path = tmp.name

            doc = fitz.open(tmp_path)
            info = {
                "page_count": len(doc),
                "metadata": doc.metadata,
                "pages_info": [],
            }

            for i in range(len(doc)):
                page = doc.load_page(i)
                rect = page.rect
                info["pages_info"].append(
                    {
                        "page": i + 1,
                        "width": round(rect.width),
                        "height": round(rect.height),
                    }
                )

            doc.close()
            os.unlink(tmp_path)
            return info

        except Exception as e:
            logger.error(f"PDF info error: {e}")
            return {"error": str(e)}
