# auth_i18n.py
import os, sqlite3, hashlib, hmac
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Tuple
import streamlit as st
from email_utils import send_welcome_email  # <— جديد

try:
    from passlib.hash import bcrypt_sha256 as _bcrypt_sha256
except Exception:
    _bcrypt_sha256 = None
try:
    from passlib.hash import bcrypt
except Exception:
    bcrypt = None

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
    with _conn(DB_PATH_DEFAULT) as c:
        cur = c.cursor()
        cur.execute(
            "INSERT INTO audit_logs(created_at, user_email, action, meta) VALUES(?,?,?,?)",
            (_now(), user_email, action, meta)
        )
        c.commit()

def _hash_pw(pw: str) -> str:
    if _bcrypt_sha256:
        return _bcrypt_sha256.hash(pw)
    if bcrypt:
        pw = pw[:72]
        return bcrypt.hash(pw)
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def _verify_pw(pw: str, hashed: str) -> bool:
    if _bcrypt_sha256:
        try:
            return _bcrypt_sha256.verify(pw, hashed)
        except Exception:
            pass
    if bcrypt:
        try:
            return bcrypt.verify(pw[:72], hashed)
        except Exception:
            pass
    return hmac.compare_digest(hashlib.sha256(pw.encode("utf-8")).hexdigest(), hashed)

def create_user(email: str, password: str, role: str = "user"):
    with _conn(DB_PATH_DEFAULT) as c:
        cur = c.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO users(email, password_hash, role, created_at) VALUES(?,?,?,?)",
            (email.lower().strip(), _hash_pw(password), role, _now())
        )
        c.commit()

def upsert_user(email: str, password: str, role: str = "user") -> bool:
    """
    يرجّع True إذا كان INSERT (مستخدم جديد)، و False إذا كان UPDATE.
    """
    email_n = email.lower().strip()
    with _conn(DB_PATH_DEFAULT) as c:
        cur = c.cursor()
        cur.execute("SELECT id FROM users WHERE email=?", (email_n,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE users SET password_hash=?, role=? WHERE email=?",
                (_hash_pw(password), role, email_n)
            )
            c.commit()
            return False
        else:
            cur.execute(
                "INSERT INTO users(email, password_hash, role, created_at) VALUES(?,?,?,?)",
                (email_n, _hash_pw(password), role, _now())
            )
            c.commit()
            return True

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

LANGS = {"ar": "العربية", "en": "English"}

def get_lang() -> str:
    return st.session_state.get("LANG", "ar")

def set_lang(lang: str):
    st.session_state["LANG"] = "ar" if lang not in LANGS else lang

def t(ar: str, en: str) -> str:
    return ar if get_lang() == "ar" else en

def setup_defaults():
    ensure_auth_tables(DB_PATH_DEFAULT)
    create_user("admin@demo.local", "admin123", role="admin")
    create_user("demo@demo.local", "demo123", role="demo")
    upsert_user("hamed.mukhtar@daral-sd.com", os.getenv("DEFAULT_USER_PASSWORD", "Daral@2025"), role="admin")

def login_gate() -> bool:
    st.markdown(
        """
<div style='display:flex;align-items:center;gap:12px;margin:10px 0 6px 0'>
  <img src='https://raw.githubusercontent.com/hamedmukhtar-dev/supertech-v2/main/assets/logo.png' onerror="this.style.display='none'" style='height:36px;border-radius:6px;border:1px solid #ddd;padding:2px;background:#fff' />
  <div style='font-weight:700;font-size:18px'>HUMAIN Lifestyle — Live Demo</div>
</div>
<div style='font-size:12.5px;opacity:.9;margin-bottom:8px'>
 Dar AL Khartoum Travel And Tourism CO LTD — شركة دار الخرطوم للسفر والسياحة المحدودة
</div>
<hr style="margin:8px 0 14px 0"/>
<div style='font-size:12.5px;line-height:1.6;background:#fff9db;border:1px solid #f1e2a4;padding:10px;border-radius:8px;margin-bottom:10px'>
  <b>© 2025 HUMAIN Lifestyle — {rights}</b><br/>
  {legal}
</div>
        """.format(
            rights=t("جميع الحقوق محفوظة.", "All rights reserved"),
            legal=t(
                "هذا نموذج عرض حي (Demo) لأغراض الاختبار والتقييم فقط. البيانات المعروضة تجريبية وقد لا تعكس أسعار/توفّر حقيقي. باستخدامك لهذه المنصة فأنت تقرّ بمسؤوليتك عن صحة البيانات المدخلة وقبولك لشروط الاستخدام وسياسة الخصوصية.",
                "This is a live demo for testing/evaluation purposes. Data shown is sample and may not reflect actual availability/prices. By using this platform, you accept responsibility for your inputs and agree to the Terms of Use and Privacy Policy."
            ),
        ),
        unsafe_allow_html=True
    )

    st.sidebar.markdown("### 🌐 " + t("اللغة", "Language"))
    lang = st.sidebar.selectbox(
        "Language", options=list(LANGS.keys()),
        format_func=lambda k: LANGS[k],
        index=0 if get_lang()=="ar" else 1
    )
    set_lang(lang)

    if st.session_state.get("AUTH_EMAIL"):
        return True

    st.markdown("---")
    st.subheader(t("تسجيل الدخول", "Sign in"))

    tabs = st.tabs([t("دخول", "Login"), t("إنشاء حساب", "Create account")])

    allow_any = os.getenv("ALLOW_ANY_LOGIN", "0").strip() in ("1","true","True","yes","YES")

    # تبويب الدخول
    with tabs[0]:
        email = st.text_input(t("البريد الإلكتروني", "Email"), key="login_email")
        pw = st.text_input(t("كلمة المرور", "Password"), type="password", key="login_pw")
        if st.button(t("دخول", "Login"), type="primary"):
            if allow_any:
                if email and pw:
                    is_new = upsert_user(email, pw, role="user")
                    st.session_state["AUTH_EMAIL"] = email.lower().strip()
                    st.session_state["AUTH_ROLE"] = "user"
                    touch_last_login(email)
                    _audit("login_success", email, "allow_any=1")
                    # ابعت ترحيب عند أول مرة فقط
                    if os.getenv("EMAIL_ENABLED", "0") in ("1","true","True","YES","yes") and is_new:
                        send_welcome_email(email, get_lang())
                    st.rerun()
                else:
                    st.error(t("رجاءً أدخل البريد وكلمة المرور.", "Please enter email and password."))
            else:
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

    # تبويب إنشاء حساب
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
                created = upsert_user(n_email, n_pw, role="user")
                _audit("signup", n_email, "")
                # إرسال الترحيب بعد الإنشاء
                if os.getenv("EMAIL_ENABLED", "0") in ("1","true","True","YES","yes") and created:
                    send_welcome_email(n_email, get_lang())
                st.success(t("تم إنشاء الحساب. الرجاء تسجيل الدخول.", "Account created. Please sign in."))

    st.stop()

def signout_button():
    if st.sidebar.button("🔓 " + t("تسجيل خروج", "Sign out")):
        _audit("logout", st.session_state.get("AUTH_EMAIL"))
        for k in ["AUTH_EMAIL", "AUTH_ROLE"]:
            st.session_state.pop(k, None)
        st.rerun()

def track_page_view(page_name: str):
    _audit("page_view", st.session_state.get("AUTH_EMAIL"), page_name)
