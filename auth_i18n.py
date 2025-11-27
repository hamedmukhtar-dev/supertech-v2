# auth_i18n.py — Light Login + Language Gateway + Auto-Provision
import os, sqlite3, hashlib, hmac, base64
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path
import streamlit as st

DB_PATH_DEFAULT = "humain_lifestyle.db"
ALLOW_ANY_LOGIN = os.getenv("ALLOW_ANY_LOGIN", "0") == "1"  # إذا =1 يقبل أي باسورد (للعرض فقط)

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

def _now(): return datetime.utcnow().isoformat()

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

# ====== Password hashing (SHA-256 ديمو) ======
def _hash_pw(pw: str) -> str:
    return hashlib.sha256((pw or "").encode("utf-8")).hexdigest()
def _verify_pw(pw: str, hashed: str) -> bool:
    return hmac.compare_digest(_hash_pw(pw), hashed)

def create_user(email: str, password: str, role: str = "user"):
    with _conn(DB_PATH_DEFAULT) as c:
        cur = c.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO users(email, password_hash, role, created_at) VALUES(?,?,?,?)",
            (email.lower().strip(), _hash_pw(password), role, _now())
        )
        c.commit()

def upsert_user(email: str, password: str, role: str = "user"):
    """إنشاء أو تحديث كلمة المرور لو الحساب موجود (للديمو)."""
    with _conn(DB_PATH_DEFAULT) as c:
        cur = c.cursor()
        cur.execute("SELECT id FROM users WHERE email=?",(email.lower().strip(),))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE users SET password_hash=? WHERE email=?", (_hash_pw(password), email.lower().strip()))
        else:
            cur.execute(
                "INSERT INTO users(email, password_hash, role, created_at) VALUES(?,?,?,?)",
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

# ====== i18n ======
LANGS = {"ar": "العربية", "en": "English"}
def get_lang() -> str: return st.session_state.get("LANG", "ar")
def set_lang(lang: str): st.session_state["LANG"] = lang if lang in LANGS else "ar"
def t(ar: str, en: str) -> str: return ar if get_lang() == "ar" else en

# ====== Seed ======
def setup_defaults():
    ensure_auth_tables(DB_PATH_DEFAULT)
    # حسابات ديمو
    create_user("admin@demo.local", os.getenv("ADMIN_DEMO_PW", "admin123"), role="admin")
    create_user("demo@demo.local", os.getenv("DEMO_DEMO_PW", "demo123"), role="demo")
    create_user("hamed.mukhtar@daral-sd.com", os.getenv("DEFAULT_USER_PASSWORD", "Daral@2025"), role="admin")

# ====== UI helpers ======
def _read_logo_as_base64():
    p = Path("assets/logo.png")
    if p.exists():
        try:
            return base64.b64encode(p.read_bytes()).decode("utf-8")
        except Exception:
            return None
    return None

def _login_css():
    # نسخة Light بيضاء بالكامل + خط واضح
    st.markdown(
        """
<style>
:root{
  --gold:#C8A646; --green:#0D7A45; --bg:#ffffff; --card:#ffffff; --text:#101418; --muted:#677181; --border:#E6E8EF;
}
html, body, .stApp { background: var(--bg) !important; color: var(--text) !important; }
* { font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Noto Kufi Arabic", "Cairo", Arial, "Apple Color Emoji", "Segoe UI Emoji" !important; }
.humain-wrap{ min-height:100vh; display:flex; align-items:center; justify-content:center; padding:28px; background:#fff; }
.humain-card{
  width:min(980px,94vw); background: var(--card);
  border:1px solid var(--border);
  box-shadow: 0 20px 50px rgba(16,20,24,.06);
  border-radius:18px; padding:22px 22px 16px;
}
.h-header{ display:flex; align-items:center; gap:16px; padding:8px 4px 16px; border-bottom:1px dashed #e8e6da; }
.h-logo{ height:58px; width:58px; border-radius:12px; border:1px solid var(--gold); background:#fff; overflow:hidden; display:flex; align-items:center; justify-content:center;}
.h-title h1{ margin:0; font-size:1.6rem; color:#1a1f2a; font-weight:800; letter-spacing:.2px;}
.h-title p{ margin:4px 0 0; color:var(--muted); font-size:.98rem;}
.h-body{ display:grid; gap:18px; grid-template-columns:1.05fr .95fr; padding-top:18px;}
.h-left{ padding-right:12px;}
.h-legal{
  border:1px solid var(--border); background:linear-gradient(180deg, #ffffff, #fcfcfd);
  border-radius:12px; padding:14px; color:#273142; font-size:.98rem;
}
.h-legal strong{ color:#1a1f2a; }
.h-divider{ height:1px; background:#efe9d5; margin:14px 0;}
.h-right{ border-left:1px dashed #e8e6da; padding-left:14px;}
.h-form{
  border:1px solid var(--border);
  background:linear-gradient(180deg, #ffffff, #fbfcff);
  border-radius:12px; padding:16px;
}
.h-form h3{ margin-top:0; color:#1a1f2a;}
.h-foot{
  margin-top:12px; padding-top:12px; border-top:1px dashed #e8e6da;
  display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; color:#3b4556; font-size:.92rem;
}
.h-company{ display:flex; gap:10px; align-items:center;}
.h-company .mini-logo{ height:28px; width:28px; border-radius:8px; border:1px solid var(--gold); background:#fff; overflow:hidden;}
.h-muted{ color:var(--muted);}
@media (max-width: 880px){ .h-body{ grid-template-columns:1fr;} .h-right{ border-left:none; padding-left:0;} }
</style>
        """,
        unsafe_allow_html=True
    )

def _language_selector():
    lang = st.selectbox(
        "Language | اللغة",
        options=list(LANGS.keys()),
        index=0 if get_lang()=="ar" else 1,
        format_func=lambda k: LANGS[k]
    )
    set_lang(lang)

def signout_button():
    if st.sidebar.button("🔓 " + t("تسجيل خروج", "Sign out")):
        _audit("logout", st.session_state.get("AUTH_EMAIL"))
        for k in ["AUTH_EMAIL", "AUTH_ROLE"]:
            st.session_state.pop(k, None)
        st.experimental_rerun()

def track_page_view(page_name: str):
    _audit("page_view", st.session_state.get("AUTH_EMAIL"), page_name)

def _do_login(email: str, password: str):
    """يسجّل الدخول حسب الإعداد:
       - ALLOW_ANY_LOGIN=1: أي باسورد مقبول؛ ينشئ/يحدّث المستخدم ويدخّل فوراً.
       - غير ذلك: لو المستخدم غير موجود → يُنشأ تلقائياً بالباسورد المرسل؛ لو موجود يتحقق من كلمة المرور."""
    email = (email or "").strip().lower()
    if not email:
        return False, t("أدخل بريدك الإلكتروني.", "Please enter your email.")

    if ALLOW_ANY_LOGIN:
        # قبول فوري وإنشاء/تحديث الحساب (ديمو)
        upsert_user(email, password or "demo", role="user")
        u = get_user(email)
        st.session_state["AUTH_EMAIL"] = u[1]
        st.session_state["AUTH_ROLE"] = u[3]
        touch_last_login(u[1])
        _audit("login_success_any", u[1], "ALLOW_ANY_LOGIN=1")
        return True, ""

    u = get_user(email)
    if not u:
        # إنشاء تلقائي ثم دخول
        create_user(email, password or "demo", role="user")
        u = get_user(email)

    # تحقق عادي
    if not _verify_pw(password or "", u[2]):
        _audit("login_failed", email, "bad_credentials")
        return False, t("بيانات الدخول غير صحيحة.", "Invalid credentials.")
    st.session_state["AUTH_EMAIL"] = u[1]
    st.session_state["AUTH_ROLE"] = u[3]
    touch_last_login(u[1])
    _audit("login_success", u[1], f"role={u[3]}")
    return True, ""

def login_gate() -> bool:
    # إذا مسجّل خلاص
    if st.session_state.get("AUTH_EMAIL"):
        return True

    # otherwise: اعرض صفحة البوابة (Light)
    _login_css()
    logo_b64 = _read_logo_as_base64()

    st.markdown('<div class="humain-wrap"><div class="humain-card">', unsafe_allow_html=True)

    # Header
    st.markdown('<div class="h-header">', unsafe_allow_html=True)
    if logo_b64:
        st.markdown(f'<div class="h-logo"><img src="data:image/png;base64,{logo_b64}" alt="Logo" style="height:100%;width:100%;object-fit:cover;"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="h-logo"><span style="color:#888;">Logo</span></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="h-title">
          <h1>HUMAIN Lifestyle — Live Demo</h1>
          <p>Dar AL Khartoum Travel And Tourism CO LTD — <span class="h-muted">شركة دار الخرطوم للسفر والسياحة المحدودة</span></p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Body
    st.markdown('<div class="h-body">', unsafe_allow_html=True)

    # LEFT (Legal / Brand)
    st.markdown('<div class="h-left">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="h-legal">
          <strong>© 2025 HUMAIN Lifestyle — {t('جميع الحقوق محفوظة','All rights reserved')}</strong>
          <div class="h-divider"></div>
          <div>
            {t(
                'هذا نموذج عرض حي (Demo) لأغراض الاختبار والتقييم فقط. البيانات المعروضة تجريبية وقد لا تعكس أسعار/توفّر حقيقي. باستخدامك لهذه المنصة فأنت تقرّ بمسؤوليتك عن صحة البيانات المدخلة وقبولك لشروط الاستخدام وسياسة الخصوصية.',
                'This is a live demo for testing/evaluation purposes. Data shown is sample and may not reflect actual availability/prices. By using this platform, you accept responsibility for your inputs and agree to the Terms of Use and Privacy Policy.'
            )}
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # RIGHT (Language + Auth)
    st.markdown('<div class="h-right">', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="h-form">', unsafe_allow_html=True)
        st.markdown(f"<h3>🌐 {t('اللغة','Language')}</h3>", unsafe_allow_html=True)
        _language_selector()

        tabs = st.tabs([t("دخول", "Login"), t("إنشاء حساب", "Create account")])

        with tabs[0]:
            email = st.text_input(t("البريد الإلكتروني", "Email"), key="login_email")
            pw = st.text_input(t("كلمة المرور", "Password"), type="password", key="login_pw")
            if st.button(t("دخول", "Login"), type="primary"):
                ok, msg = _do_login(email, pw)
                if ok:
                    st.experimental_rerun()
                else:
                    st.error(msg)

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

        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)  # /h-right
    st.markdown('</div>', unsafe_allow_html=True)  # /h-body

    # Footer
    st.markdown(
        f"""
        <div class="h-foot">
          <div class="h-company">
            <div class="mini-logo">{'<img src="data:image/png;base64,'+logo_b64+'" style="height:100%;width:100%;object-fit:cover;">' if logo_b64 else ''}</div>
            <div>
              <div style="font-weight:700;">Dar AL Khartoum Travel And Tourism CO LTD</div>
              <div class="h-muted">شركة دار الخرطوم للسفر والسياحة المحدودة</div>
            </div>
          </div>
          <div class="h-muted">HUMAIN Lifestyle — {t('بوابة ذكية للزائر والمعتمر والمستثمر','A smart gateway for visitors, pilgrims, and investors')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('</div></div>', unsafe_allow_html=True)  # /humain-card /humain-wrap
    st.stop()
