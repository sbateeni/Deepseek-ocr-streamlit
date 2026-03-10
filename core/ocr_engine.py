"""
محرك OCR — يدعم Tesseract (محلي) و HF Inference API (سحابي)
OCR Engine — Supports Tesseract (local) & HF Inference API (cloud)
"""

import pytesseract
from PIL import Image
import requests
import time
import io

from config import (
    HF_BASE_URL,
    HF_STATUS_URL,
    HF_OCR_MODELS,
    API_TIMEOUT,
    API_MAX_RETRIES,
    API_RETRY_BASE_DELAY,
)
from utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# Tesseract OCR (محلي — لا يحتاج إنترنت ولا API Key)
# ═══════════════════════════════════════════════════════════════

class TesseractOCR:
    """محرك Tesseract OCR — مجاني، محلي، يدعم العربية"""

    @staticmethod
    def extract_text(
        image: Image.Image,
        lang: str = "eng",
        psm: int = 3,
        extra_config: str = "",
    ) -> dict:
        """
        استخراج النص من صورة باستخدام Tesseract
        """
        # إضافة إعدادات الحفاظ على المسافات للجداول
        hifi_config = "-c preserve_interword_spaces=1"
        config = f"--psm {psm} --oem 3 {hifi_config} {extra_config}".strip()

        try:
            text = pytesseract.image_to_string(image, lang=lang, config=config)
            text = text.strip()

            logger.info(
                f"Tesseract: extracted {len(text)} chars, "
                f"lang={lang}, psm={psm}"
            )

            return {
                "text": text,
                "engine": "Tesseract",
                "language": lang,
                "char_count": len(text),
                "word_count": len(text.split()) if text else 0,
            }

        except Exception as e:
            logger.error(f"Tesseract extraction error: {e}")
            return {"error": f"خطأ في Tesseract: {str(e)}"}

    @staticmethod
    def extract_with_confidence(
        image: Image.Image,
        lang: str = "eng",
        psm: int = 3,
    ) -> dict:
        """
        استخراج النص مع نسبة الثقة لكل كلمة

        Returns:
            dict يحتوي على: text, words, avg_confidence, word_count
        """
        config = f"--psm {psm} --oem 3"

        try:
            data = pytesseract.image_to_data(
                image,
                lang=lang,
                config=config,
                output_type=pytesseract.Output.DICT,
            )

            words = []
            total_conf = 0
            word_count = 0

            for i in range(len(data["text"])):
                word = data["text"][i].strip()
                conf = int(data["conf"][i])

                if word and conf > 0:
                    words.append(
                        {
                            "text": word,
                            "confidence": conf,
                            "x": data["left"][i],
                            "y": data["top"][i],
                            "w": data["width"][i],
                            "h": data["height"][i],
                            "block": data["block_num"][i],
                            "line": data["line_num"][i],
                        }
                    )
                    total_conf += conf
                    word_count += 1

            # بناء النص الكامل مع احترام الأسطر
            lines = {}
            for w in words:
                key = (w["block"], w["line"])
                if key not in lines:
                    lines[key] = []
                lines[key].append(w["text"])

            full_text = "\n".join(
                " ".join(line_words)
                for line_words in lines.values()
            )

            avg_confidence = round(total_conf / word_count, 1) if word_count > 0 else 0

            logger.info(
                f"Tesseract detailed: {word_count} words, "
                f"avg_confidence={avg_confidence}%"
            )

            return {
                "text": full_text,
                "words": words,
                "avg_confidence": avg_confidence,
                "word_count": word_count,
                "engine": "Tesseract",
            }

        except Exception as e:
            logger.error(f"Tesseract detailed error: {e}")
            return {"error": f"خطأ في Tesseract: {str(e)}"}

    @staticmethod
    def is_available() -> bool:
        """فحص ما إذا كان Tesseract مثبّتاً"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    @staticmethod
    def get_available_languages() -> list:
        """الحصول على اللغات المثبتة"""
        try:
            return pytesseract.get_languages()
        except Exception:
            return []


# ═══════════════════════════════════════════════════════════════
# HF Inference API (سحابي — يحتاج Token)
# ═══════════════════════════════════════════════════════════════

class HFInferenceOCR:
    """محرك HF Inference API — للنماذج السحابية المتقدمة"""

    @staticmethod
    def get_api_url(model_name: str) -> str:
        """الحصول على عنوان API للنموذج"""
        model_info = HF_OCR_MODELS.get(model_name)
        if not model_info:
            return None
        return f"{HF_BASE_URL}models/{model_info['model_id']}"

    @staticmethod
    def get_status_url(model_name: str) -> str:
        """الحصول على عنوان حالة النموذج"""
        model_info = HF_OCR_MODELS.get(model_name)
        if not model_info:
            return None
        return f"{HF_STATUS_URL}{model_info['model_id']}"

    @staticmethod
    def check_model_status(model_name: str, token: str) -> dict:
        """فحص حالة النموذج"""
        if not token:
            return {"error": "⚠️ يرجى إدخال HF Token أولاً"}

        status_url = HFInferenceOCR.get_status_url(model_name)
        if not status_url:
            return {"error": "❌ النموذج غير موجود"}

        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = requests.get(status_url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                loaded = data.get("loaded", False)
                state = data.get("state", "Unknown")
                return {
                    "status": "success" if loaded else "loading",
                    "message": "✅ جاهز" if loaded else "🔄 قيد التحميل",
                    "ready": loaded,
                    "state": state,
                }
            elif response.status_code == 404:
                return {"status": "error", "message": "❌ النموذج غير متاح", "ready": False}
            else:
                return {
                    "status": "error",
                    "message": f"❌ خطأ: {response.status_code}",
                    "ready": False,
                }

        except requests.exceptions.Timeout:
            return {"status": "error", "message": "⏰ انتهت مهلة الاتصال", "ready": False}
        except Exception as e:
            return {"status": "error", "message": f"❌ خطأ: {str(e)}", "ready": False}

    @staticmethod
    def force_load_model(model_name: str, token: str) -> dict:
        """إجبار تحميل النموذج"""
        if not token:
            return {"status": "error", "message": "⚠️ يرجى إدخال Token"}

        api_url = HFInferenceOCR.get_api_url(model_name)
        if not api_url:
            return {"status": "error", "message": "❌ النموذج غير موجود"}

        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = requests.post(
                api_url, headers=headers, json={"inputs": "test"}, timeout=60
            )
            if response.status_code == 200:
                return {"status": "success", "message": "✅ تم تحميل النموذج"}
            elif response.status_code in [503, 422]:
                return {"status": "loading", "message": "🔄 قيد التحميل، انتظر 30 ثانية"}
            else:
                return {"status": "error", "message": f"❌ فشل: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"❌ خطأ: {str(e)}"}

    @staticmethod
    def extract_text(
        image_bytes: bytes,
        model_name: str,
        token: str,
    ) -> dict:
        """
        استخراج النص عبر HF Inference API مع Retry

        يرسل الصورة كـ binary data (الطريقة الصحيحة لـ HF API)
        """
        if not token:
            return {"error": "⚠️ يرجى إدخال HF Token"}

        api_url = HFInferenceOCR.get_api_url(model_name)
        if not api_url:
            return {"error": "❌ النموذج غير موجود"}

        headers = {"Authorization": f"Bearer {token}"}

        last_error = None

        for attempt in range(1, API_MAX_RETRIES + 1):
            try:
                logger.info(
                    f"HF API attempt {attempt}/{API_MAX_RETRIES}: {model_name}"
                )

                # إرسال الصورة كـ binary data (الطريقة الصحيحة)
                response = requests.post(
                    api_url,
                    headers=headers,
                    data=image_bytes,
                    timeout=API_TIMEOUT,
                )

                if response.status_code == 200:
                    result = response.json()

                    # استخراج النص من أشكال الاستجابة المختلفة
                    text = ""
                    if isinstance(result, list) and len(result) > 0:
                        text = result[0].get("generated_text", "")
                    elif isinstance(result, dict):
                        text = result.get("text", result.get("generated_text", ""))

                    return {
                        "text": text.strip() if text else "",
                        "engine": f"HF API ({model_name})",
                        "raw_response": result,
                    }

                elif response.status_code == 503:
                    last_error = "النموذج قيد التحميل"
                    logger.warning(f"Model loading (503), attempt {attempt}")
                elif response.status_code == 429:
                    last_error = "تم تجاوز الحد المسموح"
                    logger.warning(f"Rate limited (429), attempt {attempt}")
                elif response.status_code == 401:
                    return {"error": "❌ Token غير صالح"}
                elif response.status_code == 404:
                    return {"error": "❌ النموذج غير متاح"}
                else:
                    last_error = f"خطأ {response.status_code}: {response.text[:200]}"

            except requests.exceptions.Timeout:
                last_error = "انتهت مهلة الطلب"
                logger.warning(f"Timeout on attempt {attempt}")
            except Exception as e:
                last_error = str(e)
                logger.error(f"Error on attempt {attempt}: {e}")

            # انتظار قبل المحاولة التالية (Exponential Backoff)
            if attempt < API_MAX_RETRIES:
                delay = API_RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.info(f"Waiting {delay}s before retry...")
                time.sleep(delay)

        return {"error": f"❌ فشل بعد {API_MAX_RETRIES} محاولات: {last_error}"}
