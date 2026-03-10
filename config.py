"""
إعدادات التطبيق والثوابت
Application Settings & Constants
"""

# ═══════════════════════════════════════════════════════════
# لغات Tesseract OCR
# ═══════════════════════════════════════════════════════════
TESSERACT_LANGUAGES = {
    "إنجليزي": "eng",
    "عربي": "ara",
    "عربي + إنجليزي": "ara+eng",
    "عبري": "heb",
    "عبري + إنجليزي": "heb+eng",
    "فرنسي": "fra",
    "إسباني": "spa",
    "ألماني": "deu",
}

# أوضاع تقسيم الصفحة (Page Segmentation Modes)
TESSERACT_PSM_MODES = {
    "تلقائي كامل (مُوصى)": 3,
    "عمود نص واحد": 4,
    "كتلة نص عمودية موحّدة": 6,
    "سطر واحد فقط": 7,
    "كلمة واحدة فقط": 8,
}

# ═══════════════════════════════════════════════════════════
# نماذج HF API (اختياري — يحتاج Token)
# ═══════════════════════════════════════════════════════════
HF_OCR_MODELS = {
    "TrOCR Large Printed": {
        "model_id": "microsoft/trocr-large-printed",
        "description": "🔤 دقة عالية — نصوص مطبوعة (إنجليزي)",
    },
    "TrOCR Large Handwritten": {
        "model_id": "microsoft/trocr-large-handwritten",
        "description": "✍️ دقة عالية — خط يد (إنجليزي)",
    },
    "TrOCR Base Printed": {
        "model_id": "microsoft/trocr-base-printed",
        "description": "⚡ سريع — نصوص مطبوعة (إنجليزي)",
    },
    "TrOCR Base Handwritten": {
        "model_id": "microsoft/trocr-base-handwritten",
        "description": "⚡ سريع — خط يد (إنجليزي)",
    },
    "Donut (وثائق منظمة)": {
        "model_id": "naver-clova-ix/donut-base-finetuned-cord-v2",
        "description": "📋 وثائق منظمة وإيصالات",
    },
}

HF_BASE_URL = "https://router.huggingface.co/hf-inference/"
HF_STATUS_URL = "https://router.huggingface.co/hf-inference/status/"

# ═══════════════════════════════════════════════════════════
# إعدادات API
# ═══════════════════════════════════════════════════════════
API_TIMEOUT = 120
API_MAX_RETRIES = 3
API_RETRY_BASE_DELAY = 2

# ═══════════════════════════════════════════════════════════
# إعدادات معالجة الصور
# ═══════════════════════════════════════════════════════════
IMAGE_MAX_DIMENSION = 4096
IMAGE_MIN_DIMENSION = 384

ENHANCEMENT_DEFAULTS = {
    "contrast": 1.3,
    "brightness": 1.05,
    "sharpness": 1.5,
}

# ═══════════════════════════════════════════════════════════
# إعدادات PDF
# ═══════════════════════════════════════════════════════════
PDF_DPI_OPTIONS = {
    "عادي (150 DPI)": 1.5,
    "جيد (200 DPI)": 2.0,
    "عالي (250 DPI)": 2.5,
    "عالي جداً (300 DPI)": 3.0,
}
DEFAULT_PDF_DPI = "جيد (200 DPI)"

# ═══════════════════════════════════════════════════════════
# الملفات المدعومة والتصدير
# ═══════════════════════════════════════════════════════════
SUPPORTED_IMAGE_TYPES = ["jpg", "jpeg", "png", "bmp", "tiff", "webp"]
SUPPORTED_FILE_TYPES = SUPPORTED_IMAGE_TYPES + ["pdf"]
EXPORT_FORMATS = ["TXT", "JSON", "CSV"]
