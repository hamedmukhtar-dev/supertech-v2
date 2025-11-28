# utils/i18n.py

translations = {
    "en": {
        "language_selector_title": "Choose your preferred language",
        "welcome_title": "Welcome",
        "pilot_signup": "Pilot Signup",
        "ai_reports": "AI Reports",
        "home": "Home",
        "loading": "Loading...",
        "continue": "Continue",
        "back": "Back",
    },
    "ar": {
        "language_selector_title": "اختر لغتك المفضلة",
        "welcome_title": "مرحباً",
        "pilot_signup": "الانضمام للبرنامج التجريبي",
        "ai_reports": "تقارير الذكاء الاصطناعي",
        "home": "الرئيسية",
        "loading": "جاري التحميل...",
        "continue": "استمرار",
        "back": "رجوع",
    }
}

def t(lang, key):
    return translations.get(lang, translations["en"]).get(key, key)