from setuptools import setup, find_packages

setup(
    name="deepseek-ocr-app",
    version="1.0.0",
    description="تطبيق استخراج النص من الصور وPDF باستخدام DeepSeek OCR",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "requests>=2.31.0",
        "Pillow>=10.0.0",
        "pymupdf>=1.23.0",
    ],
    python_requires=">=3.8",
)