"""
Configuration for the Skin Problem Detection Agent
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Roboflow Configuration
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
ROBOFLOW_WORKSPACE = "bebooo"
ROBOFLOW_PROJECT = "skin-problem-detection-relabel-clean3-smqda"
ROBOFLOW_MODEL_VERSION = 1
ROBOFLOW_API_URL = "https://detect.roboflow.com"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EXTERNAL_WEBHOOK_URL = "https://webhook.site/2d1f686c-eefa-43af-9a2b-12549c922aeb"

# Model ID for inference SDK
MODEL_ID = f"{ROBOFLOW_PROJECT}/{ROBOFLOW_MODEL_VERSION}"

# Detection Settings
CONFIDENCE_THRESHOLD = 27  # Minimum confidence percentage
OVERLAP_THRESHOLD = 30     # NMS overlap threshold percentage

# Skin condition classes and their metadata
SKIN_CONDITIONS = {
    "Acne": {
        "name_ar": "حب الشباب",
        "color": "#FF4D4D",
        "icon": "🔴",
        "severity": "متوسط",
        "description": "حالة جلدية التهابية تسبب البثور والعيوب في البشرة.",
        "tips": [
            "حافظي على نظافة وجهك باستخدام منظف لطيف",
            "تجنبي لمس وجهك بكثرة",
            "استخدمي مرطبات لا تسد المسام",
            "فكري في استخدام علاجات حمض الساليسيليك أو بيروكسيد البنزويل"
        ]
    },
    "Blackheads": {
        "name_ar": "رؤوس سوداء",
        "color": "#4A4A4A",
        "icon": "⚫",
        "severity": "خفيف",
        "description": "رؤوس سوداء مفتوحة ناتجة عن انسداد بصيلات الشعر.",
        "tips": [
            "استخدمي منتجات تحتوي على حمض الساليسيليك",
            "جربي ماسكات الطين أسبوعياً",
            "لا تقومي بالضغط عليها أو عصرها",
            "قشري بشرتك بانتظام باستخدام أحماض BHA"
        ]
    },
    "Dark-Spots": {
        "name_ar": "بقع داكنة",
        "color": "#8B6914",
        "icon": "🟤",
        "severity": "خفيف",
        "description": "مناطق تصبغ داكنة ناتجة عن أضرار أشعة الشمس أو علامات ما بعد الالتهاب.",
        "tips": [
            "استخدمي واقي الشمس يومياً (SPF 30+)",
            "استخدمي سيروم فيتامين سي في الصباح",
            "جربي المنتجات التي تحتوي على النياسيناميد",
            "فكري في استخدام الريتينول للروتين المسائي"
        ]
    },
    "Dry-Skin": {
        "name_ar": "بشرة جافة",
        "color": "#D2B48C",
        "icon": "🏜️",
        "severity": "خفيف",
        "description": "بشرة تفتقر للترطيب، تبدو متقشرة أو خشنة.",
        "tips": [
            "استخدمي مرطب غني وعميق",
            "ضعي سيروم حمض الهيالورونيك على بشرة رطبة",
            "تجنبي الاستحمام بالماء الساخن والمنظفات القاسية",
            "استخدمي جهاز ترطيب الجو في البيئات الجافة"
        ]
    },
    "Englarged-Pores": {
        "name_ar": "مسام واسعة",
        "color": "#FF8C00",
        "icon": "🔵",
        "severity": "خفيف",
        "description": "المسام الواسعة وتظهر بشكل خاص على الأنف والخدين.",
        "tips": [
            "استخدمي النياسيناميد لتقليل مظهر المسام",
            "استخدمي التونر القابض للمسام",
            "جربي الريتينول لتحسين ملمس البشرة",
            "حافظي على نظافة البشرة لمنع انسداد المسام"
        ]
    },
    "Eyebags": {
        "name_ar": "هالات سوداء",
        "color": "#9370DB",
        "icon": "👁️",
        "severity": "خفيف",
        "description": "انتفاخ أو تورم تحت العينين (الهالات والأكياس).",
        "tips": [
            "احصلي على قسط كافٍ من النوم (7-9 ساعات)",
            "استخدمي كمادات باردة",
            "استخدمي كريمات العين التي تحتوي على الكافيين",
            "حافظي على رطوبة جسمك وقللي من تناول الملح"
        ]
    },
    "Oily-Skin": {
        "name_ar": "بشرة دهنية",
        "color": "#FFD700",
        "icon": "✨",
        "severity": "خفيف",
        "description": "زيادة في الإفرازات الدهنية مما يسبب مظهر لامع للبشرة.",
        "tips": [
            "استخدمي منظف رغوي لطيف",
            "ضعي مرطب خالي من الزيوت",
            "استخدمي ورق امتصاص الزيوت خلال اليوم",
            "جربي المنتجات التي تحتوي على النياسيناميد"
        ]
    },
    "Skin-Redness": {
        "name_ar": "احمرار البشرة",
        "color": "#DC143C",
        "icon": "🔺",
        "severity": "متوسط",
        "description": "التهاب أو تهيج يسبب بقع حمراء على البشرة.",
        "tips": [
            "استخدمي منتجات لطيفة وخالية من العطور",
            "استخدمي الألوفيرا أو السيكا (سنتيلا أسياتيكا) المهدئة",
            "تجنبي المهيجات مثل الأطعمة الحارة والكحول",
            "فكري في حمض الأزيلايك للاحمرار المستمر"
        ]
    },
    "Whiteheads": {
        "name_ar": "رؤوس بيضاء",
        "color": "#F5F5DC",
        "icon": "⚪",
        "severity": "خفيف",
        "description": "رؤوس بيضاء مغلقة محتبسة تحت سطح البشرة.",
        "tips": [
            "استخدمي المنتجات التي تحتوي على مشتقات فيتامين أ (الريتينويد)",
            "ضعي علاج موضعي بـ بيروكسيد البنزويل",
            "حافظي على تقشير بشرتك بانتظام",
            "تجنبي المنتجات الثقيلة التي تسد المسام"
        ]
    },
    "Wrinkles": {
        "name_ar": "تجاعيد",
        "color": "#BC8F8F",
        "icon": "〰️",
        "severity": "خفيف",
        "description": "خطوط دقيقة وتجاعيد تشكلت بسبب التقدم في العمر أو التعرض للشمس.",
        "tips": [
            "استخدمي الريتينول بانتظام ليلاً",
            "استخدمي واقي الشمس يومياً لمنع المزيد من التلف",
            "حافظي على الترطيب واستخدمي سيروم الببتيدات",
            "فكري في المنتجات التي تحتوي على حمض الهيالورونيك"
        ]
    }
}

# Flask Settings
UPLOAD_FOLDER = "uploads"
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp"}
