"""
معالجة الصور المتقدمة لتحسين دقة OCR
Advanced Image Processing for OCR quality improvement
"""

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io

from utils.logger import get_logger

logger = get_logger(__name__)


class ImageProcessor:
    """معالج الصور — تحسينات متقدمة لأفضل نتائج OCR"""

    @staticmethod
    def enhance_image(
        image: Image.Image,
        contrast: float = 1.3,
        brightness: float = 1.05,
        sharpness: float = 1.5,
    ) -> Image.Image:
        """
        تحسين جودة الصورة للحصول على أفضل نتائج OCR

        Args:
            image: الصورة الأصلية
            contrast: معامل التباين (1.0 = بدون تغيير)
            brightness: معامل السطوع (1.0 = بدون تغيير)
            sharpness: معامل الحدة (1.0 = بدون تغيير)

        Returns:
            الصورة المحسّنة
        """
        try:
            # 1. تحسين التباين
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(contrast)

            # 2. تحسين السطوع
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(brightness)

            # 3. تحسين الحدة
            if sharpness != 1.0:
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(sharpness)

            logger.info(
                f"Image enhanced: contrast={contrast}, "
                f"brightness={brightness}, sharpness={sharpness}"
            )
            return image

        except Exception as e:
            logger.error(f"Enhancement error: {e}")
            return image

    @staticmethod
    def auto_enhance(image: Image.Image) -> Image.Image:
        """
        تحسين تلقائي للصورة — يعمل على تحسين التباين والإضاءة تلقائياً
        """
        try:
            # تحسين تلقائي للتباين
            image = ImageOps.autocontrast(image, cutoff=1)
            logger.info("Auto-enhancement applied")
            return image
        except Exception as e:
            logger.error(f"Auto-enhance error: {e}")
            return image

    @staticmethod
    def prepare_for_tesseract(
        image: Image.Image,
        grayscale: bool = True,
        denoise: bool = True,
        binarize: bool = False,
        binarize_threshold: int = 128,
    ) -> Image.Image:
        """
        تحضير الصورة خصيصاً لـ Tesseract OCR

        Tesseract يعمل أفضل مع صور:
        - رمادية (Grayscale) أو ثنائية (Binary)
        - عالية التباين
        - خالية من الضوضاء

        Args:
            image: الصورة الأصلية
            grayscale: تحويل للرمادي
            denoise: إزالة الضوضاء
            binarize: تحويل لأبيض وأسود (Binary)
            binarize_threshold: عتبة التحويل الثنائي

        Returns:
            الصورة المحضّرة
        """
        try:
            # 1. تحويل للرمادي (Tesseract يفضل هذا)
            if grayscale and image.mode not in ("L", "1"):
                image = image.convert("L")

            # 2. إزالة الضوضاء باستخدام فلتر Median
            if denoise:
                image = image.filter(ImageFilter.MedianFilter(size=3))

            # 3. تحسين تلقائي للتباين
            image = ImageOps.autocontrast(image, cutoff=2)

            # 4. تحويل ثنائي (Binary) إذا مطلوب
            if binarize:
                image = image.point(
                    lambda x: 255 if x > binarize_threshold else 0, mode="1"
                )

            logger.info(
                f"Prepared for Tesseract: grayscale={grayscale}, "
                f"denoise={denoise}, binarize={binarize}"
            )
            return image

        except Exception as e:
            logger.error(f"Tesseract prep error: {e}")
            return image

    @staticmethod
    def smart_resize(
        image: Image.Image,
        max_dimension: int = 4096,
        min_dimension: int = 384,
        upscale_small: bool = True,
    ) -> Image.Image:
        """
        تغيير حجم الصورة بذكاء مع الحفاظ على النسبة

        Args:
            image: الصورة الأصلية
            max_dimension: الحد الأقصى للبُعد
            min_dimension: الحد الأدنى للبُعد
            upscale_small: تكبير الصور الصغيرة

        Returns:
            الصورة بالحجم المناسب
        """
        width, height = image.size

        # تصغير الصور الكبيرة جداً
        if width > max_dimension or height > max_dimension:
            ratio = min(max_dimension / width, max_dimension / height)
            new_size = (int(width * ratio), int(height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Downscaled: {width}x{height} → {new_size[0]}x{new_size[1]}")

        # تكبير الصور الصغيرة (لتحسين دقة Tesseract)
        elif upscale_small and (width < min_dimension or height < min_dimension):
            ratio = max(min_dimension / width, min_dimension / height)
            # لا نكبّر أكثر من 3x
            ratio = min(ratio, 3.0)
            new_size = (int(width * ratio), int(height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Upscaled: {width}x{height} → {new_size[0]}x{new_size[1]}")

        return image

    @classmethod
    def full_pipeline(
        cls,
        image: Image.Image,
        contrast: float = 1.3,
        brightness: float = 1.05,
        sharpness: float = 1.5,
        grayscale: bool = True,
        denoise: bool = True,
        binarize: bool = False,
        max_dimension: int = 4096,
    ) -> Image.Image:
        """
        خط معالجة كامل — يطبّق كل التحسينات بالترتيب الأمثل

        ترتيب المعالجة:
        1. تغيير الحجم
        2. تحسين الجودة (تباين، سطوع، حدة)
        3. تحضير لـ Tesseract (رمادي، إزالة ضوضاء)
        """
        # 1. تغيير الحجم أولاً
        image = cls.smart_resize(image, max_dimension=max_dimension)

        # 2. تحسين الجودة (على الصورة الملونة قبل التحويل للرمادي)
        image = cls.enhance_image(
            image, contrast=contrast, brightness=brightness, sharpness=sharpness
        )

        # 3. تحضير لـ Tesseract
        image = cls.prepare_for_tesseract(
            image, grayscale=grayscale, denoise=denoise, binarize=binarize
        )

        return image

    @staticmethod
    def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
        """تحويل الصورة إلى bytes"""
        buffer = io.BytesIO()
        # إذا كانت الصورة باللون الرمادي أو ثنائية، حوّل لـ RGB لحفظ كـ JPEG
        if format.upper() == "JPEG" and image.mode in ("L", "1", "RGBA", "P"):
            image = image.convert("RGB")
        image.save(buffer, format=format)
        return buffer.getvalue()
