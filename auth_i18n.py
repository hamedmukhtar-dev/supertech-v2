# auth_i18n.py
import os, sqlite3, hashlib, hmac
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Tuple
import streamlit as st

# ====== اختيار خوارزمية هاش آمنة بدون قيود 72 بايت ======
try:
    from passlib.hash import pbkdf2_sha256
except Exception:
    pbkdf2_sha256 = None  # fallback إذا passlib غير متاح

DB_PATH_DEFAULT = os.getenv("DB_PATH", "humain_lifestyle.db")

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

# ====== هاش/تحقق كلمات المرور ======
def _hash_pw(pw: str) -> str:
    pw = (pw or "").strip()
    if pbkdf2_sha256:
        # قوي وآمن—بدون حد 72 بايت
        return pbkdf2_sha256.hash(pw)
    # fallback بسيط
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def _verify_pw(pw: str, hashed: str) -> bool:
    pw = (pw or "").strip()
    if pbkdf2_sha256:
        try:
            return pbkdf2_sha256.verify(pw, hashed)
        except Exception:
            return False
    return hmac.compare_digest(hashlib.sha256(pw.encode("utf-8")).hexdigest(), hashed)

def create_user(email: str, password: str, role: str = "user"):
    with _conn(DB_PATH_DEFAULT) as c:
        cur = c.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO users(email, password_hash, role, created_at) VALUES(?,?,?,?)",
            (email.lower().strip(), _hash_pw(password), role, _now())
        )
        c.commit()

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

# -------- اللغة (i18n) --------
LANGS = {"ar": "العربية", "en": "English"}

def get_lang() -> str:
    return st.session_state.get("LANG", "ar")

def set_lang(lang: str):
    st.session_state["LANG"] = "ar" if lang not in LANGS else lang

def t(ar: str, en: str) -> str:
    return ar if get_lang() == "ar" else en

# -------- البوابة (تسجيل الدخول + اختيار اللغة) --------
def setup_defaults():
    ensure_auth_tables(DB_PATH_DEFAULT)
    # حسابات ديمو + حسابك
    create_user("admin@demo.local", "admin123", role="admin")
    create_user("demo@demo.local", "demo123", role="demo")
    create_user("hamed.mukhtar@daral-sd.com", os.getenv("DEFAULT_USER_PASSWORD", "Daral@2025"), role="admin")

def login_gate() -> bool:
    st.sidebar.markdown("### 🌐 Language | اللغة")
    lang = st.sidebar.selectbox(
        "Language",
        options=list(LANGS.keys()),
        format_func=lambda k: LANGS[k],
        index=0 if get_lang()=="ar" else 1
    )
    set_lang(lang)

    if st.session_state.get("AUTH_EMAIL"):
        return True

    st.markdown("---")
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
                return False
            st.session_state["AUTH_EMAIL"] = u[1]
            st.session_state["AUTH_ROLE"] = u[3]
            touch_last_login(u[1])
            _audit("login_success", u[1], f"role={u[3]}")
            st.experimental_rerun()

    with tabs[1]:
        n_email = st.text_input(t("البريد الإلكتروني", "Email"), key="new_email")
        n_pw = st.text_input(t("كلمة المرور", "Password"), type="password", key="new_pw")
        n_pw2 = st.text_input(t("تأكيد كلمة المرور", "Confirm password"), type="password", key="new_pw2")
        if st.button(t("إنشاء الحساب", "Create account")):
            if not n_email or not n_pw:
                st.error(t("رجاءً املأ كل الحقول.", "Please fill all fields."))
            elif n_pw != n_pw2:
                st.error(t("كلمتا المرور غير متطابقتين.", "Passwords do not match."))
            elif get_user(n_email):
                st.error(t("الحساب موجود بالفعل.", "Account already exists."))
            else:
                create_user(n_email, n_pw, role="user")
                _audit("signup", n_email, "")
                st.success(t("تم إنشاء الحساب. الرجاء تسجيل الدخول.", "Account created. Please sign in."))

    st.stop()

def signout_button():
    if st.sidebar.button("🔓 " + t("تسجيل خروج", "Sign out")):
        _audit("logout", st.session_state.get("AUTH_EMAIL"))
        for k in ["AUTH_EMAIL", "AUTH_ROLE"]:
            st.session_state.pop(k, None)
        st.experimental_rerun()

def track_page_view(page_name: str):
    _audit("page_view", st.session_state.get("AUTH_EMAIL"), page_name)
