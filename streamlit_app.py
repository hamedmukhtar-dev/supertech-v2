# ============================================================
# HUMAIN Lifestyle — Live Presentation Demo
# Your Gateway to KSA 🇸🇦
# ============================================================

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from typing import Dict, Any, List, Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from layout_header import render_header  # الهيدر الأخضر

# ----------------------------
# تهيئة البيئة
# ----------------------------
load_dotenv()

DB_PATH = "humain_lifestyle.db"

# متغيرات الدخول من الـ Environment (للعرض الحي)
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

DEMO_USER = os.getenv("DEMO_USER", "demo")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo123")

PARTNER_USER = os.getenv("PARTNER_USER", "partner")
PARTNER_PASSWORD = os.getenv("PARTNER_PASSWORD", "partner123")

USERS = {
    ADMIN_USER: {"password": ADMIN_PASSWORD, "role": "admin"},
    DEMO_USER: {"password": DEMO_PASSWORD, "role": "demo"},
    PARTNER_USER: {"password": PARTNER_PASSWORD, "role": "partner"},
}

# ----------------------------
# إعداد صفحة Streamlit
# ----------------------------
st.set_page_config(
    page_title="HUMAIN Lifestyle — Gateway to KSA",
    page_icon="🌍",
    layout="wide",
)


# ==============================
# 1) الاتصال بقاعدة البيانات
# ==============================

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()

        # الفنادق
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS hotels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT,
                country TEXT,
                contact_name TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                has_api INTEGER DEFAULT 0,
                notes TEXT
            );
            """
        )

        # العقود
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_id INTEGER NOT NULL,
                contract_name TEXT NOT NULL,
                contract_type TEXT,
                currency TEXT,
                valid_from TEXT,
                valid_to TEXT,
                payment_terms TEXT,
                cancellation_policy TEXT,
                notes TEXT,
                FOREIGN KEY (hotel_id) REFERENCES hotels(id)
            );
            """
        )

        # الأنشطة/التجارب
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT,
                description TEXT,
                approx_price_usd REAL,
                provider TEXT,
                booking_link TEXT
            );
            """
        )

        # خطط الرحلات
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS itineraries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                traveller_name TEXT,
                traveller_email TEXT,
                traveller_phone TEXT,
                from_city TEXT,
                destination_city TEXT,
                destination_country TEXT,
                days INTEGER,
                budget REAL,
                month TEXT,
                interests TEXT,
                plan_text TEXT
            );
            """
        )

        # البرامج / Packages
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                name TEXT NOT NULL,
                city TEXT,
                days INTEGER,
                budget REAL,
                base_hotel_id INTEGER,
                activities_ids TEXT,
                ai_plan_text TEXT,
                target_segment TEXT,
                price_from_usd REAL,
                status TEXT,
                notes TEXT,
                source_itinerary_id INTEGER,
                FOREIGN KEY (base_hotel_id) REFERENCES hotels(id),
                FOREIGN KEY (source_itinerary_id) REFERENCES itineraries(id)
            );
            """
        )

        # طلبات الحجز / Leads
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS booking_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                traveller_name TEXT,
                traveller_email TEXT,
                traveller_phone TEXT,
                from_city TEXT,
                to_city TEXT,
                days INTEGER,
                budget REAL,
                notes TEXT,
                status TEXT,
                source TEXT,
                package_id INTEGER,
                itinerary_id INTEGER,
                FOREIGN KEY (package_id) REFERENCES packages(id),
                FOREIGN KEY (itinerary_id) REFERENCES itineraries(id)
            );
            """
        )

        conn.commit()

        # لو ما في أنشطة، نضيف كتالوج أولي
        cur.execute("SELECT COUNT(*) FROM activities;")
        count = cur.fetchone()[0]
        if count == 0:
            seed_activities = [
                # Riyadh
                (
                    "Riyadh",
                    "Boulevard City Evening",
                    "Entertainment",
                    "زيارة بوليفارد سيتي مع مطاعم وعروض حية وتجارب ترفيهية مناسبة للعائلات والشباب.",
                    150.0,
                    "Riyadh Season Partner",
                    "https://example.com/riyadh-boulevard-city",
                ),
                (
                    "Riyadh",
                    "Boulevard World Discovery",
                    "Entertainment",
                    "تجربة عوالم وثقافات مختلفة في منطقة ترفيهية ضخمة مع فعاليات وعروض موسمية.",
                    180.0,
                    "Riyadh Season Partner",
                    "https://example.com/riyadh-boulevard-world",
                ),
                (
                    "Riyadh",
                    "Riyadh Desert Safari & Dunes",
                    "Adventure",
                    "رحلة سفاري في صحراء الرياض مع رمال، دبابات، وجلسة بدوية مع عشاء تقليدي.",
                    220.0,
                    "Desert Operator",
                    "https://example.com/riyadh-dunes",
                ),
                (
                    "Riyadh",
                    "Riyadh Zoo Family Day",
                    "Family",
                    "يوم عائلي في حديقة الحيوانات مع أنشطة للأطفال ومناطق ألعاب ومطاعم.",
                    90.0,
                    "Family Operator",
                    "https://example.com/riyadh-zoo",
                ),
                (
                    "Riyadh",
                    "CityWalk Riyadh Night",
                    "Leisure",
                    "جولة مسائية في CityWalk مع مطاعم وكافيهات وفعاليات موسمية مميزة.",
                    110.0,
                    "CityWalk Partner",
                    "https://example.com/riyadh-citywalk",
                ),

                # Jeddah
                (
                    "Jeddah",
                    "Jeddah Waterfront Evening Walk",
                    "Leisure",
                    "نزهة مسائية على واجهة جدة البحرية مع مطاعم بحرية وجلسات خارجية.",
                    80.0,
                    "Local Guide",
                    "https://example.com/jeddah-waterfront",
                ),
                (
                    "Jeddah",
                    "Red Sea Boat Trip",
                    "Adventure",
                    "رحلة قارب في البحر الأحمر مع سباحة أو سنوركلينج وجلسة بحرية.",
                    260.0,
                    "Red Sea Operator",
                    "https://example.com/jeddah-redsea-boat",
                ),
                (
                    "Jeddah",
                    "Historic Jeddah (Al Balad) Tour",
                    "Culture",
                    "جولة في جدة التاريخية مع زيارة البيوت القديمة والأسواق الشعبية.",
                    130.0,
                    "Heritage Guide",
                    "https://example.com/jeddah-albalad",
                ),

                # Makkah
                (
                    "Makkah",
                    "Umrah Program & City Tour",
                    "Religious",
                    "برنامج عمرة كامل مع نقل وإرشاد وزيارة لبعض المعالم في مكة المكرمة.",
                    230.0,
                    "Umrah Partner",
                    "https://example.com/makkah-umrah",
                ),
                (
                    "Makkah",
                    "Makkah Historical Sites Tour",
                    "Religious",
                    "زيارة بعض المواقع التاريخية المرتبطة بالسيرة النبوية حول مكة المكرمة.",
                    150.0,
                    "Religious Guide",
                    "https://example.com/makkah-historical",
                ),

                # Madina
                (
                    "Madina",
                    "Ziyarah of Madina Landmarks",
                    "Religious",
                    "زيارة عدد من المساجد والمعالم التاريخية في المدينة المنورة مع مرشد.",
                    160.0,
                    "Ziyarah Partner",
                    "https://example.com/madina-ziyarah",
                ),
                (
                    "Madina",
                    "Madina Night Markets Walk",
                    "Leisure",
                    "جولة في الأسواق والمناطق التجارية القريبة من المسجد النبوي.",
                    70.0,
                    "Local Guide",
                    "https://example.com/madina-markets",
                ),

                # Dammam & Al Khobar
                (
                    "Dammam",
                    "Dammam Corniche & Park",
                    "Leisure",
                    "جلسة على كورنيش الدمام مع حدائق وألعاب أطفال ومطاعم مطلة على الخليج.",
                    60.0,
                    "Local Operator",
                    "https://example.com/dammam-corniche",
                ),
                (
                    "Al Khobar",
                    "Al Khobar Waterfront & Skywalk",
                    "Leisure",
                    "نزهة في واجهة الخبر البحرية مع ممشى وسكاي ووك ومقاهي ومطاعم مميزة.",
                    75.0,
                    "Local Operator",
                    "https://example.com/khobar-waterfront",
                ),
                (
                    "Al Khobar",
                    "Family Entertainment Center Visit",
                    "Family",
                    "زيارة مركز ترفيهي مغلق للعائلات مع ألعاب إلكترونية وجلسات مريحة.",
                    95.0,
                    "Entertainment Center",
                    "https://example.com/khobar-family-center",
                ),

                # Abha
                (
                    "Abha",
                    "Abha Mountains & Cable Car",
                    "Nature",
                    "تجربة العربات المعلقة مع إطلالات على الجبال والقرى في مدينة أبها.",
                    200.0,
                    "Abha Operator",
                    "https://example.com/abha-cablecar",
                ),
                (
                    "Abha",
                    "Rijal Almaa Heritage Village Tour",
                    "Culture",
                    "زيارة قرية رجال ألمع التراثية واستكشاف الطراز المعماري الفريد.",
                    170.0,
                    "Heritage Guide",
                    "https://example.com/abha-rijal-almaa",
                ),

                # Taif
                (
                    "Taif",
                    "Taif Rose Farms Visit",
                    "Culture",
                    "زيارة مزارع الورد الطائفي والتعرف على صناعة ماء الورد والعطور.",
                    140.0,
                    "Rose Farm Partner",
                    "https://example.com/taif-roses",
                ),
                (
                    "Taif",
                    "Taif Cable Car & Mountains",
                    "Nature",
                    "جولة في جبال الهدا أو الشفا مع العربات المعلقة وإطلالات جميلة.",
                    180.0,
                    "Taif Operator",
                    "https://example.com/taif-cablecar",
                ),

                # AlUla
                (
                    "AlUla",
                    "AlUla Heritage & Nature Tour",
                    "Nature",
                    "جولة في المواقع الأثرية والطبيعية بالعلا مع مرشد محلي.",
                    350.0,
                    "AlUla Partner",
                    "https://example.com/alula-heritage",
                ),
                (
                    "AlUla",
                    "AlUla Stargazing Night",
                    "Adventure",
                    "ليلة تحت النجوم في صحراء العلا مع جلسة بدوية وشرح عن السماء.",
                    320.0,
                    "Stargazing Operator",
                    "https://example.com/alula-stargazing",
                ),

                # Tabuk
                (
                    "Tabuk",
                    "Tabuk Desert & Historical Tour",
                    "Adventure",
                    "زيارة بعض المواقع الطبيعية والتاريخية حول تبوك مع جولة في الصحراء.",
                    260.0,
                    "Tabuk Operator",
                    "https://example.com/tabuk-desert",
                ),

                # NEOM
                (
                    "NEOM Region",
                    "NEOM Future Discovery Tour (Concept)",
                    "Futuristic",
                    "تجربة تعريفية برؤية نيوم وزيارة بعض المواقع المفتوحة حالياً حسب الأنظمة.",
                    400.0,
                    "NEOM Experience",
                    "https://example.com/neom-discovery",
                ),

                # Diriyah
                (
                    "Diriyah",
                    "Diriyah Heritage District Walk",
                    "Culture",
                    "جولة في منطقة الدرعية التاريخية مع مسار للمشاة ومقاهي ومتاحف.",
                    160.0,
                    "Diriyah Operator",
                    "https://example.com/diriyah-heritage",
                ),
            ]
            cur.executemany(
                """
                INSERT INTO activities
                (city, name, category, description, approx_price_usd, provider, booking_link)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                seed_activities,
            )
            conn.commit()


init_db()


# ==============================
# 3) دوال CRUD
# ==============================

def add_hotel(
    name: str,
    city: str,
    country: str,
    contact_name: str,
    contact_email: str,
    contact_phone: str,
    has_api: bool,
    notes: str,
) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO hotels
            (name, city, country, contact_name, contact_email, contact_phone, has_api, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, city, country, contact_name, contact_email, contact_phone, int(has_api), notes),
        )
        conn.commit()


def list_hotels() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query("SELECT * FROM hotels ORDER BY id DESC", conn)
    return df


def add_contract(
    hotel_id: int,
    contract_name: str,
    contract_type: str,
    currency: str,
    valid_from: str,
    valid_to: str,
    payment_terms: str,
    cancellation_policy: str,
    notes: str,
) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO contracts
            (hotel_id, contract_name, contract_type, currency, valid_from, valid_to,
             payment_terms, cancellation_policy, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hotel_id,
                contract_name,
                contract_type,
                currency,
                valid_from,
                valid_to,
                payment_terms,
                cancellation_policy,
                notes,
            ),
        )
        conn.commit()


def list_contracts() -> pd.DataFrame:
    query = """
    SELECT
        c.id,
        h.name AS hotel_name,
        c.contract_name,
        c.contract_type,
        c.currency,
        c.valid_from,
        c.valid_to,
        c.payment_terms,
        c.cancellation_policy,
        c.notes
    FROM contracts c
    JOIN hotels h ON c.hotel_id = h.id
    ORDER BY c.id DESC
    """
    with get_conn() as conn:
        df = pd.read_sql_query(query, conn)
    return df


def list_activities(city_filter: Optional[str] = None, category_filter: Optional[str] = None) -> pd.DataFrame:
    base_query = "SELECT * FROM activities"
    params: List[Any] = []
    conditions: List[str] = []

    if city_filter and city_filter != "الكل":
        conditions.append("city = ?")
        params.append(city_filter)

    if category_filter and category_filter != "الكل":
        conditions.append("category = ?")
        params.append(category_filter)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY city, category, name"

    with get_conn() as conn:
        df = pd.read_sql_query(base_query, conn, params=params)
    return df


def get_activities_by_ids(ids: List[int]) -> pd.DataFrame:
    if not ids:
        return pd.DataFrame()
    placeholders = ",".join(["?"] * len(ids))
    query = f"SELECT * FROM activities WHERE id IN ({placeholders}) ORDER BY city, name"
    with get_conn() as conn:
        df = pd.read_sql_query(query, conn, params=ids)
    return df


def save_itinerary(
    traveller_name: str,
    traveller_email: str,
    traveller_phone: str,
    form_data: Dict[str, Any],
    plan_text: str,
) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO itineraries
            (
                created_at,
                traveller_name,
                traveller_email,
                traveller_phone,
                from_city,
                destination_city,
                destination_country,
                days,
                budget,
                month,
                interests,
                plan_text
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                traveller_name,
                traveller_email,
                traveller_phone,
                form_data["from_city"],
                form_data["destination_city"],
                form_data["destination_country"],
                int(form_data["days"]),
                float(form_data["budget"]),
                form_data["month"],
                ", ".join(form_data["interests"]) if form_data["interests"] else "",
                plan_text,
            ),
        )
        conn.commit()


def list_itineraries() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                id,
                created_at,
                traveller_name,
                traveller_email,
                traveller_phone,
                from_city,
                destination_city,
                destination_country,
                days,
                budget,
                month,
                interests
            FROM itineraries
            ORDER BY datetime(created_at) DESC
            """,
            conn,
        )
    return df


def get_itinerary(itinerary_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM itineraries WHERE id = ?", (itinerary_id,))
        row = cur.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))


def add_package(
    name: str,
    city: str,
    days: int,
    budget: float,
    base_hotel_id: Optional[int],
    activities_ids: List[int],
    ai_plan_text: str,
    target_segment: str,
    price_from_usd: float,
    status: str,
    notes: str,
    source_itinerary_id: Optional[int],
) -> None:
    activities_str = ",".join(str(x) for x in activities_ids) if activities_ids else ""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO packages
            (
                created_at,
                name,
                city,
                days,
                budget,
                base_hotel_id,
                activities_ids,
                ai_plan_text,
                target_segment,
                price_from_usd,
                status,
                notes,
                source_itinerary_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                name,
                city,
                days,
                budget,
                base_hotel_id,
                activities_str,
                ai_plan_text,
                target_segment,
                price_from_usd,
                status,
                notes,
                source_itinerary_id,
            ),
        )
        conn.commit()


def list_packages() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                id,
                created_at,
                name,
                city,
                days,
                budget,
                target_segment,
                price_from_usd,
                status,
                source_itinerary_id
            FROM packages
            ORDER BY datetime(created_at) DESC
            """,
            conn,
        )
    return df


def get_package(package_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM packages WHERE id = ?", (package_id,))
        row = cur.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))


def add_booking_request(
    traveller_name: str,
    traveller_email: str,
    traveller_phone: str,
    from_city: str,
    to_city: str,
    days: int,
    budget: float,
    notes: str,
    status: str,
    source: str,
    package_id: Optional[int],
    itinerary_id: Optional[int],
) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO booking_requests
            (
                created_at,
                traveller_name,
                traveller_email,
                traveller_phone,
                from_city,
                to_city,
                days,
                budget,
                notes,
                status,
                source,
                package_id,
                itinerary_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                traveller_name,
                traveller_email,
                traveller_phone,
                from_city,
                to_city,
                days,
                budget,
                notes,
                status,
                source,
                package_id,
                itinerary_id,
            ),
        )
        conn.commit()


def list_booking_requests() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                id,
                created_at,
                traveller_name,
                traveller_email,
                traveller_phone,
                from_city,
                to_city,
                days,
                budget,
                notes,
                status,
                source,
                package_id,
                itinerary_id
            FROM booking_requests
            ORDER BY datetime(created_at) DESC
            """,
            conn,
        )
    return df


# ==============================
# 4) تكامل OpenAI
# ==============================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

try:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    client = None


def _call_ai(instructions: str, user_input: str) -> str:
    if not client or not OPENAI_API_KEY:
        return (
            "⚠️ التكامل مع OpenAI غير مفعّل بعد.\n"
            "رجاءً أضف مفتاح OPENAI_API_KEY في إعدادات السيرفر أو منصة النشر."
        )
    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            instructions=instructions,
            input=user_input,
        )
        return (resp.output_text or "").strip()
    except Exception as e:
        return f"حدث خطأ أثناء الاتصال بـ OpenAI: {e}"


def ai_travel_plan(form_data: Dict[str, Any]) -> str:
    instructions = (
        "أنت مساعد سياحي احترافي يعمل ضمن منصة HUMAIN Lifestyle. "
        "اكتب خطة رحلة مفصلة ومقسّمة على أيام، مع أنشطة مقترحة داخل السعودية، "
        "بميزانية محددة، وبأسلوب مرتب وواضح. ركّز على القيمة مقابل المال، "
        "واذكر أفكار لأنشطة (عمرة، ترفيه، تسوق، فعاليات، مباريات) حسب اهتمامات المستخدم."
    )

    user_prompt = f"""
المدينة الحالية: {form_data['from_city']}
الوجهة: {form_data['destination_city']}, {form_data['destination_country']}
عدد الأيام: {form_data['days']}
الميزانية الكلية (دولار): {form_data['budget']}
شهر السفر المتوقع: {form_data['month']}
الاهتمامات: {", ".join(form_data['interests']) if form_data['interests'] else "غير محددة"}

رجاءً:
- اقترح خطة يومية (Day 1, Day 2, ...) مع أنشطة محددة.
- اقترح توزيع تقريبي للميزانية (سكن، مواصلات، ترفيه، أنشطة).
- نبّه على أي نقاط مهمة (التأشيرة، المواسم، الحجز المبكر).
اكتب بالعربية الفصحى المبسّطة.
"""
    return _call_ai(instructions, user_prompt)


def ai_contract_helper(prompt: str) -> str:
    instructions = (
        "أنت مساعد قانوني/تجاري مختص في عقود توزيع وحجوزات الفنادق. "
        "اكتب بنود عقود أو سياسات إلغاء أو شروط دفع بصياغة عربية احترافية، مختصرة وواضحة."
    )
    return _call_ai(instructions, prompt)


def ai_general_chat(prompt: str) -> str:
    instructions = (
        "أنت مساعد ذكي في منصة HUMAIN Lifestyle، تساعد المستخدم في تخطيط السفر، "
        "الترفيه، والحجوزات، وتشرح الفكرة العامة للمنصة لو احتاج."
    )
    return _call_ai(instructions, prompt)


# ==============================
# 5) شاشة تسجيل الدخول
# ==============================

def login_screen():
    render_header()

    st.markdown(
        """
<div class="section-card">
  <h2>🔐 HUMAIN Lifestyle — Live Presentation Demo</h2>
  <p>سجّل الدخول للوصول إلى بوابة HUMAIN Lifestyle (نسخة العرض الحي الموجّهة للشركاء والمستثمرين).</p>
  <p style="font-size: 12px; opacity:0.9;">
  ⚠️ هذه منصة عرض أولية وغير مرتبطة رسمياً بأي جهة حكومية أو شركة تجارية في المملكة العربية السعودية.  
  كل البيانات المقدمة تجريبية ولا تمثل حجوزات حقيقية.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("اسم المستخدم", placeholder="مثال: admin / demo / partner")
        with col2:
            password = st.text_input("كلمة المرور", type="password", placeholder="••••••••")

        remember = st.checkbox("تذكّرني على هذا الجهاز", value=True)
        submitted = st.form_submit_button("🚀 دخول", type="primary")

    if submitted:
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state.authenticated = True
            st.session_state.current_user = username
            st.session_state.current_role = user["role"]
            if remember:
                st.session_state.remember_me = True
            st.success("✅ تم تسجيل الدخول بنجاح.")
            st.experimental_rerun()
        else:
            st.error("❌ بيانات الدخول غير صحيحة. جرّب مرة أخرى.")


# ==============================
# 6) واجهات الصفحات
# ==============================

def page_home():
    render_header()
    st.title("🌍 HUMAIN Lifestyle — Your Gateway to KSA")

    st.markdown(
        """
<div class="section-card">
  <h3>🎯 What is HUMAIN Lifestyle?</h3>
  <p>
  <strong>HUMAIN Lifestyle</strong> هو نموذج أوّلي لمنصّة حياة متكاملة تربط المسافر، المعتمر، والمستثمر بالمملكة العربية السعودية
  في تجربة رقمية واحدة، مدعومة بالذكاء الاصطناعي.
  </p>
  <p>
  من أول فكرة السفر… إلى الطيران، القطار، الفنادق، الترفيه، العمرة والحج، وحتى خدمات تأسيس الأعمال — كل ذلك في واجهة موحّدة.
  </p>
</div>

<div class="section-card">
  <h3>🧩 Core Journeys in the Live Demo</h3>
  <ul>
    <li>🧭 <strong>Trip Planner (B2C)</strong> — مخطّط رحلات ذكي إلى مدن السعودية.</li>
    <li>🎟️ <strong>Experiences & Activities</strong> — كتالوج تجارب وأنشطة في الرياض، جدة، مكة، المدينة، العلا، نيوم…</li>
    <li>📝 <strong>Saved Itineraries</strong> — حفظ خطط الرحلات ومراجعتها لاحقاً.</li>
    <li>📦 <strong>Packages / Programs</strong> — تحويل الخطط إلى برامج جاهزة للبيع.</li>
    <li>🕋 <strong>Umrah & Hajj</strong> — طلب برامج عمرة/حج متكاملة.</li>
    <li>💼 <strong>Invest in KSA</strong> — بوابة المستثمرين وروّاد الأعمال.</li>
    <li>✈️ <strong>Flights</strong> & 🚄 <strong>Rail</strong> — تجميع طلبات سفر منظمّة.</li>
    <li>📥 <strong>Booking Requests (Admin)</strong> — شاشة إدارة لكل الـ Leads.</li>
    <li>🤖 <strong>AI Co-pilot</strong> — مساعد ذكي داخل المنصّة.</li>
  </ul>
</div>

<div class="section-card">
  <h3>🏗 From Demo → Live Presentation Demo</h3>
  <p>
  هذه النسخة مصممة لتكون <strong>Live Presentation Demo</strong> جاهزة للعرض على شركاء داخل السعودية (مثل NEOM، البنوك، وشركات السفر)،
  مع إمكانية تطويرها لاحقاً للربط الفعلي مع الأنظمة (NDC/GDS, SAR, Nusuk, Banks, Wallets).
  </p>
  <p style="font-size: 13px; opacity: 0.9;">
  ⚠️ ملاحظة: لا توجد تكاملات حقيقية بعد — كل الطلبات تُسجَّل في قاعدة البيانات كـ Leads وتُستخدم للأفكار والاختبار.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )


# باقي الصفحات من نسختك الأصلية (Trip Planner, Activities, Itineraries, Packages,
# Booking Requests, Hotels Admin, Flights, Rail, Umrah, Investor, Lifestyle,
# Health/Insurance, Education/Jobs) تبقى كما هي بالضبط – لن أكررها هنا لتقليل الطول.
# 👇 مهم: تأكد أن هذه الدوال موجودة كما في كودك السابق:


# --- ضع هنا تعريفات: page_trip_planner, page_activities, page_itineraries,
# page_packages, page_booking_requests, page_hotels_admin,
# page_flights, page_rail, page_umrah, page_investor_gateway,
# page_lifestyle, page_health_insurance, page_education_jobs ---
# (انسخها كما كانت عندك بدون تعديل، لأنها طويلة جداً ومضبوطة)


# ==============================
# 7) AI Co-pilot
# ==============================

def page_ai_assistant():
    render_header()
    st.title("🤖 HUMAIN AI Co-pilot")

    st.write(
        "من هنا تقدر تتحاور مع المساعد الذكي حول السفر، نمط الحياة، الاستثمار في السعودية، "
        "وأيضاً تسأله عن فكرة HUMAIN Lifestyle نفسها."
    )

    if "ai_history" not in st.session_state:
        st.session_state.ai_history = []

    col_chat, col_info = st.columns([2, 1])

    with col_chat:
        st.subheader("💬 جلسة المحادثة")

        if st.session_state.ai_history:
            for msg in st.session_state.ai_history:
                role = "🧑‍💻 أنت" if msg["role"] == "user" else "🤖 HUMAIN Co-pilot"
                box_color = "#F5F5F5" if msg["role"] == "user" else "#E7F8F0"
                st.markdown(
                    f"""
                    <div style="background:{box_color}; padding:10px 12px; border-radius:10px; margin-bottom:6px;">
                        <strong>{role}:</strong><br>{msg["content"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("ابدأ بكتابة أول سؤال أو طلبك في الأسفل 👇")

        st.markdown("---")
        user_prompt = st.text_area("اكتب سؤالك أو فكرتك هنا", height=120)

        col_send1, col_send2 = st.columns([1, 3])
        with col_send1:
            if st.button("📨 إرسال", type="primary"):
                if not user_prompt.strip():
                    st.error("رجاءً اكتب شيئاً أولاً.")
                else:
                    st.session_state.ai_history.append(
                        {"role": "user", "content": user_prompt.strip()}
                    )
                    with st.spinner("جاري توليد رد المساعد..."):
                        answer = ai_general_chat(user_prompt.strip())
                    st.session_state.ai_history.append(
                        {"role": "assistant", "content": answer}
                    )
                    st.experimental_rerun()

        with col_send2:
            if st.button("🧹 مسح المحادثة"):
                st.session_state.ai_history = []
                st.experimental_rerun()

    with col_info:
        st.subheader("ℹ️ عن HUMAIN Co-pilot")
        st.markdown(
            """
- مبني على OpenAI (في نسخة الـ Demo).
- مخصص لفهم:
  - السفر داخل السعودية
  - العمرة والحج
  - الاستثمار ورواد الأعمال
  - نمط الحياة، الصحة، والتعليم
- يمكن لاحقاً ربطه بـ **HUMAIN ONE / ALLAM** أو نماذج محلية.
"""
        )
        st.markdown("---")
        st.caption(
            "تنبيه: هذه النسخة للاستخدام التجريبي فقط، وليست أداة استشارات قانونية أو مالية رسمية."
        )


# ==============================
# 8) Leads Dashboard
# ==============================

def page_leads_dashboard():
    render_header()
    st.title("📊 Leads Dashboard — HUMAIN Lifestyle")

    df = list_booking_requests()
    if df.empty:
        st.info("لا توجد طلبات حجز حتى الآن لعرضها في لوحة المتابعة.")
        return

    try:
        df["created_at_dt"] = pd.to_datetime(df["created_at"])
    except Exception:
        df["created_at_dt"] = df["created_at"]

    total_leads = len(df)
    by_source = df["source"].value_counts()
    by_status = df["status"].value_counts()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("إجمالي الطلبات", total_leads)
    with col2:
        st.metric("عدد المصادر المختلفة", by_source.shape[0])
    with col3:
        st.metric("عدد الحالات المختلفة", by_status.shape[0])

    st.markdown("---")
    st.subheader("📌 توزيع حسب المصدر (Source)")
    st.bar_chart(by_source)

    st.subheader("📌 توزيع حسب الحالة (Status)")
    st.bar_chart(by_status)

    st.markdown("---")
    st.subheader("📥 تصدير البيانات")

    csv_data = df.drop(columns=["created_at_dt"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ تنزيل كـ CSV",
        data=csv_data,
        file_name="humain_leads.csv",
        mime="text/csv",
    )

    st.markdown("### معاينة سريعة للبيانات الخام")
    st.dataframe(df.drop(columns=["created_at_dt"], errors="ignore"), use_container_width=True, hide_index=True)


# ==============================
# 9) فوتر قانوني / حقوق ملكية
# ==============================

def render_legal_footer():
    st.markdown("---")
    st.markdown(
        """
<p style="font-size: 12px; opacity:0.85;">
<strong>⚠️ HUMAIN Lifestyle — Live Presentation Demo</strong><br>
هذه منصة عرض أولية وغير مرتبطة رسمياً بأي جهة حكومية أو شركة تجارية في المملكة العربية السعودية.  
كل البيانات المقدمة تجريبية ولا تمثل حجوزات حقيقية أو عروض ملزمة.
</p>
<p style="font-size: 11px; opacity:0.7;">
© 2025 HUMAIN Lifestyle / Dara Khartoum Air Booking Agency — All rights reserved.<br>
جميع الحقوق محفوظة. يمنع نسخ أو إعادة استخدام الفكرة أو التصميم أو المكونات البرمجية بدون إذن خطي من المالك.
</p>
""",
        unsafe_allow_html=True,
    )


# ==============================
# 10) توجيه الصفحات + الجلسة
# ==============================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_role" not in st.session_state:
    st.session_state.current_role = "demo"

# لو غير مسجل دخول → شاشة الدخول
if not st.session_state.authenticated:
    login_screen()
    render_legal_footer()
    st.stop()

role = st.session_state.current_role

st.sidebar.title("HUMAIN Lifestyle 🌍")
st.sidebar.markdown(f"👤 المستخدم: **{st.session_state.get('current_user', 'Guest')}**")
st.sidebar.markdown(f"🔐 الدور: **{role}**")

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.current_role = "demo"
    st.experimental_rerun()

general_pages = [
    "🏠 Home",
    "🧭 Trip Planner (B2C)",
    "🎟️ Experiences & Activities",
    "📝 Saved Itineraries",
    "📦 Packages / Programs",
    "✈️ Flights to KSA",
    "🚄 Saudi Rail",
    "🕋 Umrah & Hajj",
    "💼 Invest in KSA",
    "🏙️ Local Lifestyle & Services",
    "🩺 Health & Insurance",
    "🎓 Education & Jobs",
    "🤖 AI Co-pilot",
]

admin_only_pages = [
    "📊 Leads Dashboard",
    "📥 Booking Requests (Admin)",
    "🏨 Hotels & Contracts (Admin)",
]

if role == "admin":
    pages = general_pages + admin_only_pages
else:
    pages = general_pages

page = st.sidebar.radio("اختر الصفحة", pages)

if page.startswith("🏠"):
    page_home()
elif page.startswith("🧭"):
    page_trip_planner()
elif page.startswith("🎟️"):
    page_activities()
elif page.startswith("📝"):
    page_itineraries()
elif page.startswith("📦"):
    page_packages()
elif page.startswith("✈️"):
    page_flights()
elif page.startswith("🚄"):
    page_rail()
elif page.startswith("🕋"):
    page_umrah()
elif page.startswith("💼"):
    page_investor_gateway()
elif page.startswith("🏙️"):
    page_lifestyle()
elif page.startswith("🩺"):
    page_health_insurance()
elif page.startswith("🎓"):
    page_education_jobs()
elif page.startswith("📊"):
    page_leads_dashboard()
elif page.startswith("📥"):
    page_booking_requests()
elif page.startswith("🏨"):
    page_hotels_admin()
elif page.startswith("🤖"):
    page_ai_assistant()

render_legal_footer()
