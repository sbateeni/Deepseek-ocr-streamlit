"""
تصدير النتائج بصيغ متعددة
Export results in multiple formats
"""

import json
import csv
import io

from utils.logger import get_logger

logger = get_logger(__name__)


def export_as_txt(results: list) -> str:
    """تصدير النتائج كنص عادي"""
    parts = []
    for r in results:
        if len(results) > 1:
            header = f"═══ الصفحة {r['page']} ═══"
            if r.get("confidence"):
                header += f"  (الثقة: {r['confidence']}%)"
            parts.append(header)
        parts.append(r["text"])
        parts.append("")  # سطر فارغ

    return "\n".join(parts).strip()


def export_as_json(results: list) -> str:
    """تصدير النتائج كـ JSON"""
    export_data = {
        "total_pages": len(results),
        "pages": [],
    }

    for r in results:
        page_data = {
            "page_number": r["page"],
            "text": r["text"],
            "word_count": len(r["text"].split()) if r["text"] else 0,
            "char_count": len(r["text"]) if r["text"] else 0,
        }
        if r.get("confidence"):
            page_data["confidence"] = r["confidence"]
        if r.get("engine"):
            page_data["engine"] = r["engine"]

        export_data["pages"].append(page_data)

    return json.dumps(export_data, ensure_ascii=False, indent=2)


def export_as_csv(results: list) -> str:
    """تصدير النتائج كـ CSV"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["الصفحة", "النص", "عدد الكلمات", "الثقة", "المحرك"])

    for r in results:
        writer.writerow(
            [
                r["page"],
                r["text"],
                len(r["text"].split()) if r["text"] else 0,
                r.get("confidence", ""),
                r.get("engine", ""),
            ]
        )

    return output.getvalue()


def get_export_data(results: list, format: str) -> tuple:
    """
    الحصول على بيانات التصدير بالصيغة المطلوبة

    Returns:
        tuple: (data, filename, mime_type)
    """
    exporters = {
        "TXT": (export_as_txt, "extracted_text.txt", "text/plain"),
        "JSON": (export_as_json, "extracted_text.json", "application/json"),
        "CSV": (export_as_csv, "extracted_text.csv", "text/csv"),
    }

    if format not in exporters:
        format = "TXT"

    func, filename, mime = exporters[format]
    data = func(results)
    logger.info(f"Exported as {format}: {len(data)} bytes")

    return data, filename, mime
