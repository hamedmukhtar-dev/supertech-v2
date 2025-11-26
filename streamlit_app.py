import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Dict, Any, List

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# ==============================
# 1) إعداد عام للتطبيق
# ==============================

st.set_page_config(
    page_title="HUMAIN Lifestyle",
    page_icon="🌍",
    layout="wide",
)

load_dotenv()  # قراءة OPENAI_API_KEY من .env (لو موجود)

APP_TITLE = "HUMAIN Lifestyle — Travel & Entertainment Super Platform"

# ==============================
# 2) إعداد قاعدة البيانات (SQLite بسيطة)
# ==============================

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

        # جدول الفنادق (للاستخدام الإداري حالياً)
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

        # جدول العقود البسيط
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

        conn.commit()


init_db()

# ==============================
# 3) CRUD للفنادق والعقود
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


# ==============================
# 4) تكامل بسيط مع OpenAI (الموديل قابل للتبديل لاحقاً مع HUMAIN)
# ==============================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

try:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    client = None


def _call_ai(instructions: str, user_input: str) -> str:
    """استدعاء موحّد لـ OpenAI (لاحقاً نستبدل بـ HUMAIN بسهولة)."""
    if not client or not OPENAI_API_KEY:
        return (
            "⚠️ التكامل مع OpenAI غير مفعّل بعد.\n"
            "رجاءً أضف مفتاح OPENAI_API_KEY في ملف .env على السيرفر أو الجهاز المحلي."
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
        "اكتب بنود عقود أو سياسات إلغاء أو شروط دفع بصياغة عربية احترافية، مختصرة وواضحة. "
        "إن أمكن، قسّم النص إلى فقرات أو نقاط."
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
    st.title("🌍 HUMAIN Lifestyle")
    st.subheader("منصة ذكية للسفر والترفيه — من الفكرة إلى التجربة، في مكان واحد.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            """
مرحباً بك في **HUMAIN Lifestyle** — نموذج أولي (Live Demo) لمنصة B2C ذكية:

- تخطيط رحلات إلى السعودية (وخارجها لاحقاً) حسب **الميزانية والاهتمامات**.
- إدارة عقود الفنادق والتكامل مع مزودي الخدمات (API Ready).
- دمج الذكاء الاصطناعي (اليوم عبر OpenAI، وغداً عبر HUMAIN ONE و ALLAM).

هذه النسخة مهيّأة لتكون **عرض توضيحي (Demo)** يمكن مشاركته مع:
- المستثمرين
- HUMAIN
- الشركاء في قطاع السياحة والترفيه.
"""
        )

    with col2:
        st.info(
            "**وضع العرض (Demo Mode)**\n\n"
            "- لا توجد بعد تكاملات حقيقية مع خطوط طيران أو منصات ترفيه.\n"
            "- كل شيء معدّ ليعرض *كيف ستكون تجربة المنصة* للمستخدم النهائي.\n"
            "- يمكن تطوير التكاملات لاحقاً (Flights, Hotels, Events APIs)."
        )

    st.markdown("---")
    st.markdown("### جرّب الآن 👇")
    st.markdown(
        "- من القائمة الجانبية اختر **🧭 Trip Planner (B2C)** لتجربة تخطيط رحلة.\n"
        "- أو ادخل إلى **🏨 Hotels & Contracts (Admin)** لاستكشاف إدارة الفنادق.\n"
        "- أو افتح **🤖 AI Assistant** للتحاور مع المساعد الذكي."
    )


def page_trip_planner():
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
                ["Makkah", "Madina", "Jeddah", "Riyadh", "AlUla", "NEOM Region"],
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

        st.markdown("---")
        st.caption(
            "هذه خطة تجريبية (Demo) مبنية على الذكاء الاصطناعي فقط، "
            "وليست مرتبطة بعد بأنظمة حجز حقيقية."
        )


def page_hotels_admin():
    st.title("🏨 Hotels & Contracts (Admin Demo)")

    st.write(
        "هذا القسم استعراضي للمستثمرين/الشركاء، يوضح كيف تدير المنصة "
        "فنادقك وعقودك في الخلفية (Back-office)."
    )

    tab1, tab2 = st.tabs(["الفنادق", "العقود"])

    # --- الفنادق ---
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

    # --- العقود ---
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


# ==============================
# 6) توجيه الصفحات
# ==============================

st.sidebar.title("HUMAIN Lifestyle 🌍")
page = st.sidebar.radio(
    "اختر الصفحة",
    [
        "🏠 Home",
        "🧭 Trip Planner (B2C)",
        "🏨 Hotels & Contracts (Admin)",
        "🤖 AI Assistant",
    ],
)

if page.startswith("🏠"):
    page_home()
elif page.startswith("🧭"):
    page_trip_planner()
elif page.startswith("🏨"):
    page_hotels_admin()
elif page.startswith("🤖"):
    page_ai_assistant()
