from setuptools import setup, find_packages

setup(
    name="ocr-streamlit-app",
    version="2.0.0",
    description="نظام استخراج النص من الصور وPDF — Tesseract OCR + HF Inference API",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "requests>=2.31.0",
        "Pillow>=10.0.0",
        "pymupdf>=1.23.0",
        "pytesseract>=0.3.10",
    ],
    python_requires=">=3.8",
)