import requests

def detect_language_from_ip():
    try:
        ip_data = requests.get("https://ipapi.co/json/").json()
        country = ip_data.get("country_code", "US")

        arabic_countries = ["EG", "SA", "SD", "QA", "AE", "KW", "OM", "BH", "LY", "JO", "DZ", "MA", "TN", "YE"]

        if country in arabic_countries:
            return "ar"
        else:
            return "en"
    except:
        return "en"