# 🔍 OCR System — استخراج النص من الصور و PDF

نظام استخراج نصوص متكامل مبني بـ **Streamlit** مع دعم **Tesseract OCR** (محلي) و **HF Inference API** (سحابي).

## ✨ الميزات

- 🖥️ **Tesseract OCR** — مجاني، محلي، يدعم العربية والإنجليزية
- ☁️ **HF Inference API** — نماذج سحابية متقدمة (اختياري)
- 📄 **دعم PDF** — تحويل ومعالجة صفحات PDF بدقة عالية
- 🖼️ **معالجة صور متقدمة** — تباين، سطوع، حدة، إزالة ضوضاء
- 🚀 **معالجة دفعية** — استخراج النص من جميع صفحات PDF دفعة واحدة
- 📊 **نسبة الثقة** — تقييم دقة كل كلمة مستخرجة
- 📥 **تصدير متعدد** — TXT, JSON, CSV

## 🚀 تشغيل محلي

```bash
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Streamlit Cloud

1. ارفع المشروع على GitHub
2. اربطه بـ [Streamlit Cloud](https://share.streamlit.io)
3. ملف `packages.txt` سيثبّت Tesseract تلقائياً
4. حدد `app.py` كنقطة الدخول

## 📁 هيكل المشروع

```
├── app.py                # نقطة الدخول
├── config.py             # الإعدادات
├── packages.txt          # حزم النظام (Streamlit Cloud)
├── requirements.txt      # متطلبات Python
│
├── core/                 # المنطق الأساسي
│   ├── ocr_engine.py     # محرك Tesseract + HF API
│   ├── image_processor.py # معالجة الصور
│   └── pdf_handler.py    # معالجة PDF
│
├── ui/                   # واجهة المستخدم
│   ├── sidebar.py        # الشريط الجانبي
│   ├── main_page.py      # الصفحة الرئيسية
│   └── components.py     # مكونات مشتركة
│
└── utils/                # أدوات مساعدة
    ├── session.py        # إدارة الجلسة
    ├── export.py         # التصدير
    └── logger.py         # التسجيل
```