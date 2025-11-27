import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from typing import Dict, Any, List, Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from layout_header import render_header  # الهيدر الأخضر الذهبي

# ==============================
# 1) إعداد عام للتطبيق
# ==============================

st.set_page_config(
    page_title="HUMAIN Lifestyle",
    page_icon="🌍",
    layout="wide",
)

load_dotenv()  # قراءة OPENAI_API_KEY من .env (لو موجود)

DB_PATH = "humain_lifestyle.db"


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

        # الخدمات الحياتية المحلية (مطاعم، سوبرماركت، تعليم، صحة، الخ)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS local_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                name TEXT NOT NULL,
                sector TEXT NOT NULL,      -- Food, Shopping, Education, Health, Sports, Community, Services
                sub_type TEXT,
                description TEXT,
                address TEXT,
                contact_phone TEXT,
                website TEXT,
                tags TEXT
            );
            """
        )

        conn.commit()

        # لو ما في أنشطة، نضيف كتالوج أولي
        cur.execute("SELECT COUNT(*) FROM activities;")
        count_acts = cur.fetchone()[0]
        if count_acts == 0:
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

        # لو ما في خدمات حياتية، نضيف كتالوج أولي (مطاعم، سوبرماركت، تعليم، صحة...)
        cur.execute("SELECT COUNT(*) FROM local_services;")
        count_ls = cur.fetchone()[0]
        if count_ls == 0:
            seed_local_services = [
                # Food & Cafes
                (
                    "Riyadh",
                    "Najd Village Restaurant",
                    "Food",
                    "Saudi Restaurant",
                    "مطعم يقدم الأكلات السعودية الشعبية في جو تراثي مناسب للعائلات والضيوف.",
                    "حي العليا، الرياض",
                    "+966-11-000-0000",
                    "https://example.com/najd-village",
                    "مطعم,سعودي,عائلي",
                ),
                (
                    "Riyadh",
                    "Specialty Coffee Hub",
                    "Food",
                    "Cafe",
                    "كوفي شوب مختص يقدم قهوة مختصة وجلسات عمل واجتماع مع إنترنت سريع.",
                    "حي الصحافة، الرياض",
                    "+966-11-000-0001",
                    "https://example.com/coffee-hub",
                    "كوفي,قهوة مختصة,عمل",
                ),
                (
                    "Jeddah",
                    "Red Sea Seafood Market",
                    "Food",
                    "Seafood",
                    "سوق ومطعم للمأكولات البحرية الطازجة على الواجهة البحرية.",
                    "كورنيش جدة",
                    "+966-12-000-0002",
                    "https://example.com/redsea-seafood",
                    "بحري,مطعم,عائلي",
                ),

                # Supermarkets & Shopping
                (
                    "Riyadh",
                    "City Hypermarket",
                    "Shopping",
                    "Hypermarket",
                    "هايبرماركت متكامل للمواد الغذائية والمنتجات المنزلية.",
                    "طريق الملك فهد، الرياض",
                    "+966-11-000-0003",
                    "https://example.com/city-hyper",
                    "سوبرماركت,مواد غذائية,منزلي",
                ),
                (
                    "Jeddah",
                    "Jeddah Mall",
                    "Shopping",
                    "Mall",
                    "مجمع تجاري كبير يضم محلات ملابس، الكترونيات، مطاعم، ومناطق ترفيه.",
                    "حي الأندلس، جدة",
                    "+966-12-000-0004",
                    "https://example.com/jeddah-mall",
                    "مول,تسوق,ترفيه",
                ),
                (
                    "Riyadh",
                    "Office & Home Furniture Center",
                    "Shopping",
                    "Furniture",
                    "معرض لقطع الأثاث المكتبي والمنزلي مع خيارات مختلفة للأسعار.",
                    "المنطقة الصناعية، الرياض",
                    "+966-11-000-0005",
                    "https://example.com/furniture-center",
                    "أثاث,مكتبي,منزلي",
                ),

                # Education & Courses
                (
                    "Riyadh",
                    "Riyadh Language Institute",
                    "Education",
                    "Languages",
                    "معهد لتعليم اللغات (إنجليزي، عربي لغير الناطقين، ولغات أخرى).",
                    "حي الملك عبدالله، الرياض",
                    "+966-11-000-0006",
                    "https://example.com/riyadh-language",
                    "تعليم,لغات,دورات",
                ),
                (
                    "Jeddah",
                    "Tech Skills Academy",
                    "Education",
                    "IT & Coding",
                    "أكاديمية لتعليم البرمجة، التحول الرقمي، والمهارات التقنية للشباب.",
                    "حي السلامة، جدة",
                    "+966-12-000-0007",
                    "https://example.com/tech-academy",
                    "برمجة,تقنية,دورات",
                ),

                # Sports & Community
                (
                    "Riyadh",
                    "Riyadh Sports Club",
                    "Sports",
                    "Gym & Fitness",
                    "نادي رياضي متكامل مع أجهزة حديثة، حصص لياقة، ومدربين شخصيين.",
                    "حي الياسمين، الرياض",
                    "+966-11-000-0008",
                    "https://example.com/riyadh-sports",
                    "رياضة,نادي,لياقة",
                ),
                (
                    "Jeddah",
                    "Community Cultural Center",
                    "Community",
                    "Cultural Center",
                    "مركز مجتمعي يقدم فعاليات ثقافية، ورش عمل، وأنشطة عائلية.",
                    "حي الروضة، جدة",
                    "+966-12-000-0009",
                    "https://example.com/community-center",
                    "مجتمعي,ثقافة,فعاليات",
                ),

                # Health & Clinics (مكمّلة لصفحة الصحة)
                (
                    "Riyadh",
                    "Riyadh Specialized Clinic",
                    "Health",
                    "Clinic",
                    "عيادة تخصصية تقدم استشارات طبية في عدة تخصصات.",
                    "حي المروج، الرياض",
                    "+966-11-000-0010",
                    "https://example.com/riyadh-clinic",
                    "عيادة,صحة,استشارات",
                ),
                (
                    "Jeddah",
                    "Jeddah General Hospital",
                    "Health",
                    "Hospital",
                    "مستشفى عام يقدم خدمات طبية متكاملة مع طوارئ على مدار الساعة.",
                    "شمال جدة",
                    "+966-12-000-0011",
                    "https://example.com/jeddah-hospital",
                    "مستشفى,طوارئ,صحة",
                ),
            ]
            cur.executemany(
                """
                INSERT INTO local_services
                (city, name, sector, sub_type, description, address, contact_phone, website, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                seed_local_services,
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


def list_local_services(
    city_filter: Optional[str] = None,
    sector_filter: Optional[str] = None,
    search: Optional[str] = None,
) -> pd.DataFrame:
    base_query = "SELECT * FROM local_services"
    params: List[Any] = []
    conditions: List[str] = []

    if city_filter and city_filter != "الكل":
        conditions.append("city = ?")
        params.append(city_filter)

    if sector_filter and sector_filter != "الكل":
        conditions.append("sector = ?")
        params.append(sector_filter)

    if search and search.strip():
        conditions.append("(name LIKE ? OR description LIKE ? OR tags LIKE ?)")
        like_val = f"%{search.strip()}%"
        params.extend([like_val, like_val, like_val])

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY city, sector, name"

    with get_conn() as conn:
        df = pd.read_sql_query(base_query, conn, params=params)
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
# 5) واجهات الصفحات
# ==============================


def page_home():
    render_header()
    st.title("🌍 HUMAIN Lifestyle")
    st.caption("your gateway to KSA — منصّة ذكية تربط بين الزائر، المعتمر، والمستثمر")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            """
مرحباً بك في **HUMAIN Lifestyle** — نموذج أولي (Live Demo) لمنصّة رقمية ذكية
تجمع كل ما يخص المملكة في مكان واحد:

- **Travel & Leisure**: تخطيط رحلات، أنشطة، برامج، وفنادق داخل السعودية.
- **Umrah & Hajj**: طلب برامج عمرة/حج متكاملة (سكن + نقل + خدمات).
- **Invest in KSA**: بوابة للمستثمرين وروّاد الأعمال لتأسيس مشاريعهم داخل المملكة.
- **Local Lifestyle**: مطاعم، تسوق، تعليم، صحة، رياضة، وخدمات مجتمعية.

المنصّة مصمَّمة بحيث:

> المستخدم يدخل من HUMAIN Lifestyle  
> ثم **نحن** نوزِّعه على أفضل مزوّدي الخدمات (طيران، قطار، فنادق، بنوك، منصّات رسمية، مزودي خدمات محليين) وفق الشراكات المستقبلية.
"""
        )

    with col2:
        st.info(
            "ℹ️ **Demo Mode — وضع العرض التجريبي**\n\n"
            "- البيانات الحالية تجريبية وليست مرتبطة بأنظمة حجز حقيقية.\n"
            "- كل الطلبات (Flights, Rail, Umrah, Investor, Health, Local Services...) تُسجَّل في النظام كـ Leads.\n"
            "- البنية جاهزة للربط مع HUMAIN ONE، ALLAM، وموفّري خدمات في السعودية لاحقاً."
        )

    st.markdown("---")
    st.markdown("### 👥 من المنصّة دي موجهة لمين؟")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("#### 🧳 Travelers & Visitors")
        st.markdown(
            """
- تخطيط رحلة إلى مدينة سعودية
- اختيار أنشطة وتجارب
- تجميع برنامج كامل (Package)
- اكتشاف مطاعم، كافيهات، ومولات
"""
        )
        st.markdown("**جرّب:**\n- 🧭 Trip Planner\n- 🎟️ Experiences\n- 🏙️ Local Lifestyle\n- 📦 Packages")

    with c2:
        st.markdown("#### 🕋 Pilgrims (Umrah & Hajj)")
        st.markdown(
            """
- طلب برنامج عمرة أو عمرة + سياحة
- سكن في مكة والمدينة
- تنقّل، أنشطة دينية وترفيهية
- دعم صحي وتأمين أثناء الإقامة
"""
        )
        st.markdown("**جرّب:**\n- 🕋 Umrah & Hajj\n- ✈️ Flights to KSA\n- 🚄 Saudi Rail\n- 🏥 Health & Insurance")

    with c3:
        st.markdown("#### 💼 Investors & Business")
        st.markdown(
            """
- تأسيس شركة أو نشاط تجاري
- مكاتب، شقق، بنوك، استشارات
- التعرف على نمط الحياة في المدينة (تعليم، صحة، تسوق)
- طلب موحّد لكل خدمات الاستثمار
"""
        )
        st.markdown("**جرّب:**\n- 💼 Invest in KSA\n- 🏙️ Local Lifestyle\n- 📥 Booking Requests (Admin)")

    st.markdown("---")
    st.markdown("### 🔗 أقسام المنصّة (اختصار)")

    st.markdown(
        """
- 🧭 **Trip Planner (B2C)** → ذكاء اصطناعي لتخطيط الرحلات وحفظ الخطط.  
- 🎟️ **Experiences & Activities** → كتالوج أنشطة وتجارب داخل مدن المملكة.  
- 🏙️ **Local Lifestyle & Services** → مطاعم، سوبرماركت، مولات، تعليم، صحة، رياضة، ومراكز مجتمعية.  
- 📦 **Packages / Programs** → تحويل الخطط إلى منتجات جاهزة للبيع.  
- ✈️ **Flights to KSA** & 🚄 **Saudi Rail** → تجميع طلبات السفر (Leads) للطيران والقطار.  
- 🕋 **Umrah & Hajj** → بوابة برامج العمرة والحج، تمهيداً للتكامل مع منصات رسمية.  
- 🏥 **Health & Insurance** → تجميع طلبات التأمين الصحي وحجوزات المستشفيات/العيادات.  
- 💼 **Invest in KSA** → بوابة المستثمرين لتجميع كل طلباتهم في مكان واحد.  
- 📥 **Booking Requests (Admin)** → شاشة الإدارة لمتابعة كل الـ Leads.  
- 🏨 **Hotels & Contracts (Admin)** → إدارة الفنادق والعقود الخلفية (Back-office).  
- 🤖 **AI Assistant** → مساعد ذكي مدمج داخل المنصّة.
"""
    )


def page_trip_planner():
    render_header()
    st.title("🧭 Trip Planner (B2C) — مخطِّط رحلة ذكي")

    st.write(
        "أدخل تفضيلاتك الأساسية، ودع المنصة تقترح لك خطة رحلة متكاملة "
        "إلى السعودية (كخطوة أولى في الـ Demo)."
    )

    with st.form("trip_form"):
        col1, col2 = st.columns(2)

        with col1:
            from_city = st.text_input("أين أنت الآن؟ (مدينة الانطلاق)", value="Cairo")
            destination_country = st.text_input("الوجهة (الدولة)", value="Saudi Arabia")
            destination_city = st.selectbox(
                "مدينة الوجهة داخل السعودية",
                [
                    "Riyadh",
                    "Jeddah",
                    "Makkah",
                    "Madina",
                    "Dammam",
                    "Al Khobar",
                    "Abha",
                    "Taif",
                    "AlUla",
                    "Tabuk",
                    "NEOM Region",
                    "Diriyah",
                ],
            )

        with col2:
            budget = st.slider("الميزانية الكلية بالدولار", min_value=500, max_value=10000, value=2500, step=100)
            days = st.slider("مدة الرحلة (أيام)", min_value=3, max_value=21, value=7)
            month = st.selectbox(
                "شهر السفر المتوقع",
                [
                    "غير محدد",
                    "يناير",
                    "فبراير",
                    "مارس",
                    "أبريل",
                    "مايو",
                    "يونيو",
                    "يوليو",
                    "أغسطس",
                    "سبتمبر",
                    "أكتوبر",
                    "نوفمبر",
                    "ديسمبر",
                ],
            )

        interests = st.multiselect(
            "ما هي اهتماماتك الرئيسية في هذه الرحلة؟",
            ["عمرة", "سياحة دينية", "تسوق", "فعاليات ترفيهية", "مباريات كرة", "طبيعة وهدوء", "مطاعم وتجارب طعام"],
        )

        st.markdown("---")
        st.markdown("### حفظ هذه الخطة في النظام (اختياري)")

        col3, col4 = st.columns(2)
        with col3:
            traveller_name = st.text_input("اسم المسافر (اختياري)")
            traveller_email = st.text_input("البريد الإلكتروني (اختياري)")
        with col4:
            traveller_phone = st.text_input("رقم الهاتف (اختياري)")
            save_plan_flag = st.checkbox("🔐 احفظ هذه الخطة في النظام بعد توليدها")

        submitted = st.form_submit_button("✨ اقترح لي خطة رحلة")

    if submitted:
        form_data = {
            "from_city": from_city.strip(),
            "destination_country": destination_country.strip(),
            "destination_city": destination_city.strip(),
            "budget": budget,
            "days": days,
            "month": month,
            "interests": interests,
        }

        with st.spinner("جاري توليد خطة الرحلة بالذكاء الاصطناعي..."):
            plan_text = ai_travel_plan(form_data)

        st.markdown("### ✈️ الخطة المقترحة:")
        st.write(plan_text)

        if save_plan_flag and plan_text and not plan_text.startswith("⚠️"):
            save_itinerary(
                traveller_name=traveller_name.strip(),
                traveller_email=traveller_email.strip(),
                traveller_phone=traveller_phone.strip(),
                form_data=form_data,
                plan_text=plan_text,
            )
            st.success("✅ تم حفظ هذه الخطة في قسم Saved Itineraries.")
        elif save_plan_flag and plan_text.startswith("⚠️"):
            st.warning("لم يتم الحفظ لأن التكامل مع الذكاء الاصطناعي غير مفعّل حالياً.")

        st.markdown("---")
        st.caption(
            "هذه خطة تجريبية (Demo) مبنية على الذكاء الاصطناعي فقط، "
            "وليست مرتبطة بعد بأنظمة حجز حقيقية."
        )


def page_activities():
    render_header()
    st.title("🎟️ Experiences & Activities — الأنشطة والتجارب")

    st.write(
        "كتالوج تجريبي لأنشطة وتجارب داخل مدن مختلفة في السعودية. "
        "يمكن لاحقاً ربط هذه الأنشطة بمنصات حجز حقيقية (Tickets, Events, Tours APIs)."
    )

    with get_conn() as conn:
        df_all = pd.read_sql_query("SELECT DISTINCT city FROM activities ORDER BY city;", conn)
        df_cat = pd.read_sql_query("SELECT DISTINCT category FROM activities ORDER BY category;", conn)

    cities = ["الكل"] + df_all["city"].tolist()
    categories = ["الكل"] + df_cat["category"].dropna().tolist()

    col1, col2 = st.columns(2)
    with col1:
        city_filter = st.selectbox("اختر المدينة", cities)
    with col2:
        category_filter = st.selectbox("اختر نوع النشاط", categories)

    df = list_activities(city_filter, category_filter)

    if df.empty:
        st.info("لا توجد أنشطة مطابقة للفلتر الحالي.")
        return

    st.markdown("---")
    st.subheader("الأنشطة المتاحة")

    for _, row in df.iterrows():
        with st.expander(f"{row['name']} — {row['city']} ({row['category']})"):
            st.write(row["description"])
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                if row["approx_price_usd"]:
                    st.write(f"💰 السعر التقريبي: **{row['approx_price_usd']:.0f} دولار**")
                else:
                    st.write("💰 السعر: غير محدد")
            with col2:
                if row["provider"]:
                    st.write(f"🤝 المزوّد: {row['provider']}")
            with col3:
                if row["booking_link"]:
                    st.link_button("رابط حجز (تجريبي)", row["booking_link"])


def page_local_lifestyle():
    render_header()
    st.title("🏙️ Local Lifestyle & Services — نمط الحياة والخدمات المحلية")

    st.write(
        "اكتشف المطاعم، الكافيهات، السوبرماركت، المولات، المعاهد التعليمية، الأندية الرياضية، "
        "والمراكز الصحية والمجتمعية في مدن مختلفة داخل المملكة."
    )

    with get_conn() as conn:
        df_cities = pd.read_sql_query("SELECT DISTINCT city FROM local_services ORDER BY city;", conn)
        df_sectors = pd.read_sql_query("SELECT DISTINCT sector FROM local_services ORDER BY sector;", conn)

    city_options = ["الكل"] + df_cities["city"].tolist()
    sector_options_map = {
        "الكل": "الكل",
        "Food": "Food (مطاعم وكافيهات)",
        "Shopping": "Shopping (تسوق وسوبرماركت)",
        "Education": "Education (تعليم ودورات)",
        "Health": "Health (صحة وعيادات)",
        "Sports": "Sports (نوادي ولياقة)",
        "Community": "Community (مراكز مجتمعية)",
        "Services": "Services (خدمات متنوعة)",
    }

    sector_keys = ["الكل"] + df_sectors["sector"].tolist()
    readable_sectors = [sector_options_map.get(s, s) for s in sector_keys]

    col1, col2, col3 = st.columns([1.2, 1.2, 1.5])
    with col1:
        city_filter = st.selectbox("المدينة", city_options)
    with col2:
        selected_sector_label = st.selectbox("قطاع الخدمة", readable_sectors)
        # رجّعها لـ key الأصلي
        sector_filter = None
        for key, label in sector_options_map.items():
            if label == selected_sector_label:
                sector_filter = key
                break
    with col3:
        search = st.text_input("بحث بالاسم / الوصف / التاغات", value="")

    df = list_local_services(
        city_filter=city_filter,
        sector_filter=sector_filter,
        search=search,
    )

    if df.empty:
        st.info("لا توجد خدمات مطابقة للفلتر الحالي.")
        return

    st.markdown("---")
    st.subheader("الخدمات المتاحة")

    for _, row in df.iterrows():
        sector_name = sector_options_map.get(row["sector"], row["sector"])
        title = f"{row['name']} — {row['city']} ({sector_name})"
        with st.expander(title):
            if row["description"]:
                st.write(row["description"])
            if row["address"]:
                st.write(f"📍 العنوان: {row['address']}")
            col1, col2 = st.columns(2)
            with col1:
                if row["contact_phone"]:
                    st.write(f"📞 هاتف: {row['contact_phone']}")
                if row["sub_type"]:
                    st.write(f"🔹 نوع الخدمة: {row['sub_type']}")
            with col2:
                if row["website"]:
                    st.link_button("🌐 موقع / صفحة (تجريبي)", row["website"])
                if row["tags"]:
                    st.write(f"🏷️ تاغات: {row['tags']}")


def page_itineraries():
    render_header()
    st.title("📝 Saved Itineraries — خطط الرحلات المحفوظة")

    df = list_itineraries()
    if df.empty:
        st.info("لا توجد خطط رحلات محفوظة حتى الآن. جرّب إنشاء خطة من صفحة Trip Planner.")
        return

    st.subheader("قائمة الخطط")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    labels = []
    for _, row in df.iterrows():
        label = f"#{row['id']} — {row['traveller_name'] or 'بدون اسم'} ({row['from_city']} → {row['destination_city']})"
        labels.append(label)

    selected_label = st.selectbox("اختر خطة لعرض التفاصيل", labels)
    if selected_label:
        try:
            selected_id = int(selected_label.split("—")[0].replace("#", "").strip())
        except Exception:
            selected_id = None

        if selected_id:
            details = get_itinerary(selected_id)
            if not details:
                st.error("تعذر تحميل تفاصيل هذه الخطة.")
                return

            st.markdown("### تفاصيل الخطة")
            st.write(f"👤 المسافر: {details.get('traveller_name') or 'غير محدد'}")
            st.write(f"📧 البريد: {details.get('traveller_email') or 'غير محدد'}")
            st.write(f"📱 الهاتف: {details.get('traveller_phone') or 'غير محدد'}")
            st.write(
                f"✈️ المسار: {details.get('from_city')} → {details.get('destination_city')}, {details.get('destination_country')}"
            )
            st.write(f"🗓️ الأيام: {details.get('days')} | 💰 الميزانية: {details.get('budget')} USD")
            st.write(f"🕒 أنشئت في: {details.get('created_at')}")
            st.write(f"🎯 الاهتمامات: {details.get('interests') or 'غير محددة'}")

            st.markdown("---")
            st.markdown("### نص الخطة الكاملة:")
            st.write(details.get("plan_text") or "")


def page_packages():
    render_header()
    st.title("📦 Packages / Programs — برامج جاهزة للبيع")

    st.write(
        "حوّل خطط الرحلات المحفوظة إلى برامج (Packages) تحتوي على: مدينة، فندق، أنشطة، وسعر تقريبي."
    )

    tab_create, tab_list = st.tabs(["إنشاء برنامج جديد", "قائمة البرامج"])

    # إنشاء برنامج جديد
    with tab_create:
        itineraries_df = list_itineraries()
        if itineraries_df.empty:
            st.info("لا توجد خطط رحلات محفوظة بعد. جرّب إنشاء خطة من صفحة Trip Planner أولاً.")
        else:
            st.subheader("1) اختر خطة رحلة كأساس للبرنامج")

            labels = []
            id_mapping: Dict[str, int] = {}
            for _, row in itineraries_df.iterrows():
                label = (
                    f"#{row['id']} — {row['traveller_name'] or 'بدون اسم'} "
                    f"({row['from_city']} → {row['destination_city']}, {row['days']} أيام)"
                )
                labels.append(label)
                id_mapping[label] = int(row["id"])

            selected_label = st.selectbox("اختر خطة", labels)
            source_itinerary_id = id_mapping[selected_label]
            itinerary_details = get_itinerary(source_itinerary_id)

            default_city = itinerary_details["destination_city"] or ""
            default_days = int(itinerary_details["days"] or 7)
            default_budget = float(itinerary_details["budget"] or 2500.0)
            default_plan_text = itinerary_details.get("plan_text") or ""

            st.markdown("---")
            st.subheader("2) تعريف البرنامج")

            hotels_df = list_hotels()
            hotel_options: Dict[str, Optional[int]] = {"بدون فندق محدد": None}
            if not hotels_df.empty:
                for _, row in hotels_df.iterrows():
                    label_h = f"{row['name']} ({row['city'] or ''})"
                    hotel_options[label_h] = int(row["id"])

            activities_df = list_activities(city_filter=default_city, category_filter=None)
            activity_labels: List[str] = []
            activity_map: Dict[str, int] = {}
            for _, row in activities_df.iterrows():
                lbl = f"{row['name']} — {row['city']} ({row['category']})"
                activity_labels.append(lbl)
                activity_map[lbl] = int(row["id"])

            with st.form("create_package_form"):
                pkg_name = st.text_input("اسم البرنامج *", value=f"برنامج {default_city} {default_days} أيام")
                pkg_city = st.text_input("مدينة البرنامج", value=default_city)
                col1, col2, col3 = st.columns(3)
                with col1:
                    pkg_days = st.number_input("عدد الأيام", min_value=1, max_value=60, value=default_days)
                with col2:
                    pkg_budget = st.number_input(
                        "الميزانية التقديرية (من الواقع)", min_value=100.0, max_value=50000.0,
                        value=default_budget, step=100.0
                    )
                with col3:
                    pkg_price_from = st.number_input(
                        "سعر البيع (ابتداءً من)", min_value=100.0, max_value=100000.0,
                        value=default_budget, step=100.0
                    )

                target_segment = st.selectbox(
                    "الفئة المستهدفة",
                    ["Individuals", "Families", "Groups", "VIP", "Umrah"],
                )

                base_hotel_label = st.selectbox(
                    "الفندق الأساسي في البرنامج (اختياري)",
                    list(hotel_options.keys()),
                )
                base_hotel_id = hotel_options[base_hotel_label]

                st.markdown("#### الأنشطة داخل البرنامج")
                if activities_df.empty:
                    st.info("لا توجد أنشطة مسجلة لهذه المدينة بعد.")
                    selected_activities_labels: List[str] = []
                else:
                    selected_activities_labels = st.multiselect(
                        "اختر الأنشطة",
                        activity_labels,
                    )

                pkg_status = st.selectbox("حالة البرنامج", ["Draft", "Active"])
                pkg_notes = st.text_area("ملاحظات إضافية (اختياري)")

                st.markdown("#### خطة الرحلة المرتبطة (للمراجعة)")
                st.code(default_plan_text or "لا توجد خطة محفوظة.", language="markdown")

                submitted_pkg = st.form_submit_button("💾 حفظ البرنامج")

            if submitted_pkg:
                if not pkg_name.strip():
                    st.error("اسم البرنامج مطلوب.")
                else:
                    activities_ids = [activity_map[lbl] for lbl in selected_activities_labels]
                    add_package(
                        name=pkg_name.strip(),
                        city=pkg_city.strip(),
                        days=int(pkg_days),
                        budget=float(pkg_budget),
                        base_hotel_id=base_hotel_id,
                        activities_ids=activities_ids,
                        ai_plan_text=default_plan_text,
                        target_segment=target_segment,
                        price_from_usd=float(pkg_price_from),
                        status=pkg_status,
                        notes=pkg_notes.strip(),
                        source_itinerary_id=source_itinerary_id,
                    )
                    st.success("✅ تم إنشاء البرنامج وحفظه في النظام.")
                    st.experimental_rerun()

    # قائمة البرامج
    with tab_list:
        st.subheader("قائمة البرامج المتاحة")

        packages_df = list_packages()
        if packages_df.empty:
            st.info("لا توجد برامج محفوظة حتى الآن.")
            return

        st.dataframe(packages_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        labels = []
        id_map: Dict[str, int] = {}
        for _, row in packages_df.iterrows():
            label = f"#{row['id']} — {row['name']} ({row['city']}, {row['days']} أيام)"
            labels.append(label)
            id_map[label] = int(row["id"])

        selected_pkg_label = st.selectbox("اختر برنامج لعرض التفاصيل", labels)

        if selected_pkg_label:
            pkg_id = id_map[selected_pkg_label]
            details = get_package(pkg_id)
            if not details:
                st.error("تعذر تحميل تفاصيل البرنامج.")
                return

            st.markdown("### تفاصيل البرنامج")
            st.write(f"📦 اسم البرنامج: **{details.get('name')}**")
            st.write(f"📍 المدينة: {details.get('city') or 'غير محددة'}")
            st.write(f"🗓️ عدد الأيام: {details.get('days')}")
            st.write(f"💰 الميزانية المرجعية: {details.get('budget')} USD")
            st.write(f"💵 سعر البيع (ابتداءً من): {details.get('price_from_usd')} USD")
            st.write(f"🎯 الفئة المستهدفة: {details.get('target_segment') or 'غير محددة'}")
            st.write(f"📊 الحالة: {details.get('status') or 'Draft'}")
            st.write(f"🕒 تم الإنشاء في: {details.get('created_at')}")

            if details.get("notes"):
                st.markdown("#### ملاحظات البرنامج")
                st.write(details["notes"])

            st.markdown("---")
            # الأنشطة المرتبطة
            activities_ids_str = details.get("activities_ids") or ""
            ids_list: List[int] = []
            if activities_ids_str.strip():
                try:
                    ids_list = [int(x) for x in activities_ids_str.split(",") if x.strip().isdigit()]
                except Exception:
                    ids_list = []

            if ids_list:
                st.markdown("#### الأنشطة المرتبطة بالبرنامج")
                df_acts = get_activities_by_ids(ids_list)
                if not df_acts.empty:
                    for _, row in df_acts.iterrows():
                        st.write(
                            f"- {row['name']} — {row['city']} ({row['category']}) "
                            f"— تقريباً {row['approx_price_usd']} USD"
                        )
                else:
                    st.info("لا يمكن تحميل تفاصيل الأنشطة المرتبطة.")
            else:
                st.info("لا توجد أنشطة مرتبطة لهذا البرنامج حالياً.")

            st.markdown("---")
            st.markdown("#### الخطة التفصيلية (من خطة الرحلة الأصلية)")
            st.write(details.get("ai_plan_text") or "لا توجد خطة مرتبطة.")


def page_booking_requests():
    render_header()
    st.title("📥 Booking Requests (Admin) — طلبات الحجز")

    st.write(
        "هنا يمكنك تسجيل ومراجعة طلبات الحجز (Leads) المرتبطة بالبرامج، الرحلات، العمرة، الطيران، القطار، الصحة، أو المستثمرين."
    )

    tab_new, tab_list = st.tabs(["طلب جديد يدوي", "قائمة الطلبات"])

    # طلب جديد يدوي
    with tab_new:
        st.subheader("تسجيل طلب حجز جديد (Manual)")

        packages_df = list_packages()
        itineraries_df = list_itineraries()

        pkg_options: Dict[str, Optional[int]] = {"بدون ربط ببرنامج محدد": None}
        if not packages_df.empty:
            for _, row in packages_df.iterrows():
                label = f"#{row['id']} — {row['name']} ({row['city']})"
                pkg_options[label] = int(row["id"])

        itin_options: Dict[str, Optional[int]] = {"بدون ربط بخطة محددة": None}
        if not itineraries_df.empty:
            for _, row in itineraries_df.iterrows():
                label = (
                    f"#{row['id']} — {row['traveller_name'] or 'بدون اسم'} "
                    f"({row['from_city']} → {row['destination_city']})"
                )
                itin_options[label] = int(row["id"])

        with st.form("new_booking_request"):
            col1, col2 = st.columns(2)
            with col1:
                traveller_name = st.text_input("اسم العميل *")
                traveller_email = st.text_input("البريد الإلكتروني (اختياري)")
                traveller_phone = st.text_input("رقم الهاتف *")
            with col2:
                from_city = st.text_input("مدينة/جهة الانطلاق", value="Cairo")
                to_city = st.text_input("الوجهة / نوع الخدمة", value="Riyadh")
                days = st.number_input("عدد الأيام (إن وجد)", min_value=0, max_value=60, value=0)
                budget = st.number_input(
                    "الميزانية التقريبية (دولار)", min_value=0.0, max_value=100000.0,
                    value=2500.0, step=100.0
                )

            st.markdown("#### ربط الطلب ببرنامج أو خطة (اختياري)")
            col3, col4 = st.columns(2)
            with col3:
                pkg_label = st.selectbox("ربط ببرنامج", list(pkg_options.keys()))
                package_id = pkg_options[pkg_label]
            with col4:
                itin_label = st.selectbox("ربط بخطة رحلة", list(itin_options.keys()))
                itinerary_id = itin_options[itin_label]

            source = st.selectbox(
                "مصدر الطلب",
                ["Web", "Mobile", "Agent", "Flights", "Rail", "Umrah/Hajj", "Investor", "Health/Insurance", "Local Service", "Other"],
            )
            status = st.selectbox(
                "حالة الطلب",
                ["New", "In Progress", "Confirmed", "Cancelled"],
            )

            notes = st.text_area("ملاحظات / تفاصيل إضافية")

            submitted_req = st.form_submit_button("💾 حفظ الطلب")

        if submitted_req:
            if not traveller_name.strip() or not traveller_phone.strip():
                st.error("اسم العميل ورقم الهاتف مطلوبان.")
            else:
                add_booking_request(
                    traveller_name=traveller_name.strip(),
                    traveller_email=traveller_email.strip(),
                    traveller_phone=traveller_phone.strip(),
                    from_city=from_city.strip(),
                    to_city=to_city.strip(),
                    days=int(days),
                    budget=float(budget),
                    notes=notes.strip(),
                    status=status,
                    source=source,
                    package_id=package_id,
                    itinerary_id=itinerary_id,
                )
                st.success("✅ تم حفظ طلب الحجز.")
                st.experimental_rerun()

    # قائمة الطلبات
    with tab_list:
        st.subheader("قائمة طلبات الحجز")

        df = list_booking_requests()
        if df.empty:
            st.info("لا توجد طلبات حجز مسجلة حتى الآن.")
            return

        # فلتر بسيط حسب المصدر والحالة
        col1, col2 = st.columns(2)
        with col1:
            source_filter = st.selectbox(
                "فلتر حسب المصدر",
                ["الكل"] + sorted(df["source"].dropna().unique().tolist()),
            )
        with col2:
            status_filter = st.selectbox(
                "فلتر حسب الحالة",
                ["الكل"] + sorted(df["status"].dropna().unique().tolist()),
            )

        df_filtered = df.copy()
        if source_filter != "الكل":
            df_filtered = df_filtered[df_filtered["source"] == source_filter]
        if status_filter != "الكل":
            df_filtered = df_filtered[df_filtered["status"] == status_filter]

        st.dataframe(df_filtered, use_container_width=True, hide_index=True)


def page_hotels_admin():
    render_header()
    st.title("🏨 Hotels & Contracts (Admin Demo)")

    st.write(
        "هذا القسم يوضّح كيف يمكن للمنصة إدارة الفنادق والعقود في الخلفية (Back-office)."
    )

    tab1, tab2 = st.tabs(["الفنادق", "العقود"])

    # الفنادق
    with tab1:
        st.subheader("إضافة فندق جديد")

        with st.form("add_hotel_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("اسم الفندق *")
                city = st.text_input("المدينة")
                country = st.text_input("الدولة", value="Saudi Arabia")

            with col2:
                contact_name = st.text_input("اسم مسؤول الاتصال")
                contact_email = st.text_input("البريد الإلكتروني لمسؤول الاتصال")
                contact_phone = st.text_input("رقم الهاتف")
                has_api = st.checkbox("لدى الفندق نظام حجز / Channel Manager / API؟")

            notes = st.text_area("ملاحظات إضافية (اختياري)")

            submitted_hotel = st.form_submit_button("حفظ الفندق")

        if submitted_hotel:
            if not name.strip():
                st.error("اسم الفندق مطلوب.")
            else:
                add_hotel(
                    name=name.strip(),
                    city=city.strip(),
                    country=country.strip(),
                    contact_name=contact_name.strip(),
                    contact_email=contact_email.strip(),
                    contact_phone=contact_phone.strip(),
                    has_api=has_api,
                    notes=notes.strip(),
                )
                st.success("✅ تم حفظ بيانات الفندق.")
                st.experimental_rerun()

        st.markdown("---")
        st.subheader("قائمة الفنادق المسجلة")

        hotels_df = list_hotels()
        if hotels_df.empty:
            st.info("لا توجد فنادق مسجلة بعد.")
        else:
            st.dataframe(hotels_df, use_container_width=True)

    # العقود
    with tab2:
        st.subheader("إنشاء عقد جديد")

        hotels_df = list_hotels()
        if hotels_df.empty:
            st.warning("يجب إضافة فندق واحد على الأقل قبل إنشاء عقد.")
        else:
            hotel_options = {
                f"{row['name']} (#{row['id']})": int(row["id"])
                for _, row in hotels_df.iterrows()
            }

            with st.form("add_contract_form"):
                hotel_label = st.selectbox("اختر الفندق", list(hotel_options.keys()))
                hotel_id = hotel_options[hotel_label]

                col1, col2 = st.columns(2)

                with col1:
                    contract_name = st.text_input("اسم العقد *", value="عقد توزيع غرف فندقية")
                    contract_type = st.selectbox(
                        "نوع العقد",
                        ["Net Rates", "Commission", "Hybrid", "Other"],
                    )
                    currency = st.text_input("العملة", value="USD")

                with col2:
                    valid_from = st.date_input("تاريخ بداية العقد", value=date.today())
                    valid_to = st.date_input(
                        "تاريخ نهاية العقد",
                        value=date(date.today().year + 1, 12, 31),
                    )

                payment_terms = st.text_area(
                    "شروط الدفع",
                    value="يتم السداد خلال 30 يومًا من تاريخ استلام الفاتورة.",
                )

                cancellation_policy = st.text_area(
                    "سياسة الإلغاء",
                    value="يمكن الإلغاء مجانًا حتى 48 ساعة قبل موعد الوصول، وبعد ذلك يتم خصم أول ليلة.",
                )

                notes = st.text_area("ملاحظات إضافية")

                submitted_contract = st.form_submit_button("حفظ العقد")

            if submitted_contract:
                if not contract_name.strip():
                    st.error("اسم العقد مطلوب.")
                else:
                    add_contract(
                        hotel_id=hotel_id,
                        contract_name=contract_name.strip(),
                        contract_type=contract_type,
                        currency=currency.strip(),
                        valid_from=str(valid_from),
                        valid_to=str(valid_to),
                        payment_terms=payment_terms.strip(),
                        cancellation_policy=cancellation_policy.strip(),
                        notes=notes.strip(),
                    )
                    st.success("✅ تم حفظ العقد.")
                    st.experimental_rerun()

        st.markdown("---")
        st.subheader("قائمة العقود")

        contracts_df = list_contracts()
        if contracts_df.empty:
            st.info("لا توجد عقود مسجلة بعد.")
        else:
            st.dataframe(contracts_df, use_container_width=True)


def page_ai_assistant():
    render_header()
    st.title("🤖 AI Assistant — HUMAIN Lifestyle")

    st.write(
        "اسأل المساعد عن أي شيء يخص السفر إلى السعودية، التخطيط، أو فكرة المنصة نفسها."
    )

    user_prompt = st.text_area("اكتب سؤالك أو فكرتك هنا", height=200)

    if st.button("💬 رد المساعد", type="primary"):
        if not user_prompt.strip():
            st.error("رجاءً اكتب شيئاً أولاً.")
        else:
            with st.spinner("جاري توليد الرد بالذكاء الاصطناعي..."):
                answer = ai_general_chat(user_prompt.strip())
            st.markdown("### ✍️ رد المساعد:")
            st.write(answer)

    st.markdown("---")
    st.caption(
        "هذا المساعد متصل حالياً بـ OpenAI فقط لأغراض العرض. "
        "يمكن ربطه لاحقاً بـ HUMAIN ONE / ALLAM أو نماذج أخرى."
    )


def page_flights():
    render_header()
    st.title("✈️ Flights to KSA — طلب حجز طيران")

    st.write(
        "نموذج تجريبي لتجميع طلبات حجز تذاكر طيران إلى السعودية. "
        "لاحقاً يمكن ربطه بنظام طيران (NDC / GDS)."
    )

    with st.form("flights_form"):
        col1, col2 = st.columns(2)
        with col1:
            from_city = st.text_input("مدينة الانطلاق", value="Cairo")
            to_city = st.selectbox(
                "مدينة الوصول داخل السعودية",
                [
                    "Riyadh",
                    "Jeddah",
                    "Makkah (via Jeddah)",
                    "Madina",
                    "Dammam",
                    "NEOM Region",
                ],
            )
            trip_type = st.selectbox("نوع الرحلة", ["ذهاب وعودة", "ذهاب فقط"])
        with col2:
            depart_date = st.date_input("تاريخ الذهاب", value=date.today())
            return_date = st.date_input("تاريخ العودة (إن وجد)", value=date.today())
            passengers = st.number_input("عدد المسافرين", min_value=1, max_value=9, value=1)

        travel_class = st.selectbox("الدرجة", ["اقتصادية", "ممتازة", "رجال أعمال", "أولى"])
        approx_budget = st.number_input(
            "الميزانية التقريبية (دولار)", min_value=100.0, max_value=20000.0,
            value=800.0, step=50.0
        )

        st.markdown("### بيانات التواصل")
        col3, col4 = st.columns(2)
        with col3:
            traveller_name = st.text_input("اسم العميل *")
            traveller_email = st.text_input("البريد الإلكتروني (اختياري)")
        with col4:
            traveller_phone = st.text_input("رقم الهاتف * (مع كود الدولة)")
            notes = st.text_area("ملاحظات إضافية (مثلاً خطوط مفضلة، أوقات معينة)")

        submitted = st.form_submit_button("📩 إرسال طلب الطيران")

    if submitted:
        if not traveller_name.strip() or not traveller_phone.strip():
            st.error("اسم العميل ورقم الهاتف مطلوبان.")
        else:
            full_to_city = f"{to_city} - {trip_type}, {passengers} pax, {travel_class}, {depart_date}"
            if trip_type == "ذهاب وعودة":
                full_to_city += f" / عودة: {return_date}"

            full_notes = f"[Flights Request] {notes or ''}"

            add_booking_request(
                traveller_name=traveller_name.strip(),
                traveller_email=traveller_email.strip(),
                traveller_phone=traveller_phone.strip(),
                from_city=from_city.strip(),
                to_city=full_to_city,
                days=0,
                budget=float(approx_budget),
                notes=full_notes,
                status="New",
                source="Flights",
                package_id=None,
                itinerary_id=None,
            )
            st.success("✅ تم استلام طلب الطيران، وسيتم التواصل معك عبر البيانات المسجّلة.")


def page_rail():
    render_header()
    st.title("🚄 Saudi Rail — طلب حجز قطار")

    st.write(
        "نموذج تجريبي لتجميع طلبات رحلات القطار داخل المملكة (SAR، الحرمين، وغيره مستقبلاً)."
    )

    with st.form("rail_form"):
        col1, col2 = st.columns(2)
        with col1:
            from_station = st.selectbox(
                "محطة الانطلاق",
                ["Riyadh", "Jeddah", "Makkah", "Madina", "Dammam", "Al Khobar", "Abha", "Tabuk"],
            )
            to_station = st.selectbox(
                "محطة الوصول",
                ["Riyadh", "Jeddah", "Makkah", "Madina", "Dammam", "Al Khobar", "Abha", "Tabuk"],
            )
        with col2:
            travel_date = st.date_input("تاريخ الرحلة", value=date.today())
            passengers = st.number_input("عدد الركّاب", min_value=1, max_value=9, value=1)

        seat_class = st.selectbox("الدرجة", ["اقتصادية", "درجة أولى", "أعمال"])
        approx_budget = st.number_input(
            "الميزانية التقريبية (دولار)", min_value=20.0, max_value=5000.0,
            value=150.0, step=10.0
        )

        st.markdown("### بيانات التواصل")
        col3, col4 = st.columns(2)
        with col3:
            traveller_name = st.text_input("اسم العميل *")
            traveller_email = st.text_input("البريد الإلكتروني (اختياري)")
        with col4:
            traveller_phone = st.text_input("رقم الهاتف * (مع كود الدولة)")
            notes = st.text_area("ملاحظات إضافية (مثلاً أوقات مفضلة، مقاعد معينة)")

        submitted = st.form_submit_button("📩 إرسال طلب القطار")

    if submitted:
        if not traveller_name.strip() or not traveller_phone.strip():
            st.error("اسم العميل ورقم الهاتف مطلوبان.")
        else:
            full_to_city = f"{from_station} → {to_station}, {passengers} pax, {seat_class}, {travel_date}"
            full_notes = f"[Rail Request] {notes or ''}"

            add_booking_request(
                traveller_name=traveller_name.strip(),
                traveller_email=traveller_email.strip(),
                traveller_phone=traveller_phone.strip(),
                from_city=from_station,
                to_city=full_to_city,
                days=0,
                budget=float(approx_budget),
                notes=full_notes,
                status="New",
                source="Rail",
                package_id=None,
                itinerary_id=None,
            )
            st.success("✅ تم استلام طلب القطار، وسيتم التواصل معك عبر البيانات المسجّلة.")


def page_umrah():
    render_header()
    st.title("🕋 Umrah & Hajj — طلب برنامج عمرة/حج")

    st.write(
        "هذه الصفحة لجمع طلبات برامج العمرة أو الحج (إقامة + نقل + خدمات إضافية). "
        "لاحقاً يمكن ربطها بمنصات رسمية (مثل نسك) وشركاء مرخّصين."
    )

    with st.form("umrah_form"):
        program_type = st.selectbox("نوع البرنامج", ["عمرة", "حج (مستقبلاً)", "عمرة + سياحة"])

        col1, col2 = st.columns(2)
        with col1:
            from_city = st.text_input("مدينة الانطلاق", value="Cairo")
            entry_city = st.selectbox(
                "مدينة الدخول للسعودية",
                ["Jeddah", "Makkah (via Jeddah)", "Madina", "Riyadh"],
            )
            nights_makkah = st.number_input("عدد الليالي في مكة", min_value=0, max_value=30, value=5)
        with col2:
            nights_madina = st.number_input("عدد الليالي في المدينة", min_value=0, max_value=30, value=3)
            total_guests = st.number_input("عدد الأفراد (بالغين + أطفال)", min_value=1, max_value=50, value=2)

        st.markdown("### تفضيلات السكن")
        hotel_pref = st.selectbox(
            "درجة السكن",
            ["اقتصادي قريب من الحرم", "متوسط", "5 نجوم قريب جداً من الحرم", "VIP / أجنحة خاصة"],
        )
        approx_budget = st.number_input(
            "الميزانية التقريبية للبرنامج (دولار لكل المجموعة)",
            min_value=300.0,
            max_value=50000.0,
            value=2500.0,
            step=100.0,
        )

        st.markdown("### بيانات التواصل")
        col3, col4 = st.columns(2)
        with col3:
            traveller_name = st.text_input("اسم مقدم الطلب *")
            traveller_email = st.text_input("البريد الإلكتروني (اختياري)")
        with col4:
            traveller_phone = st.text_input("رقم الهاتف * (مع كود الدولة)")
            notes = st.text_area("تفاصيل إضافية (مثلاً: تواريخ تقريبية، احتياجات خاصة، أطفال...)")

        submitted = st.form_submit_button("📩 إرسال طلب برنامج العمرة/الحج")

    if submitted:
        if not traveller_name.strip() or not traveller_phone.strip():
            st.error("اسم مقدم الطلب ورقم الهاتف مطلوبان.")
        else:
            total_nights = int(nights_makkah + nights_madina)
            full_to_city = f"{program_type} via {entry_city}, nights: Makkah {nights_makkah}, Madina {nights_madina}, guests {total_guests}"
            full_notes = f"[Umrah/Hajj Request] {hotel_pref}. {notes or ''}"

            add_booking_request(
                traveller_name=traveller_name.strip(),
                traveller_email=traveller_email.strip(),
                traveller_phone=traveller_phone.strip(),
                from_city=from_city.strip(),
                to_city=full_to_city,
                days=total_nights,
                budget=float(approx_budget),
                notes=full_notes,
                status="New",
                source="Umrah/Hajj",
                package_id=None,
                itinerary_id=None,
            )
            st.success("✅ تم استلام طلب برنامج العمرة/الحج، وسيتم التواصل معك عبر البيانات المسجّلة.")


def page_health_insurance():
    render_header()
    st.title("🏥 Health & Insurance — الصحة والتأمين")

    st.write(
        "هذه الصفحة لتجميع طلبات الخدمات الصحية والتأمين الصحي داخل المملكة "
        "(تأمين، مستشفيات، عيادات، فحوصات، واستشارات عن بعد)."
    )

    with st.form("health_form"):
        service_type = st.selectbox(
            "نوع الخدمة المطلوبة",
            ["تأمين صحي", "حجز مستشفى", "حجز عيادة", "فحص دوري", "استشارة طبية عن بعد"],
        )

        col1, col2 = st.columns(2)
        with col1:
            city = st.selectbox(
                "المدينة داخل المملكة",
                ["Riyadh", "Jeddah", "Makkah", "Madina", "Dammam", "Al Khobar", "Abha", "Tabuk", "NEOM Region", "Other"],
            )
            guests = st.number_input("عدد الأشخاص المشمولين بالخدمة", min_value=1, max_value=50, value=1)
        with col2:
            approx_budget = st.number_input(
                "الميزانية التقريبية (دولار، إن وجدت)",
                min_value=0.0,
                max_value=100000.0,
                value=0.0,
                step=50.0,
            )
            provider_pref = st.text_input("تفضيل مقدم خدمة (إن وجد)", value="")

        st.markdown("### تفاصيل الحالة / الطلب")
        details = st.text_area(
            "اشرح بإيجاز ما تحتاجه",
            help="مثال: تأمين لعائلة مكونة من 4 أفراد، أو حجز موعد مع طبيب قلب، أو فحص شامل، إلخ.",
        )

        st.markdown("### بيانات التواصل")
        col3, col4 = st.columns(2)
        with col3:
            contact_name = st.text_input("اسم مقدم الطلب *")
            contact_email = st.text_input("البريد الإلكتروني (اختياري)")
        with col4:
            contact_phone = st.text_input("رقم الهاتف * (مع كود الدولة)")
            from_city = st.text_input("مدينة الإقامة الحالية", value="")

        submitted = st.form_submit_button("📩 إرسال طلب صحي / تأمين")

    if submitted:
        if not contact_name.strip() or not contact_phone.strip():
            st.error("اسم مقدم الطلب ورقم الهاتف مطلوبان.")
        else:
            full_to_city = f"{service_type} in {city}, people={guests}, provider_pref={provider_pref or 'N/A'}"
            full_notes = f"[Health/Insurance Request] {details or ''}"

            add_booking_request(
                traveller_name=contact_name.strip(),
                traveller_email=contact_email.strip(),
                traveller_phone=contact_phone.strip(),
                from_city=from_city.strip() or "N/A",
                to_city=full_to_city,
                days=0,
                budget=float(approx_budget),
                notes=full_notes,
                status="New",
                source="Health/Insurance",
                package_id=None,
                itinerary_id=None,
            )
            st.success("✅ تم استلام طلب الصحة/التأمين، وسيتم التواصل معكم عبر البيانات المسجّلة.")


def page_investor_gateway():
    render_header()
    st.title("💼 Invest in KSA — بوابة المستثمرين")

    st.write(
        "هذه الصفحة مخصصة للمستثمرين وروّاد الأعمال الذين يرغبون في التواجد في المملكة "
        "(تأسيس شركة، استئجار مكتب، شقة، فتح حساب بنكي، وغيرها)."
    )

    with st.form("invest_form"):
        profile_type = st.selectbox("نوع العميل", ["فرد", "شركة / مؤسسة"])
        target_city = st.selectbox(
            "المدينة الرئيسية المستهدفة",
            ["Riyadh", "Jeddah", "Al Khobar", "Dammam", "NEOM Region", "Diriyah", "Other"],
        )

        st.markdown("### الخدمات المطلوبة")
        services = st.multiselect(
            "اختر كل ما ينطبق:",
            [
                "تأسيس شركة",
                "فتح سجل تجاري",
                "استئجار مكتب",
                "مساحات عمل مشتركة (Coworking)",
                "استئجار شقة سكنية",
                "فتح حساب بنكي",
                "استشارات قانونية / نظامية",
                "استقدام موظفين / تأشيرات عمل",
            ],
        )

        col1, col2 = st.columns(2)
        with col1:
            investment_budget = st.number_input(
                "الميزانية الاستثمارية التقريبية (دولار)",
                min_value=10000.0,
                max_value=10000000.0,
                value=50000.0,
                step=5000.0,
            )
        with col2:
            time_horizon = st.selectbox(
                "الإطار الزمني المتوقع للبدء",
                ["خلال 3 أشهر", "خلال 6 أشهر", "خلال سنة", "غير محدد"],
            )

        st.markdown("### بيانات التواصل")
        col3, col4 = st.columns(2)
        with col3:
            contact_name = st.text_input("اسم الشخص المسؤول *")
            contact_email = st.text_input("البريد الإلكتروني *")
        with col4:
            contact_phone = st.text_input("رقم الهاتف * (مع كود الدولة)")
            company_name = st.text_input("اسم الشركة (إن وجد)")

        notes = st.text_area(
            "تفاصيل إضافية عن المشروع / الاهتمامات",
            help="مثال: نشاط الشركة الحالي، القطاعات المستهدفة، نوع العقار المطلوب، حجم الفريق المتوقع...",
        )

        submitted = st.form_submit_button("📩 إرسال طلب استثمار")

    if submitted:
        if not contact_name.strip() or not contact_email.strip() or not contact_phone.strip():
            st.error("اسم المسؤول، البريد الإلكتروني، ورقم الهاتف مطلوبون.")
        else:
            services_str = ", ".join(services) if services else "لم يحدد"
            full_to_city = f"Invest in {target_city}, profile={profile_type}, horizon={time_horizon}"
            full_notes = f"[Investor Request] Company={company_name or 'N/A'}, Services={services_str}. {notes or ''}"

            add_booking_request(
                traveller_name=contact_name.strip(),
                traveller_email=contact_email.strip(),
                traveller_phone=contact_phone.strip(),
                from_city="Investor Origin (N/A)",
                to_city=full_to_city,
                days=0,
                budget=float(investment_budget),
                notes=full_notes,
                status="New",
                source="Investor",
                package_id=None,
                itinerary_id=None,
            )
            st.success("✅ تم استلام طلب المستثمر، وسيتم التواصل معكم عبر البيانات المسجّلة.")


# ==============================
# 7) توجيه الصفحات
# ==============================

st.sidebar.title("HUMAIN Lifestyle 🌍")
page = st.sidebar.radio(
    "اختر الصفحة",
    [
        "🏠 Home",
        "🧭 Trip Planner (B2C)",
        "🎟️ Experiences & Activities",
        "🏙️ Local Lifestyle & Services",
        "📝 Saved Itineraries",
        "📦 Packages / Programs",
        "✈️ Flights to KSA",
        "🚄 Saudi Rail",
        "🕋 Umrah & Hajj",
        "🏥 Health & Insurance",
        "💼 Invest in KSA",
        "📥 Booking Requests (Admin)",
        "🏨 Hotels & Contracts (Admin)",
        "🤖 AI Assistant",
    ],
)

if page.startswith("🏠"):
    page_home()
elif page.startswith("🧭"):
    page_trip_planner()
elif page.startswith("🎟️"):
    page_activities()
elif page.startswith("🏙️"):
    page_local_lifestyle()
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
elif page.startswith("🏥"):
    page_health_insurance()
elif page.startswith("💼"):
    page_investor_gateway()
elif page.startswith("📥"):
    page_booking_requests()
elif page.startswith("🏨"):
    page_hotels_admin()
elif page.startswith("🤖"):
    page_ai_assistant()
