# auth_i18n.py
import os, sqlite3, hashlib, hmac, smtplib
from email.message import EmailMessage
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Tuple
import streamlit as st

# ====== Password hashing (يدعم الطول>72 بايت) ======
try:
    from passlib.hash import bcrypt_sha256 as _bcrypt
except Exception:
    _bcrypt = None  # fallback إذا passlib غير متاح

DB_PATH_DEFAULT = "humain_lifestyle.db"

@contextmanager
def _conn(db_path: str):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

def ensure_auth_tables(db_path: str = DB_PATH_DEFAULT):
    with _conn(db_path) as c:
        cur = c.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TEXT NOT NULL,
                last_login_at TEXT
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                user_email TEXT,
                action TEXT NOT NULL,
                meta TEXT
            );
        """)
        c.commit()

def _now():
    return datetime.utcnow().isoformat()

def _audit(action: str, user_email: Optional[str] = None, meta: str = ""):
    try:
        with _conn(DB_PATH_DEFAULT) as c:
            cur = c.cursor()
            cur.execute(
                "INSERT INTO audit_logs(created_at, user_email, action, meta) VALUES(?,?,?,?)",
                (_now(), user_email, action, meta)
            )
            c.commit()
    except Exception:
        pass

# ====== Hash / Verify ======
def _hash_pw(pw: str) -> str:
    # enforce minimal policy
    if len(pw) < 6:
        raise ValueError("Password too short")
    if _bcrypt:
        # bcrypt_sha256 يتجاوز حدود 72-بايت تلقائياً
        return _bcrypt.hash(pw)
    # fallback بسيط
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def _verify_pw(pw: str, hashed: str) -> bool:
    if _bcrypt:
        try:
            return _bcrypt.verify(pw, hashed)
        except Exception:
            return False
    return hmac.compare_digest(hashlib.sha256(pw.encode("utf-8")).hexdigest(), hashed)

# ====== CRUD مستخدم ======
def create_user(email: str, password: str, role: str = "user") -> bool:
    email = email.lower().strip()
    hashed = _hash_pw(password)
    with _conn(DB_PATH_DEFAULT) as c:
        cur = c.cursor()
        try:
            cur.execute(
                "INSERT INTO users(email, password_hash, role, created_at) VALUES(?,?,?,?)",
                (email, hashed, role, _now())
            )
            c.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def get_user(email: str) -> Optional[Tuple[int, str, str, str, str, str]]:
    with _conn(DB_PATH_DEFAULT) as c:
        cur = c.cursor()
        cur.execute(
            "SELECT id, email, password_hash, role, created_at, last_login_at FROM users WHERE email=?",
            (email.lower().strip(),)
        )
        return cur.fetchone()

def touch_last_login(email: str):
    with _conn(DB_PATH_DEFAULT) as c:
        cur = c.cursor()
        cur.execute("UPDATE users SET last_login_at=? WHERE email=?", (_now(), email.lower().strip()))
        c.commit()

# ====== إعدادات اللغة ======
LANGS = {"ar": "العربية", "en": "English"}

def get_lang() -> str:
    return st.session_state.get("LANG", "ar")

def set_lang(lang: str):
    st.session_state["LANG"] = "ar" if lang not in LANGS else lang

def t(ar: str, en: str) -> str:
    return ar if get_lang() == "ar" else en

# ====== بريد ترحيبي ======
def _smtp_enabled() -> bool:
    return os.getenv("SEND_WELCOME_EMAIL", "0").strip() in ("1", "true", "True")

def send_welcome_email(to_email: str):
    if not _smtp_enabled():
        return
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USERNAME", "")
    pwd  = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", "HUMAIN Lifestyle <no-reply@humain.local>")
    use_tls = os.getenv("SMTP_TLS", "true").lower() in ("1", "true", "yes")

    if not (host and port and user and pwd):
        _audit("welcome_email_skipped", to_email, "missing_smtp_env")
        return

    msg = EmailMessage()
    msg["Subject"] = "Welcome to HUMAIN Lifestyle"
    msg["From"] = sender
    msg["To"] = to_email
    body_ar = (
        "مرحباً بك في HUMAIN Lifestyle!\n\n"
        "تم إنشاء حسابك بنجاح. يمكنك الآن تسجيل الدخول والبدء في استخدام المنصّة.\n"
        "إذا لم تقم بإنشاء هذا الحساب، يرجى تجاهل هذه الرسالة.\n\n"
        "تحياتنا،\nفريق HUMAIN Lifestyle"
    )
    body_en = (
        "Welcome to HUMAIN Lifestyle!\n\n"
        "Your account has been created successfully. You can now sign in and start using the platform.\n"
        "If you didn’t sign up, please ignore this email.\n\n"
        "Best,\nHUMAIN Lifestyle Team"
    )
    msg.set_content(body_ar + "\n\n---\n" + body_en)

    try:
        with smtplib.SMTP(host, port, timeout=20) as s:
            if use_tls:
                s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
        _audit("welcome_email_sent", to_email, "")
    except Exception as e:
        _audit("welcome_email_failed", to_email, str(e))

# ====== إعدادات افتراضية / إنشاء حسابات ديمو (اختياري) ======
def setup_defaults():
    ensure_auth_tables(DB_PATH_DEFAULT)
    # حسابات ديمو فقط للتجربة
    try:
        if not get_user("admin@demo.local"):
            create_user("admin@demo.local", "admin123", role="admin")
        if not get_user("demo@demo.local"):
            create_user("demo@demo.local", "demo123", role="demo")
        # حسابك الإداري (يمكن تغيير كلمة المرور من متغير بيئة)
        admin_pw = os.getenv("DEFAULT_USER_PASSWORD", "Daral@2025")
        if not get_user("hamed.mukhtar@daral-sd.com"):
            create_user("hamed.mukhtar@daral-sd.com", admin_pw, role="admin")
    except Exception as e:
        _audit("setup_defaults_error", None, str(e))

# ====== واجهة الدخول/التسجيل + اختيار اللغة ======
def login_gate() -> bool:
    # شعار وحقوق قبل أي محتوى
    st.markdown(
        """
<div style="display:flex;gap:12px;align-items:center;margin:8px 0 16px 0;">
  <img src="/app/static/logo" onerror="this.style.display='none'" alt="Logo" style="height:40px;border-radius:8px;border:1px solid #ddd;padding:4px;background:#fff" />
  <div>
    <div style="font-size:22px;font-weight:800;">HUMAIN Lifestyle — Live Demo</div>
    <div style="opacity:.85;">Dar AL Khartoum Travel And Tourism CO LTD — شركة دار الخرطوم للسفر والسياحة المحدودة</div>
  </div>
</div>
<hr style="opacity:.25;">
<div style="font-size:13px;opacity:.9;">
  <b>© 2025 HUMAIN Lifestyle</b> — {rights}
  <br>
  {disclaimer}
</div>
<hr style="opacity:.25;margin-bottom:8px;">
""".format(
            rights=t("جميع الحقوق محفوظة.", "All rights reserved"),
            disclaimer=t(
                "هذا نموذج عرض حي (Demo) لأغراض الاختبار والتقييم فقط. البيانات المعروضة تجريبية وقد لا تعكس أسعار/توفّر حقيقي. باستخدامك لهذه المنصة فأنت تقرّ بمسؤوليتك عن صحة البيانات المدخلة وقبولك لشروط الاستخدام وسياسة الخصوصية.",
                "This is a live demo for testing/evaluation purposes. Data shown is sample and may not reflect actual availability/prices. By using this platform, you accept responsibility for your inputs and agree to the Terms of Use and Privacy Policy.",
            ),
        ),
        unsafe_allow_html=True,
    )

    # لغة
    with st.sidebar:
        st.markdown("### 🌐 " + t("اللغة", "Language"))
        lang = st.selectbox(
            "Language | اللغة",
            options=list(LANGS.keys()),
            format_func=lambda k: LANGS[k],
            index=0 if get_lang()=="ar" else 1,
            key="LANG_SELECTBOX"
        )
        set_lang(lang)

    # إن كان مسجلاً
    if st.session_state.get("AUTH_EMAIL"):
        return True

    # واجهة الدخول/إنشاء حساب
    st.subheader(t("تسجيل الدخول", "Sign in"))
    tabs = st.tabs([t("دخول", "Login"), t("إنشاء حساب", "Create account")])

    with tabs[0]:
        email = st.text_input(t("البريد الإلكتروني", "Email"), key="login_email")
        pw = st.text_input(t("كلمة المرور", "Password"), type="password", key="login_pw")
        if st.button(t("دخول", "Login"), type="primary"):
            u = get_user(email)
            if not u or not _verify_pw(pw, u[2]):
                st.error(t("بيانات الدخول غير صحيحة.", "Invalid credentials."))
                _audit("login_failed", email, "bad_credentials")
            else:
                st.session_state["AUTH_EMAIL"] = u[1]
                st.session_state["AUTH_ROLE"] = u[3]
                touch_last_login(u[1])
                _audit("login_success", u[1], f"role={u[3]}")
                st.rerun()

    with tabs[1]:
        n_email = st.text_input(t("البريد الإلكتروني", "Email"), key="new_email")
        n_pw = st.text_input(t("كلمة المرور (6 أحرف على الأقل)", "Password (min 6 chars)"), type="password", key="new_pw")
        n_pw2 = st.text_input(t("تأكيد كلمة المرور", "Confirm password"), type="password", key="new_pw2")
        if st.button(t("إنشاء الحساب", "Create account")):
            if not n_email or not n_pw:
                st.error(t("رجاءً املأ كل الحقول.", "Please fill all fields."))
            elif len(n_pw) < 6:
                st.error(t("كلمة المرور قصيرة جداً (الحد الأدنى 6).", "Password too short (min 6)."))
            elif n_pw != n_pw2:
                st.error(t("كلمتا المرور غير متطابقتين.", "Passwords do not match."))
            elif get_user(n_email):
                st.error(t("الحساب موجود بالفعل.", "Account already exists."))
            else:
                try:
                    ok = create_user(n_email, n_pw, role="user")
                except ValueError:
                    ok = False
                if not ok:
                    st.error(t("تعذّر إنشاء الحساب. جرّب بريداً آخر.", "Could not create account. Try a different email."))
                else:
                    _audit("signup", n_email, "")
                    # أرسل الترحيب (إن كان SMTP مفعّل)
                    try:
                        send_welcome_email(n_email)
                    except Exception as e:
                        _audit("welcome_email_error", n_email, str(e))
                    st.success(t("تم إنشاء الحساب. الرجاء تسجيل الدخول.", "Account created. Please sign in."))

    # أوقف أي محتوى آخر حتى يسجّل
    st.stop()

def signout_button():
    if st.sidebar.button("🔓 " + t("تسجيل خروج", "Sign out")):
        _audit("logout", st.session_state.get("AUTH_EMAIL"))
        for k in ["AUTH_EMAIL", "AUTH_ROLE"]:
            st.session_state.pop(k, None)
        st.rerun()

def track_page_view(page_name: str):
    _audit("page_view", st.session_state.get("AUTH_EMAIL"), page_name)
# ====== Show full auth UI with layout wrapper ======
def show_auth_ui() -> bool:
    st.set_page_config(page_title="HUMAIN Lifestyle | Auth", layout="centered")
    setup_defaults()
    return login_gate()
# ====== Show full auth UI with layout wrapper ======
def show_auth_ui() -> bool:
    st.set_page_config(page_title="HUMAIN Lifestyle | Auth", layout="centered")
    setup_defaults()
    return login_gate()
