# streamlit_app.py — HUMAIN Lifestyle (Live Demo with Auth + i18n)
import os, sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from typing import Dict, Any, List, Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from layout_header import render_header  # الهيدر + الشعار
from auth_i18n import login_gate, signout_button, setup_defaults, track_page_view, t

# ==============================
# 1) إعداد عام للتطبيق
# ==============================
st.set_page_config(page_title="HUMAIN Lifestyle", page_icon="🌍", layout="wide")
load_dotenv()

# تفعيل الحسابات الافتراضية والجداول الخاصة بالمصادقة
setup_defaults()
# بوابة الدخول + اختيار اللغة
if not login_gate():
    st.stop()

DB_PATH = os.getenv("DB_PATH", "humain_lifestyle.db")

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
        cur.execute("""
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
        """)

        # العقود
        cur.execute("""
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
        """)

        # الأنشطة/التجارب
        cur.execute("""
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
        """)

        # خطط الرحلات
        cur.execute("""
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
        """)

        # البرامج / Packages
        cur.execute("""
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
        """)

        # طلبات الحجز / Leads
        cur.execute("""
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
        """)

        conn.commit()

        # Seed للأنشطة إن كانت فارغة
        cur.execute("SELECT COUNT(*) FROM activities;")
        if cur.fetchone()[0] == 0:
            seed_activities = [
                # Riyadh
                ("Riyadh","Boulevard City Evening","Entertainment","زيارة بوليفارد سيتي مع مطاعم وعروض حية وتجارب ترفيهية مناسبة للعائلات والشباب.",150.0,"Riyadh Season Partner","https://example.com/riyadh-boulevard-city"),
                ("Riyadh","Boulevard World Discovery","Entertainment","تجربة عوالم وثقافات مختلفة في منطقة ترفيهية ضخمة مع فعاليات وعروض موسمية.",180.0,"Riyadh Season Partner","https://example.com/riyadh-boulevard-world"),
                ("Riyadh","Riyadh Desert Safari & Dunes","Adventure","رحلة سفاري في صحراء الرياض مع رمال، دبابات، وجلسة بدوية مع عشاء تقليدي.",220.0,"Desert Operator","https://example.com/riyadh-dunes"),
                ("Riyadh","Riyadh Zoo Family Day","Family","يوم عائلي في حديقة الحيوانات مع أنشطة للأطفال ومناطق ألعاب ومطاعم.",90.0,"Family Operator","https://example.com/riyadh-zoo"),
                ("Riyadh","CityWalk Riyadh Night","Leisure","جولة مسائية في CityWalk مع مطاعم وكافيهات وفعاليات موسمية مميزة.",110.0,"CityWalk Partner","https://example.com/riyadh-citywalk"),
                # Jeddah
                ("Jeddah","Jeddah Waterfront Evening Walk","Leisure","نزهة مسائية على واجهة جدة البحرية مع مطاعم بحرية وجلسات خارجية.",80.0,"Local Guide","https://example.com/jeddah-waterfront"),
                ("Jeddah","Red Sea Boat Trip","Adventure","رحلة قارب في البحر الأحمر مع سباحة أو سنوركلينج وجلسة بحرية.",260.0,"Red Sea Operator","https://example.com/jeddah-redsea-boat"),
                ("Jeddah","Historic Jeddah (Al Balad) Tour","Culture","جولة في جدة التاريخية مع زيارة البيوت القديمة والأسواق الشعبية.",130.0,"Heritage Guide","https://example.com/jeddah-albalad"),
                # Makkah
                ("Makkah","Umrah Program & City Tour","Religious","برنامج عمرة كامل مع نقل وإرشاد وزيارة لبعض المعالم في مكة المكرمة.",230.0,"Umrah Partner","https://example.com/makkah-umrah"),
                ("Makkah","Makkah Historical Sites Tour","Religious","زيارة بعض المواقع التاريخية المرتبطة بالسيرة النبوية حول مكة المكرمة.",150.0,"Religious Guide","https://example.com/makkah-historical"),
                # Madina
                ("Madina","Ziyarah of Madina Landmarks","Religious","زيارة عدد من المساجد والمعالم التاريخية في المدينة المنورة مع مرشد.",160.0,"Ziyarah Partner","https://example.com/madina-ziyarah"),
                ("Madina","Madina Night Markets Walk","Leisure","جولة في الأسواق والمناطق التجارية القريبة من المسجد النبوي.",70.0,"Local Guide","https://example.com/madina-markets"),
                # Dammam & Al Khobar
                ("Dammam","Dammam Corniche & Park","Leisure","جلسة على كورنيش الدمام مع حدائق وألعاب أطفال ومطاعم مطلة على الخليج.",60.0,"Local Operator","https://example.com/dammam-corniche"),
                ("Al Khobar","Al Khobar Waterfront & Skywalk","Leisure","نزهة في واجهة الخبر البحرية مع ممشى وسكاي ووك ومقاهي ومطاعم مميزة.",75.0,"Local Operator","https://example.com/khobar-waterfront"),
                ("Al Khobar","Family Entertainment Center Visit","Family","زيارة مركز ترفيهي مغلق للعائلات مع ألعاب إلكترونية وجلسات مريحة.",95.0,"Entertainment Center","https://example.com/khobar-family-center"),
                # Abha
                ("Abha","Abha Mountains & Cable Car","Nature","تجربة العربات المعلقة مع إطلالات على الجبال والقرى في مدينة أبها.",200.0,"Abha Operator","https://example.com/abha-cablecar"),
                ("Abha","Rijal Almaa Heritage Village Tour","Culture","زيارة قرية رجال ألمع التراثية واستكشاف الطراز المعماري الفريد.",170.0,"Heritage Guide","https://example.com/abha-rijal-almaa"),
                # Taif
                ("Taif","Taif Rose Farms Visit","Culture","زيارة مزارع الورد الطائفي والتعرف على صناعة ماء الورد والعطور.",140.0,"Rose Farm Partner","https://example.com/taif-roses"),
                ("Taif","Taif Cable Car & Mountains","Nature","جولة في جبال الهدا أو الشفا مع العربات المعلقة وإطلالات جميلة.",180.0,"Taif Operator","https://example.com/taif-cablecar"),
                # AlUla
                ("AlUla","AlUla Heritage & Nature Tour","Nature","جولة في المواقع الأثرية والطبيعية بالعلا مع مرشد محلي.",350.0,"AlUla Partner","https://example.com/alula-heritage"),
                ("AlUla","AlUla Stargazing Night","Adventure","ليلة تحت النجوم في صحراء العلا مع جلسة بدوية وشرح عن السماء.",320.0,"Stargazing Operator","https://example.com/alula-stargazing"),
                # Tabuk
                ("Tabuk","Tabuk Desert & Historical Tour","Adventure","زيارة بعض المواقع الطبيعية والتاريخية حول تبوك مع جولة في الصحراء.",260.0,"Tabuk Operator","https://example.com/tabuk-desert"),
                # NEOM
                ("NEOM Region","NEOM Future Discovery Tour (Concept)","Futuristic","تجربة تعريفية برؤية نيوم وزيارة بعض المواقع المفتوحة حالياً حسب الأنظمة.",400.0,"NEOM Experience","https://example.com/neom-discovery"),
                # Diriyah
                ("Diriyah","Diriyah Heritage District Walk","Culture","جولة في منطقة الدرعية التاريخية مع مسار للمشاة ومقاهي ومتاحف.",160.0,"Diriyah Operator","https://example.com/diriyah-heritage"),
            ]
            cur.executemany("""
                INSERT INTO activities
                (city, name, category, description, approx_price_usd, provider, booking_link)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, seed_activities)
            conn.commit()

init_db()

# ==============================
# 3) دوال CRUD
# ==============================
def add_hotel(name, city, country, contact_name, contact_email, contact_phone, has_api, notes):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO hotels
            (name, city, country, contact_name, contact_email, contact_phone, has_api, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, city, country, contact_name, contact_email, contact_phone, int(has_api), notes))
        conn.commit()

def list_hotels() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM hotels ORDER BY id DESC", conn)

def add_contract(hotel_id, contract_name, contract_type, currency, valid_from, valid_to, payment_terms, cancellation_policy, notes):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO contracts
            (hotel_id, contract_name, contract_type, currency, valid_from, valid_to, payment_terms, cancellation_policy, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (hotel_id, contract_name, contract_type, currency, valid_from, valid_to, payment_terms, cancellation_policy, notes))
        conn.commit()

def list_contracts() -> pd.DataFrame:
    q = """
    SELECT c.id, h.name AS hotel_name, c.contract_name, c.contract_type, c.currency,
           c.valid_from, c.valid_to, c.payment_terms, c.cancellation_policy, c.notes
    FROM contracts c JOIN hotels h ON c.hotel_id = h.id
    ORDER BY c.id DESC
    """
    with get_conn() as conn:
        return pd.read_sql_query(q, conn)

def list_activities(city_filter: Optional[str]=None, category_filter: Optional[str]=None) -> pd.DataFrame:
    base = "SELECT * FROM activities"
    params: List[Any] = []
    conds: List[str] = []
    if city_filter and city_filter != "الكل":
        conds.append("city = ?"); params.append(city_filter)
    if category_filter and category_filter != "الكل":
        conds.append("category = ?"); params.append(category_filter)
    if conds:
        base += " WHERE " + " AND ".join(conds)
    base += " ORDER BY city, category, name"
    with get_conn() as conn:
        return pd.read_sql_query(base, conn, params=params)

def get_activities_by_ids(ids: List[int]) -> pd.DataFrame:
    if not ids: return pd.DataFrame()
    placeholders = ",".join(["?"]*len(ids))
    q = f"SELECT * FROM activities WHERE id IN ({placeholders}) ORDER BY city, name"
    with get_conn() as conn:
        return pd.read_sql_query(q, conn, params=ids)

def save_itinerary(traveller_name, traveller_email, traveller_phone, form_data: Dict[str,Any], plan_text: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO itineraries (created_at, traveller_name, traveller_email, traveller_phone,
                                     from_city, destination_city, destination_country,
                                     days, budget, month, interests, plan_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            traveller_name, traveller_email, traveller_phone,
            form_data["from_city"], form_data["destination_city"], form_data["destination_country"],
            int(form_data["days"]), float(form_data["budget"]), form_data["month"],
            ", ".join(form_data["interests"]) if form_data["interests"] else "",
            plan_text,
        ))
        conn.commit()

def list_itineraries() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query("""
            SELECT id, created_at, traveller_name, traveller_email, traveller_phone,
                   from_city, destination_city, destination_country, days, budget, month, interests
            FROM itineraries ORDER BY datetime(created_at) DESC
        """, conn)

def get_itinerary(itinerary_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM itineraries WHERE id=?", (itinerary_id,))
        row = cur.fetchone()
        if not row: return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))

def add_package(name, city, days, budget, base_hotel_id, activities_ids: List[int],
                ai_plan_text, target_segment, price_from_usd, status, notes, source_itinerary_id):
    activities_str = ",".join(str(x) for x in activities_ids) if activities_ids else ""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO packages (created_at, name, city, days, budget, base_hotel_id, activities_ids,
                                  ai_plan_text, target_segment, price_from_usd, status, notes, source_itinerary_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(), name, city, days, budget, base_hotel_id, activities_str,
            ai_plan_text, target_segment, price_from_usd, status, notes, source_itinerary_id
        ))
        conn.commit()

def list_packages() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query("""
            SELECT id, created_at, name, city, days, budget, target_segment, price_from_usd, status, source_itinerary_id
            FROM packages ORDER BY datetime(created_at) DESC
        """, conn)

def get_package(package_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM packages WHERE id=?", (package_id,))
        row = cur.fetchone()
        if not row: return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))

def add_booking_request(traveller_name, traveller_email, traveller_phone, from_city, to_city,
                        days, budget, notes, status, source, package_id, itinerary_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO booking_requests (created_at, traveller_name, traveller_email, traveller_phone,
                from_city, to_city, days, budget, notes, status, source, package_id, itinerary_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(), traveller_name, traveller_email, traveller_phone,
            from_city, to_city, days, budget, notes, status, source, package_id, itinerary_id
        ))
        conn.commit()

def list_booking_requests() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query("""
            SELECT id, created_at, traveller_name, traveller_email, traveller_phone, from_city, to_city,
                   days, budget, notes, status, source, package_id, itinerary_id
            FROM booking_requests ORDER BY datetime(created_at) DESC
        """, conn)

# ==============================
# 4) تكامل OpenAI (خطة رحلات/دردشة)
# ==============================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    client = None

def _call_ai(instructions: str, user_input: str) -> str:
    if not client or not OPENAI_API_KEY:
        return ("⚠️ التكامل مع OpenAI غير مفعّل بعد.\n"
                "أضف OPENAI_API_KEY في إعدادات السيرفر.")
    try:
        resp = client.responses.create(model="gpt-4.1-mini", instructions=instructions, input=user_input)
        return (resp.output_text or "").strip()
    except Exception as e:
        return f"حدث خطأ أثناء الاتصال بـ OpenAI: {e}"

def ai_travel_plan(form_data: Dict[str, Any]) -> str:
    instructions = (
        "أنت مساعد سياحي احترافي يعمل ضمن منصة HUMAIN Lifestyle. "
        "اكتب خطة رحلة مفصلة ومقسّمة على أيام، داخل السعودية، بميزانية محددة وبأسلوب واضح."
    )
    user_prompt = f"""
المدينة الحالية: {form_data['from_city']}
الوجهة: {form_data['destination_city']}, {form_data['destination_country']}
عدد الأيام: {form_data['days']}
الميزانية (USD): {form_data['budget']}
شهر السفر: {form_data['month']}
الاهتمامات: {", ".join(form_data['interests']) if form_data['interests'] else "غير محددة"}

رجاءً:
- خطة يومية (Day 1, Day 2, …)
- توزيع تقريبي للميزانية
- تنبيهات (تأشيرة/مواسم/حجز مبكر)
اكتب بالعربية الفصحى المبسّطة.
"""
    return _call_ai(instructions, user_prompt)

def ai_general_chat(prompt: str) -> str:
    instructions = ("أنت مساعد داخل HUMAIN Lifestyle، تساعد المستخدم في التخطيط وشرح فكرة المنصة.")
    return _call_ai(instructions, prompt)

# ==============================
# 5) واجهات الصفحات
# ==============================
def footer_company():
    st.markdown("---")
    st.markdown(
        """
<div style="display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;">
  <div style="display:flex;gap:10px;align-items:center;">
    <img src="assets/logo.png" alt="Company Logo" style="height:36px;border-radius:8px;border:1px solid #D4AF37;padding:3px;background:white" />
    <div>
      <div style="font-weight:700;">Dar AL Khartoum Travel And Tourism CO LTD</div>
      <div style="opacity:.9;">شركة دار الخرطوم للسفر والسياحة المحدودة</div>
    </div>
  </div>
  <div style="line-height:1.3;font-size:14px;">
    <div>hamed mukhtar — <a href="mailto:hamed.mukhtar@daral-sd.com">hamed.mukhtar@daral-sd.com</a></div>
    <div>web: <a href="https://www.daral-sd.com" target="_blank">www.daral-sd.com</a></div>
    <div>Tel: +20 111 333 6672 — WhatsApp: +249 912 399 919</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

def page_home():
    track_page_view("Home")
    render_header()
    st.title("🌍 HUMAIN Lifestyle")
    st.caption("your gateway to KSA — منصّة ذكية تربط بين الزائر، المعتمر، والمستثمر")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
مرحباً بك في **HUMAIN Lifestyle** — نموذج (Live Demo) لمنصّة رقمية ذكية تجمع:
- **Travel & Leisure** (رحلات/أنشطة/فنادق)
- **Umrah & Hajj** (برامج متكاملة)
- **Invest in KSA** (بوابة المستثمرين)

> المستخدم يدخل من HUMAIN Lifestyle ثم **نحن** نوزّعه على أفضل مزوّدي الخدمات وفق الشراكات المستقبلية.
""")
    with col2:
        st.info(
            "ℹ️ **Demo Mode**\n\n"
            "- البيانات الحالية تجريبية.\n"
            "- كل الطلبات تُسجَّل كـ Leads.\n"
            "- البنية جاهزة للربط لاحقاً."
        )

    st.markdown("---")
    st.markdown("### 👥 الفئات المستهدفة")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### 🧳 Travelers & Visitors\n- تخطيط رحلة\n- أنشطة وتجارب\n- برامج جاهزة")
    with c2:
        st.markdown("#### 🕋 Pilgrims (Umrah & Hajj)\n- عمرة أو عمرة+سياحة\n- سكن ونقل وخدمات")
    with c3:
        st.markdown("#### 💼 Investors & Business\n- تأسيس شركة\n- مكاتب/شقق/بنوك\n- استقدام")

    st.markdown("---")
    st.markdown("""### 🔗 الأقسام
- 🧭 **Trip Planner (B2C)**
- 🎟️ **Experiences & Activities**
- 📝 **Saved Itineraries**
- 📦 **Packages / Programs**
- ✈️ **Flights to KSA** & 🚄 **Saudi Rail**
- 🕋 **Umrah & Hajj**
- 💼 **Invest in KSA**
- 🏙️ **Lifestyle**, 🩺 **Health & Insurance**, 🎓 **Education & Jobs**
- 📥 **Booking Requests (Admin)**, 🏨 **Hotels & Contracts (Admin)**
- 🤖 **AI Assistant**
""")
    footer_company()

def page_trip_planner():
    track_page_view("TripPlanner")
    render_header()
    st.title("🧭 Trip Planner (B2C) — مخطِّط رحلة ذكي")
    st.write("أدخل تفضيلاتك ودع المنصّة تقترح خطة رحلة متكاملة داخل السعودية.")

    with st.form("trip_form"):
        col1, col2 = st.columns(2)
        with col1:
            from_city = st.text_input("أين أنت الآن؟", value="Cairo")
            destination_country = st.text_input("الوجهة (الدولة)", value="Saudi Arabia")
            destination_city = st.selectbox("مدينة الوجهة", [
                "Riyadh","Jeddah","Makkah","Madina","Dammam","Al Khobar","Abha","Taif","AlUla","Tabuk","NEOM Region","Diriyah"
            ])
        with col2:
            budget = st.slider("الميزانية (USD)", 500, 10000, 2500, 100)
            days = st.slider("مدة الرحلة (أيام)", 3, 21, 7)
            month = st.selectbox("شهر السفر", ["غير محدد","يناير","فبراير","مارس","أبريل","مايو","يونيو","يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"])

        interests = st.multiselect("الاهتمامات", ["عمرة","سياحة دينية","تسوق","فعاليات ترفيهية","مباريات كرة","طبيعة وهدوء","مطاعم وتجارب طعام"])

        st.markdown("---")
        st.markdown("### حفظ الخطة (اختياري)")
        col3, col4 = st.columns(2)
        with col3:
            traveller_name = st.text_input("اسم المسافر")
            traveller_email = st.text_input("البريد الإلكتروني")
        with col4:
            traveller_phone = st.text_input("رقم الهاتف")
            save_plan_flag = st.checkbox("🔐 احفظ الخطة بعد توليدها")

        submitted = st.form_submit_button("✨ اقترح خطة")

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
        with st.spinner("جاري توليد الخطة..."):
            plan_text = ai_travel_plan(form_data)

        st.markdown("### ✈️ الخطة المقترحة")
        st.write(plan_text)

        if save_plan_flag and plan_text and not plan_text.startswith("⚠️"):
            save_itinerary(traveller_name.strip(), traveller_email.strip(), traveller_phone.strip(), form_data, plan_text)
            st.success("✅ تم حفظ الخطة.")
        elif save_plan_flag and plan_text.startswith("⚠️"):
            st.warning("لم يتم الحفظ لأن التكامل بالذكاء الاصطناعي غير مفعّل.")

        st.markdown("---")
        st.caption("هذه خطة تجريبية (Demo).")
    footer_company()

def page_activities():
    track_page_view("Activities")
    render_header()
    st.title("🎟️ Experiences & Activities — الأنشطة والتجارب")
    st.write("كتالوج تجريبي لأنشطة داخل مدن السعودية.")

    with get_conn() as conn:
        df_all = pd.read_sql_query("SELECT DISTINCT city FROM activities ORDER BY city;", conn)
        df_cat = pd.read_sql_query("SELECT DISTINCT category FROM activities ORDER BY category;", conn)

    cities = ["الكل"] + df_all["city"].tolist()
    categories = ["الكل"] + df_cat["category"].dropna().tolist()

    col1, col2 = st.columns(2)
    with col1:
        city_filter = st.selectbox("اختر المدينة", cities)
    with col2:
        category_filter = st.selectbox("اختر النوع", categories)

    df = list_activities(city_filter, category_filter)
    if df.empty:
        st.info("لا توجد أنشطة مطابقة.")
        footer_company(); return

    st.markdown("---")
    st.subheader("الأنشطة المتاحة")
    for _, row in df.iterrows():
        with st.expander(f"{row['name']} — {row['city']} ({row['category']})"):
            st.write(row["description"])
            c1, c2, c3 = st.columns([2,1,1])
            with c1:
                if row["approx_price_usd"]:
                    st.write(f"💰 السعر التقريبي: **{row['approx_price_usd']:.0f} USD**")
                else:
                    st.write("💰 غير محدد")
            with c2:
                if row["provider"]: st.write(f"🤝 المزوّد: {row['provider']}")
            with c3:
                if row["booking_link"]: st.link_button("رابط حجز (تجريبي)", row["booking_link"])
    footer_company()

def page_itineraries():
    track_page_view("Itineraries")
    render_header()
    st.title("📝 Saved Itineraries — خطط الرحلات المحفوظة")
    df = list_itineraries()
    if df.empty:
        st.info("لا توجد خطط محفوظة. جرّب Trip Planner.")
        footer_company(); return

    st.subheader("القائمة")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    labels = [f"#{row['id']} — {row['traveller_name'] or 'بدون اسم'} ({row['from_city']} → {row['destination_city']})" for _, row in df.iterrows()]
    selected_label = st.selectbox("اختر خطة", labels)
    if selected_label:
        try:
            selected_id = int(selected_label.split("—")[0].replace("#","").strip())
        except Exception:
            selected_id=None
        if selected_id:
            details = get_itinerary(selected_id)
            if not details:
                st.error("تعذر تحميل التفاصيل."); footer_company(); return
            st.markdown("### التفاصيل")
            st.write(f"👤: {details.get('traveller_name') or 'غير محدد'}")
            st.write(f"📧: {details.get('traveller_email') or 'غير محدد'}")
            st.write(f"📱: {details.get('traveller_phone') or 'غير محدد'}")
            st.write(f"✈️: {details.get('from_city')} → {details.get('destination_city')}, {details.get('destination_country')}")
            st.write(f"🗓️: {details.get('days')} يوم | 💰 {details.get('budget')} USD")
            st.write(f"🕒: {details.get('created_at')}")
            st.write(f"🎯: {details.get('interests') or 'غير محددة'}")
            st.markdown("---")
            st.markdown("### نص الخطة:")
            st.write(details.get("plan_text") or "")
    footer_company()

def page_packages():
    track_page_view("Packages")
    render_header()
    st.title("📦 Packages / Programs — برامج جاهزة للبيع")
    st.write("حوّل خطط الرحلات إلى برامج (Packages).")

    tab_create, tab_list = st.tabs(["إنشاء برنامج جديد","قائمة البرامج"])

    with tab_create:
        itineraries_df = list_itineraries()
        if itineraries_df.empty:
            st.info("لا توجد خطط محفوظة بعد.")
        else:
            st.subheader("1) اختر خطة كأساس")
            labels, id_mapping = [], {}
            for _, r in itineraries_df.iterrows():
                lb = f"#{r['id']} — {r['traveller_name'] or 'بدون اسم'} ({r['from_city']} → {r['destination_city']}, {r['days']} أيام)"
                labels.append(lb); id_mapping[lb]=int(r["id"])
            selected_label = st.selectbox("اختر خطة", labels)
            source_itinerary_id = id_mapping[selected_label]
            it = get_itinerary(source_itinerary_id)
            default_city = it["destination_city"] or ""
            default_days = int(it["days"] or 7)
            default_budget = float(it["budget"] or 2500.0)
            default_plan_text = it.get("plan_text") or ""

            st.markdown("---")
            st.subheader("2) تعريف البرنامج")
            hotels_df = list_hotels()
            hotel_options: Dict[str, Optional[int]] = {"بدون فندق محدد": None}
            if not hotels_df.empty:
                for _, r in hotels_df.iterrows():
                    hotel_options[f"{r['name']} ({r['city'] or ''})"] = int(r["id"])

            activities_df = list_activities(city_filter=default_city, category_filter=None)
            activity_labels, activity_map = [], {}
            for _, r in activities_df.iterrows():
                lbl = f"{r['name']} — {r['city']} ({r['category']})"
                activity_labels.append(lbl); activity_map[lbl]=int(r["id"])

            with st.form("create_package_form"):
                pkg_name = st.text_input("اسم البرنامج *", value=f"برنامج {default_city} {default_days} أيام")
                pkg_city = st.text_input("مدينة البرنامج", value=default_city)
                c1, c2, c3 = st.columns(3)
                with c1:
                    pkg_days = st.number_input("عدد الأيام", 1, 60, default_days)
                with c2:
                    pkg_budget = st.number_input("الميزانية المرجعية", 100.0, 50000.0, default_budget, 100.0)
                with c3:
                    pkg_price_from = st.number_input("سعر البيع (ابتداءً من)", 100.0, 100000.0, default_budget, 100.0)

                target_segment = st.selectbox("الفئة المستهدفة", ["Individuals","Families","Groups","VIP","Umrah"])
                base_hotel_label = st.selectbox("الفندق الأساسي (اختياري)", list(hotel_options.keys()))
                base_hotel_id = hotel_options[base_hotel_label]

                st.markdown("#### الأنشطة")
                selected_activities_labels = st.multiselect("اختر الأنشطة", activity_labels) if not activities_df.empty else []

                pkg_status = st.selectbox("الحالة", ["Draft","Active"])
                pkg_notes = st.text_area("ملاحظات")
                st.markdown("#### الخطة المرتبطة (للمراجعة)")
                st.code(default_plan_text or "لا توجد خطة.", language="markdown")
                submitted_pkg = st.form_submit_button("💾 حفظ البرنامج")

            if submitted_pkg:
                if not pkg_name.strip():
                    st.error("اسم البرنامج مطلوب.")
                else:
                    activities_ids = [activity_map[lbl] for lbl in selected_activities_labels]
                    add_package(pkg_name.strip(), pkg_city.strip(), int(pkg_days), float(pkg_budget),
                                base_hotel_id, activities_ids, default_plan_text, target_segment,
                                float(pkg_price_from), pkg_status, pkg_notes.strip(), source_itinerary_id)
                    st.success("✅ تم إنشاء البرنامج.")
                    st.experimental_rerun()

    with tab_list:
        st.subheader("قائمة البرامج")
        packages_df = list_packages()
        if packages_df.empty:
            st.info("لا توجد برامج محفوظة بعد.")
            footer_company(); return

        st.dataframe(packages_df, use_container_width=True, hide_index=True)
        st.markdown("---")
        labels, id_map = [], {}
        for _, r in packages_df.iterrows():
            lb = f"#{r['id']} — {r['name']} ({r['city']}, {r['days']} أيام)"
            labels.append(lb); id_map[lb]=int(r["id"])
        selected_pkg_label = st.selectbox("اختر برنامج", labels)
        if selected_pkg_label:
            details = get_package(id_map[selected_pkg_label])
            if not details:
                st.error("تعذر تحميل تفاصيل البرنامج."); footer_company(); return
            st.markdown("### تفاصيل البرنامج")
            st.write(f"📦 {details.get('name')}")
            st.write(f"📍 {details.get('city') or 'غير محددة'}")
            st.write(f"🗓️ {details.get('days')} يوم")
            st.write(f"💰 ميزانية مرجعية: {details.get('budget')} USD")
            st.write(f"💵 سعر البيع من: {details.get('price_from_usd')} USD")
            st.write(f"🎯 الفئة: {details.get('target_segment') or 'غير محددة'}")
            st.write(f"📊 الحالة: {details.get('status') or 'Draft'}")
            st.write(f"🕒 الإنشاء: {details.get('created_at')}")
            if details.get("notes"):
                st.markdown("#### ملاحظات"); st.write(details["notes"])
            st.markdown("---")
            ids_list: List[int] = []
            ids_str = (details.get("activities_ids") or "").strip()
            if ids_str:
                try: ids_list = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
                except Exception: ids_list = []
            if ids_list:
                st.markdown("#### أنشطة مرتبطة")
                df_acts = get_activities_by_ids(ids_list)
                if not df_acts.empty:
                    for _, r in df_acts.iterrows():
                        st.write(f"- {r['name']} — {r['city']} ({r['category']}) — ~{r['approx_price_usd']} USD")
                else:
                    st.info("لا يمكن تحميل تفاصيل الأنشطة.")
            else:
                st.info("لا توجد أنشطة مرتبطة.")
            st.markdown("---")
            st.markdown("#### الخطة التفصيلية")
            st.write(details.get("ai_plan_text") or "لا توجد خطة.")
    footer_company()

def page_booking_requests():
    track_page_view("BookingRequests")
    render_header()
    st.title("📥 Booking Requests (Admin) — طلبات الحجز")
    st.write("تسجيل ومراجعة طلبات الحجز (Leads).")

    tab_new, tab_list = st.tabs(["طلب جديد يدوي","قائمة الطلبات"])
    with tab_new:
        st.subheader("تسجيل طلب جديد")
        packages_df, itineraries_df = list_packages(), list_itineraries()
        pkg_options: Dict[str, Optional[int]] = {"بدون ربط ببرنامج": None}
        if not packages_df.empty:
            for _, r in packages_df.iterrows():
                pkg_options[f"#{r['id']} — {r['name']} ({r['city']})"] = int(r["id"])
        itin_options: Dict[str, Optional[int]] = {"بدون ربط بخطة": None}
        if not itineraries_df.empty:
            for _, r in itineraries_df.iterrows():
                itin_options[f"#{r['id']} — {r['traveller_name'] or 'بدون اسم'} ({r['from_city']} → {r['destination_city']})"] = int(r["id"])

        with st.form("new_booking_request"):
            c1, c2 = st.columns(2)
            with c1:
                traveller_name = st.text_input("اسم العميل *")
                traveller_email = st.text_input("البريد الإلكتروني")
                traveller_phone = st.text_input("رقم الهاتف *")
            with c2:
                from_city = st.text_input("مدينة الانطلاق", value="Cairo")
                to_city = st.text_input("الوجهة", value="Riyadh")
                days = st.number_input("عدد الأيام", 1, 60, 7)
                budget = st.number_input("الميزانية (USD)", 100.0, 100000.0, 2500.0, 100.0)
            st.markdown("#### الربط (اختياري)")
            c3, c4 = st.columns(2)
            with c3:
                pkg_label = st.selectbox("برنامج", list(pkg_options.keys())); package_id = pkg_options[pkg_label]
            with c4:
                itin_label = st.selectbox("خطة رحلة", list(itin_options.keys())); itinerary_id = itin_options[itin_label]
            source = st.selectbox("مصدر الطلب", ["Web","Mobile","Agent","Flights","Rail","Umrah/Hajj","Investor","Lifestyle","Health/Insurance","Education/Jobs","Other"])
            status = st.selectbox("الحالة", ["New","In Progress","Confirmed","Cancelled"])
            notes = st.text_area("ملاحظات")
            submitted_req = st.form_submit_button("💾 حفظ الطلب")

        if submitted_req:
            if not traveller_name.strip() or not traveller_phone.strip():
                st.error("الاسم ورقم الهاتف مطلوبان.")
            else:
                add_booking_request(traveller_name.strip(), traveller_email.strip(), traveller_phone.strip(),
                                    from_city.strip(), to_city.strip(), int(days), float(budget),
                                    notes.strip(), status, source, package_id, itinerary_id)
                st.success("✅ تم حفظ الطلب.")
                st.experimental_rerun()

    with tab_list:
        st.subheader("القائمة")
        df = list_booking_requests()
        if df.empty:
            st.info("لا توجد طلبات بعد."); footer_company(); return
        c1, c2 = st.columns(2)
        with c1:
            source_filter = st.selectbox("فلتر المصدر", ["الكل"] + sorted(df["source"].dropna().unique().tolist()))
        with c2:
            status_filter = st.selectbox("فلتر الحالة", ["الكل"] + sorted(df["status"].dropna().unique().tolist()))
        df_f = df.copy()
        if source_filter != "الكل": df_f = df_f[df_f["source"]==source_filter]
        if status_filter != "الكل": df_f = df_f[df_f["status"]==status_filter]
        st.dataframe(df_f, use_container_width=True, hide_index=True)
    footer_company()

def page_hotels_admin():
    track_page_view("HotelsContracts")
    render_header()
    st.title("🏨 Hotels & Contracts (Admin Demo)")
    st.write("إدارة الفنادق والعقود (Back-office).")

    tab1, tab2 = st.tabs(["الفنادق","العقود"])
    with tab1:
        st.subheader("إضافة فندق")
        with st.form("add_hotel_form"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("اسم الفندق *")
                city = st.text_input("المدينة")
                country = st.text_input("الدولة", value="Saudi Arabia")
            with c2:
                contact_name = st.text_input("اسم مسؤول الاتصال")
                contact_email = st.text_input("البريد الإلكتروني")
                contact_phone = st.text_input("رقم الهاتف")
                has_api = st.checkbox("هل لديه API/Channel Manager؟")
            notes = st.text_area("ملاحظات")
            submitted_hotel = st.form_submit_button("حفظ")

        if submitted_hotel:
            if not name.strip():
                st.error("اسم الفندق مطلوب.")
            else:
                add_hotel(name.strip(), city.strip(), country.strip(),
                          contact_name.strip(), contact_email.strip(), contact_phone.strip(),
                          has_api, notes.strip())
                st.success("✅ تم الحفظ.")
                st.experimental_rerun()

        st.markdown("---"); st.subheader("قائمة الفنادق")
        hotels_df = list_hotels()
        if hotels_df.empty: st.info("لا توجد فنادق.")
        else: st.dataframe(hotels_df, use_container_width=True)

    with tab2:
        st.subheader("إنشاء عقد")
        hotels_df = list_hotels()
        if hotels_df.empty:
            st.warning("أضف فندقاً أولاً.")
        else:
            hotel_options = {f"{r['name']} (#{r['id']})": int(r["id"]) for _, r in hotels_df.iterrows()}
            with st.form("add_contract_form"):
                hotel_label = st.selectbox("الفندق", list(hotel_options.keys()))
                hotel_id = hotel_options[hotel_label]
                c1, c2 = st.columns(2)
                with c1:
                    contract_name = st.text_input("اسم العقد *", value="عقد توزيع غرف فندقية")
                    contract_type = st.selectbox("نوع العقد", ["Net Rates","Commission","Hybrid","Other"])
                    currency = st.text_input("العملة", value="USD")
                with c2:
                    valid_from = st.date_input("بداية العقد", value=date.today())
                    valid_to = st.date_input("نهاية العقد", value=date(date.today().year+1, 12, 31))
                payment_terms = st.text_area("شروط الدفع", value="السداد خلال 30 يوماً من الفاتورة.")
                cancellation_policy = st.text_area("سياسة الإلغاء", value="إلغاء مجاني حتى 48 ساعة قبل الوصول.")
                notes = st.text_area("ملاحظات")
                submitted_contract = st.form_submit_button("حفظ العقد")

            if submitted_contract:
                if not contract_name.strip():
                    st.error("اسم العقد مطلوب.")
                else:
                    add_contract(hotel_id, contract_name.strip(), contract_type, currency.strip(),
                                 str(valid_from), str(valid_to), payment_terms.strip(),
                                 cancellation_policy.strip(), notes.strip())
                    st.success("✅ تم الحفظ.")
                    st.experimental_rerun()
        st.markdown("---"); st.subheader("قائمة العقود")
        contracts_df = list_contracts()
        if contracts_df.empty: st.info("لا توجد عقود.")
        else: st.dataframe(contracts_df, use_container_width=True)
    footer_company()

def page_ai_assistant():
    track_page_view("AI_Assistant")
    render_header()
    st.title("🤖 AI Assistant — HUMAIN Lifestyle")
    st.write("اسأل المساعد عن التخطيط وفكرة المنصة.")
    user_prompt = st.text_area("اكتب سؤالك هنا", height=200)
    if st.button("💬 رد المساعد", type="primary"):
        if not user_prompt.strip():
            st.error("اكتب شيئاً أولاً.")
        else:
            with st.spinner("جاري التوليد..."):
                ans = ai_general_chat(user_prompt.strip())
            st.markdown("### ✍️ الرد:")
            st.write(ans)
    st.caption("متصل حالياً بـ OpenAI لأغراض العرض.")
    footer_company()

def page_flights():
    track_page_view("Flights")
    render_header()
    st.title("✈️ Flights to KSA — طلب حجز طيران")
    st.write("نموذج لتجميع طلبات الطيران (Lead Capture).")

    with st.form("flights_form"):
        c1, c2 = st.columns(2)
        with c1:
            from_city = st.text_input("مدينة الانطلاق", value="Cairo")
            to_city = st.selectbox("مدينة الوصول", ["Riyadh","Jeddah","Makkah (via Jeddah)","Madina","Dammam","NEOM Region"])
            trip_type = st.selectbox("نوع الرحلة", ["ذهاب وعودة","ذهاب فقط"])
        with c2:
            depart_date = st.date_input("تاريخ الذهاب", value=date.today())
            return_date = st.date_input("تاريخ العودة", value=date.today())
            passengers = st.number_input("عدد المسافرين", 1, 9, 1)
        travel_class = st.selectbox("الدرجة", ["اقتصادية","ممتازة","رجال أعمال","أولى"])
        approx_budget = st.number_input("الميزانية (USD)", 100.0, 20000.0, 800.0, 50.0)
        st.markdown("### بيانات التواصل")
        c3, c4 = st.columns(2)
        with c3:
            traveller_name = st.text_input("اسم العميل *")
            traveller_email = st.text_input("البريد الإلكتروني")
        with c4:
            traveller_phone = st.text_input("رقم الهاتف *")
            notes = st.text_area("ملاحظات")
        submitted = st.form_submit_button("📩 إرسال الطلب")

    if submitted:
        if not traveller_name.strip() or not traveller_phone.strip():
            st.error("اسم العميل ورقم الهاتف مطلوبان.")
        else:
            full_to_city = f"{to_city} - {trip_type}, {passengers} pax, {travel_class}, {depart_date}"
            if trip_type == "ذهاب وعودة":
                full_to_city += f" / عودة: {return_date}"
            add_booking_request(
                traveller_name.strip(), traveller_email.strip(), traveller_phone.strip(),
                from_city.strip(), full_to_city, 0, float(approx_budget),
                f"[Flights Request] {notes or ''}", "New", "Flights", None, None
            )
            st.success("✅ تم استلام الطلب وسيتم التواصل معك.")
    footer_company()

def page_rail():
    track_page_view("Rail")
    render_header()
    st.title("🚄 Saudi Rail — طلب حجز قطار")
    st.write("تجميع طلبات رحلات القطار داخل المملكة.")
    with st.form("rail_form"):
        c1, c2 = st.columns(2)
        with c1:
            from_station = st.selectbox("محطة الانطلاق", ["Riyadh","Jeddah","Makkah","Madina","Dammam","Al Khobar","Abha","Tabuk"])
            to_station = st.selectbox("محطة الوصول", ["Riyadh","Jeddah","Makkah","Madina","Dammam","Al Khobar","Abha","Tabuk"])
        with c2:
            travel_date = st.date_input("تاريخ الرحلة", value=date.today())
            passengers = st.number_input("عدد الركّاب", 1, 9, 1)
        seat_class = st.selectbox("الدرجة", ["اقتصادية","درجة أولى","أعمال"])
        approx_budget = st.number_input("الميزانية (USD)", 20.0, 5000.0, 150.0, 10.0)
        st.markdown("### بيانات التواصل")
        c3, c4 = st.columns(2)
        with c3:
            traveller_name = st.text_input("اسم العميل *")
            traveller_email = st.text_input("البريد الإلكتروني")
        with c4:
            traveller_phone = st.text_input("رقم الهاتف *")
            notes = st.text_area("ملاحظات")
        submitted = st.form_submit_button("📩 إرسال الطلب")

    if submitted:
        if not traveller_name.strip() or not traveller_phone.strip():
            st.error("اسم العميل ورقم الهاتف مطلوبان.")
        else:
            full_to_city = f"{from_station} → {to_station}, {passengers} pax, {seat_class}, {travel_date}"
            add_booking_request(
                traveller_name.strip(), traveller_email.strip(), traveller_phone.strip(),
                from_station, full_to_city, 0, float(approx_budget),
                f"[Rail Request] {notes or ''}", "New", "Rail", None, None
            )
            st.success("✅ تم استلام الطلب.")
    footer_company()

def page_umrah():
    track_page_view("Umrah")
    render_header()
    st.title("🕋 Umrah & Hajj — طلب برنامج عمرة/حج")
    st.write("تجميع طلبات برامج العمرة (تمهيداً للتكامل لاحقاً).")
    with st.form("umrah_form"):
        program_type = st.selectbox("نوع البرنامج", ["عمرة","حج (مستقبلاً)","عمرة + سياحة"])
        c1, c2 = st.columns(2)
        with c1:
            from_city = st.text_input("مدينة الانطلاق", value="Cairo")
            entry_city = st.selectbox("مدينة الدخول", ["Jeddah","Makkah (via Jeddah)","Madina","Riyadh"])
            nights_makkah = st.number_input("ليالي مكة", 0, 30, 5)
        with c2:
            nights_madina = st.number_input("ليالي المدينة", 0, 30, 3)
            total_guests = st.number_input("عدد الأفراد", 1, 50, 2)
        hotel_pref = st.selectbox("درجة السكن", ["اقتصادي قريب من الحرم","متوسط","5 نجوم قريب جداً","VIP / أجنحة"])
        approx_budget = st.number_input("الميزانية (USD / المجموعة)", 300.0, 50000.0, 2500.0, 100.0)
        st.markdown("### بيانات التواصل")
        c3, c4 = st.columns(2)
        with c3:
            traveller_name = st.text_input("اسم مقدم الطلب *")
            traveller_email = st.text_input("البريد الإلكتروني")
        with c4:
            traveller_phone = st.text_input("رقم الهاتف *")
            notes = st.text_area("تفاصيل إضافية")
        submitted = st.form_submit_button("📩 إرسال الطلب")
    if submitted:
        if not traveller_name.strip() or not traveller_phone.strip():
            st.error("الاسم ورقم الهاتف مطلوبان.")
        else:
            total_nights = int(nights_makkah + nights_madina)
            to_city = f"{program_type} via {entry_city}, nights: Makkah {nights_makkah}, Madina {nights_madina}, guests {total_guests}"
            add_booking_request(
                traveller_name.strip(), traveller_email.strip(), traveller_phone.strip(),
                from_city.strip(), to_city, total_nights, float(approx_budget),
                f"[Umrah/Hajj Request] {hotel_pref}. {notes or ''}", "New", "Umrah/Hajj", None, None
            )
            st.success("✅ تم استلام الطلب.")
    footer_company()

def page_investor_gateway():
    track_page_view("InvestorGateway")
    render_header()
    st.title("💼 Invest in KSA — بوابة المستثمرين")
    st.write("بوابة موحدة للمستثمرين (تأسيس/مكاتب/شقق/بنوك/استقدام).")
    with st.form("invest_form"):
        profile_type = st.selectbox("نوع العميل", ["فرد","شركة / مؤسسة"])
        target_city = st.selectbox("المدينة", ["Riyadh","Jeddah","Al Khobar","Dammam","NEOM Region","Diriyah","Other"])
        services = st.multiselect("الخدمات المطلوبة", [
            "تأسيس شركة","فتح سجل تجاري","استئجار مكتب","مساحات عمل مشتركة",
            "استئجار شقة سكنية","فتح حساب بنكي","استشارات قانونية / نظامية","استقدام موظفين / تأشيرات عمل"
        ])
        c1, c2 = st.columns(2)
        with c1:
            investment_budget = st.number_input("الميزانية (USD)", 10000.0, 10000000.0, 50000.0, 5000.0)
        with c2:
            time_horizon = st.selectbox("الإطار الزمني", ["خلال 3 أشهر","خلال 6 أشهر","خلال سنة","غير محدد"])
        st.markdown("### بيانات التواصل")
        c3, c4 = st.columns(2)
        with c3:
            contact_name = st.text_input("اسم المسؤول *")
            contact_email = st.text_input("البريد الإلكتروني *")
        with c4:
            contact_phone = st.text_input("رقم الهاتف *")
            company_name = st.text_input("اسم الشركة")
        notes = st.text_area("تفاصيل إضافية")
        submitted = st.form_submit_button("📩 إرسال الطلب")
    if submitted:
        if not contact_name.strip() or not contact_email.strip() or not contact_phone.strip():
            st.error("الاسم، البريد، الهاتف مطلوبة.")
        else:
            services_str = ", ".join(services) if services else "لم يحدد"
            to_city = f"Invest in {target_city}, profile={profile_type}, horizon={time_horizon}"
            full_notes = f"[Investor Request] Company={company_name or 'N/A'}, Services={services_str}. {notes or ''}"
            add_booking_request(
                contact_name.strip(), contact_email.strip(), contact_phone.strip(),
                "Investor Origin (N/A)", to_city, 0, float(investment_budget),
                full_notes, "New", "Investor", None, None
            )
            st.success("✅ تم استلام طلب المستثمر.")
    footer_company()

def page_lifestyle():
    track_page_view("Lifestyle")
    render_header()
    st.title("🏙️ Local Lifestyle & Services — نمط الحياة والخدمات")
    st.write("طلب خدمات الحياة اليومية داخل المملكة.")
    with st.form("lifestyle_form"):
        c1, c2 = st.columns(2)
        with c1:
            city = st.selectbox("المدينة", ["Riyadh","Jeddah","Makkah","Madina","Dammam","Al Khobar","Abha","Taif","AlUla","Tabuk","NEOM Region","Diriyah","Other"])
            service_categories = st.multiselect("نوع الخدمات", [
                "سوبرماركت / هايبرماركت","أثاث منزلي / مكتبي","إلكترونيات وجوالات","مطاعم وكافيهات",
                "صالات رياضية / نوادي","أنشطة أطفال / ترفيه عائلي","سيارات (تأجير / خدمات)","خدمات تنظيف / صيانة منزلية",
                "صالونات وتجميل","خدمات مجتمعية / أندية","أخرى"
            ])
        with c2:
            approx_budget = st.number_input("الميزانية التقريبية (SAR/USD)", 0.0, 100000.0, 0.0, 100.0)
            urgency = st.selectbox("متى تحتاجها؟", ["خلال أسبوع","خلال شهر","أستكشف الخيارات"])
        details = st.text_area("اشرح احتياجك")
        st.markdown("### بيانات التواصل")
        c3, c4 = st.columns(2)
        with c3:
            name = st.text_input("اسمك *")
            email = st.text_input("البريد الإلكتروني")
        with c4:
            phone = st.text_input("رقم الهاتف *")
            current_city = st.text_input("مكانك الحالي", value="Cairo")
        submitted = st.form_submit_button("📩 إرسال الطلب")
    if submitted:
        if not name.strip() or not phone.strip():
            st.error("الاسم ورقم الهاتف مطلوبان.")
        else:
            services_str = ", ".join(service_categories) if service_categories else "لم يحدد"
            to_city = f"Lifestyle in {city} | Services: {services_str} | Urgency: {urgency}"
            add_booking_request(
                name.strip(), email.strip(), phone.strip(), current_city.strip(), to_city, 0, float(approx_budget),
                f"[Lifestyle Request] {details or ''}", "New", "Lifestyle", None, None
            )
            st.success("✅ تم استلام الطلب.")
    footer_company()

def page_health_insurance():
    track_page_view("HealthInsurance")
    render_header()
    st.title("🩺 Health & Insurance — الصحة والتأمين")
    st.write("تجميع طلبات التأمين/الصحة.")
    with st.form("health_form"):
        request_type = st.selectbox("نوع الطلب", [
            "تأمين صحي فردي","تأمين صحي عائلي","تأمين صحي لشركة / موظفين","تأمين سفر للسعودية",
            "حجز مستشفى / عيادة","فحوصات شاملة (Check-up)","رأي طبي ثانٍ (Second Opinion)"
        ])
        c1, c2 = st.columns(2)
        with c1:
            target_city = st.selectbox("المدينة/Any", ["Riyadh","Jeddah","Makkah","Madina","Dammam","Al Khobar","Abha","Tabuk","NEOM Region","Any"])
            coverage_for = st.selectbox("التغطية لـ", ["فرد","عائلة","شركة / فريق عمل"])
        with c2:
            approx_budget = st.number_input("الميزانية (USD/ SAR)", 0.0, 100000.0, 1000.0, 100.0)
            time_frame = st.selectbox("بداية التغطية", ["خلال شهر","خلال 3 أشهر","غير محدد"])
        details = st.text_area("تفاصيل إضافية")
        st.markdown("### بيانات التواصل")
        c3, c4 = st.columns(2)
        with c3:
            name = st.text_input("الاسم *")
        with c4:
            email = st.text_input("البريد الإلكتروني *")
        phone = st.text_input("رقم الهاتف *")
        current_country = st.text_input("الدولة/المدينة الحالية", value="Sudan / Egypt")
        submitted = st.form_submit_button("📩 إرسال الطلب")
    if submitted:
        if not name.strip() or not email.strip() or not phone.strip():
            st.error("الاسم، البريد، الهاتف مطلوبة.")
        else:
            to_city = f"{request_type} in {target_city}, coverage={coverage_for}, start={time_frame}"
            add_booking_request(
                name.strip(), email.strip(), phone.strip(), current_country.strip(), to_city, 0, float(approx_budget),
                f"[Health/Insurance Request] {details or ''}", "New", "Health/Insurance", None, None
            )
            st.success("✅ تم استلام الطلب.")
    footer_company()

def page_education_jobs():
    track_page_view("EducationJobs")
    render_header()
    st.title("🎓 Education & Jobs — التعليم وفرص العمل")
    st.write("قبول جامعي/كورسات/وظائف داخل السعودية.")
    with st.form("edu_jobs_form"):
        request_type = st.selectbox("نوع الطلب", [
            "قبول جامعي في السعودية","كورسات / دورات تدريبية","تعلم اللغة العربية / الإنجليزية",
            "فرص عمل داخل السعودية","تدريب / Internship","منح دراسية / Scholarships"
        ])
        c1, c2 = st.columns(2)
        with c1:
            target_city = st.selectbox("المدينة/أونلاين", ["Riyadh","Jeddah","Makkah","Madina","Dammam","Al Khobar","Online / Remote","Any"])
            level = st.selectbox("المستوى الحالي", ["خريج ثانوي","طالب جامعي","خريج جامعة","خبرة 1-3 سنوات","خبرة 3-7 سنوات","خبرة أكثر من 7 سنوات"])
        with c2:
            field = st.text_input("التخصص/المجال")
            approx_budget = st.number_input("ميزانية التعليم/الكورسات", 0.0, 50000.0, 0.0, 100.0)
        details = st.text_area("تفاصيل إضافية")
        st.markdown("### بيانات التواصل")
        c3, c4 = st.columns(2)
        with c3:
            name = st.text_input("الاسم *")
            email = st.text_input("البريد الإلكتروني *")
        with c4:
            phone = st.text_input("رقم الهاتف *")
            current_country = st.text_input("الدولة/المدينة الحالية", value="Sudan / Egypt")
        submitted = st.form_submit_button("📩 إرسال الطلب")
    if submitted:
        if not name.strip() or not email.strip() or not phone.strip():
            st.error("الاسم، البريد، الهاتف مطلوبة.")
        else:
            to_city = f"{request_type} in {target_city}, level={level}, field={field or 'N/A'}"
            add_booking_request(
                name.strip(), email.strip(), phone.strip(), current_country.strip(), to_city, 0, float(approx_budget),
                f"[Education/Jobs Request] {details or ''}", "New", "Education/Jobs", None, None
            )
            st.success("✅ تم استلام الطلب.")
    footer_company()

# ==============================
# 6) توجيه الصفحات + صلاحيات + خروج + تتبّع
# ==============================
st.sidebar.title("HUMAIN Lifestyle 🌍")

PAGES = {
    "🏠 Home": page_home,
    "🧭 Trip Planner (B2C)": page_trip_planner,
    "🎟️ Experiences & Activities": page_activities,
    "📝 Saved Itineraries": page_itineraries,
    "📦 Packages / Programs": page_packages,
    "✈️ Flights to KSA": page_flights,
    "🚄 Saudi Rail": page_rail,
    "🕋 Umrah & Hajj": page_umrah,
    "💼 Invest in KSA": page_investor_gateway,
    "🏙️ Local Lifestyle & Services": page_lifestyle,
    "🩺 Health & Insurance": page_health_insurance,
    "🎓 Education & Jobs": page_education_jobs,
    "🤖 AI Assistant": page_ai_assistant,
    # Admin-only
    "📥 Booking Requests (Admin)": page_booking_requests,
    "🏨 Hotels & Contracts (Admin)": page_hotels_admin,
}

role = st.session_state.get("AUTH_ROLE","user")
PUBLIC_LABELS = [
    "🏠 Home","🧭 Trip Planner (B2C)","🎟️ Experiences & Activities","📝 Saved Itineraries",
    "📦 Packages / Programs","✈️ Flights to KSA","🚄 Saudi Rail","🕋 Umrah & Hajj",
    "💼 Invest in KSA","🏙️ Local Lifestyle & Services","🩺 Health & Insurance",
    "🎓 Education & Jobs","🤖 AI Assistant",
]
ADMIN_ONLY = ["📥 Booking Requests (Admin)","🏨 Hotels & Contracts (Admin)"]
labels = PUBLIC_LABELS + (ADMIN_ONLY if role in ("admin",) else [])
page = st.sidebar.radio(t("اختر الصفحة","Choose page"), labels)

# زر تسجيل الخروج
signout_button()

# تتبع المشاهدة
try:
    track_page_view(page)
except Exception:
    pass

# استدعاء الصفحة
PAGES[page]()
