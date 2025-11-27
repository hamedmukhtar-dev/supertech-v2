# auth_i18n.py — Polished Landing + Auth + i18n + Audit (no changes to your pages)
import os, sqlite3, hashlib, hmac
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Tuple
import streamlit as st

# ---------- Optional bcrypt (auto-fallback) ----------
try:
    from passlib.hash import bcrypt
except Exception:
    bcrypt = None  # fallback if backend missing

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

def _now() -> str:
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
        pass  # لا توقف الواجهة لو اللوج فشل

# --- hashing helpers ---
def _sha256(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def _hash_pw(pw: str) -> str:
    """
    استخدم bcrypt إن كان متاحاً (آمن)، وإلا SHA-256 كحل تجريبي.
    نتجنب أخطاء backends في بعض الاستضافات.
    """
    if bcrypt:
        try:
            # bcrypt له حد 72 بايت: نقطع بأمان لو كلمة السر طويلة جداً
            if len(pw.encode("utf-8")) > 72:
                pw = pw[:72]
            return bcrypt.hash(pw)
        except Exception:
            # fallback silent
            return _sha256(pw)
    return _sha256(pw)

def _verify_pw(pw: str, hashed: str) -> bool:
    if bcrypt and hashed.startswith("$2"):
        try:
            if len(pw.encode("utf-8")) > 72:
                pw = pw[:72]
            return bcrypt.verify(pw, hashed)
        except Exception:
            return False
    # sha256 fallback
    return hmac.compare_digest(_sha256(pw), hashed)

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

# -------- i18n --------
LANGS = {"ar": "العربية", "en": "English"}

def get_lang() -> str:
    return st.session_state.get("LANG", "ar")

def set_lang(lang: str):
    st.session_state["LANG"] = "ar" if lang not in LANGS else lang

def t(ar: str, en: str) -> str:
    return ar if get_lang() == "ar" else en

# -------- Defaults (demo accounts) --------
def setup_defaults():
    ensure_auth_tables(DB_PATH_DEFAULT)
    # كلمات مرور قصيرة لتفادي 72 بايت
    create_user("admin@demo.local", "admin123", role="admin")
    create_user("demo@demo.local", "demo123", role="demo")
    create_user("hamed.mukhtar@daral-sd.com", os.getenv("DEFAULT_USER_PASSWORD", "Daral2025"), role="admin")

# -------- Landing + Auth Gate (beautiful layout) --------

_LANDING_CSS = """
<style>
  :root{
    --bg:#0b1220;
    --card:#10192e;
    --muted:#93a1b1;
    --gold:#D4AF37;
    --accent:#1f6feb;
  }
  .hl-wrap{
    min-height: 100vh;
    background: radial-gradient(1200px 600px at 80% -10%, rgba(32,77,204,.25), transparent 60%),
                radial-gradient(1200px 600px at 10% 110%, rgba(212,175,55,.20), transparent 60%),
                var(--bg);
    color: #e6edf3;
    display:flex;align-items:center;justify-content:center;padding: 24px;
  }
  .hl-card{
    width:min(980px, 100%);
    background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));
    border: 1px solid rgba(255,255,255,.08);
    box-shadow: 0 10px 40px rgba(0,0,0,.35);
    border-radius: 18px;
    overflow:hidden;
  }
  .hl-top{
    padding: 26px 26px 20px 26px;
    background: linear-gradient(90deg, rgba(0,108,53,.25), rgba(0,77,36,.25));
    border-bottom:1px solid rgba(255,255,255,.06);
  }
  .hl-brand{
    display:flex;gap:14px;align-items:center;
  }
  .hl-brand img{
    width:48px;height:48px;border-radius:12px;background:#fff;border:2px solid var(--gold);padding:4px;object-fit:contain;
  }
  .hl-title{font-weight:800;font-size:22px;margin:0;letter-spacing:.2px}
  .hl-sub{opacity:.9;margin-top:2px;font-size:13px}
  .hl-legal{
    padding:16px 26px;color:var(--muted);font-size:12px;border-top:1px dashed rgba(255,255,255,.08);
    background: linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,.00));
  }
  .hl-grid{display:grid;grid-template-columns: 1.2fr 1fr;gap:0;border-top:1px solid rgba(255,255,255,.06)}
  @media (max-width:860px){ .hl-grid{grid-template-columns: 1fr} }
  .hl-pane{padding:28px}
  .hl-pane + .hl-pane{border-left:1px solid rgba(255,255,255,.06)}
  .hl-pane h3{margin:0 0 14px 0;font-size:16px;color:#eaeef2}
  .hl-locale{
    display:flex;flex-direction:column;gap:12px
  }
  .hl-locale .hint{font-size:12px;color:var(--muted)}
  .hl-footer{
    display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;
    padding:16px 26px;border-top:1px solid rgba(255,255,255,.06);background:rgba(0,0,0,.15)
  }
  .hl-copy{font-size:12px;color:var(--muted)}
  .hl-org{display:flex;gap:10px;align-items:center}
  .hl-org img{height:28px;border-radius:8px;background:#fff;border:1px solid var(--gold);padding:3px;object-fit:contain}
  .hl-badge{line-height:1.2}
</style>
"""

def _logo_tag() -> str:
    # استخدم ملفك إن وُجد؛ وإلا إيموجي افتراضي
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        return '<img src="assets/logo.png" alt="logo" />'
    return '<div style="width:48px;height:48px;display:flex;align-items:center;justify-content:center;border-radius:12px;background:#fff;border:2px solid #D4AF37;color:#0b1220;font-weight:900">HL</div>'

def _dir_attr() -> str:
    return 'dir="rtl"' if get_lang() == "ar" else 'dir="ltr"'

def _header_block():
    st.markdown(_LANDING_CSS, unsafe_allow_html=True)
    st.markdown(f"""
<div class="hl-wrap" {_dir_attr()}>
  <div class="hl-card">
    <div class="hl-top">
      <div class="hl-brand">
        {_logo_tag()}
        <div>
          <div class="hl-title">HUMAIN Lifestyle — Live Demo</div>
          <div class="hl-sub">Dar AL Khartoum Travel And Tourism CO LTD · شركة دار الخرطوم للسفر والسياحة المحدودة</div>
        </div>
      </div>
    </div>
""", unsafe_allow_html=True)

def _legal_block():
    st.markdown(f"""
    <div class="hl-legal">
      <div>{t("© 2025 HUMAIN Lifestyle — جميع الحقوق محفوظة.",
               "© 2025 HUMAIN Lifestyle — All rights reserved.")}</div>
      <div style="margin-top:6px">
        {t("هذا نموذج عرض حي (Demo) لأغراض الاختبار والتقييم فقط. البيانات المعروضة تجريبية وقد لا تعكس أسعار/توفّر حقيقي. باستخدامك لهذه المنصة فأنت تقرّ بمسؤوليتك عن صحة البيانات المدخلة وقبولك لشروط الاستخدام وسياسة الخصوصية.",
           "This is a live demo for testing and evaluation. Data shown is sample and may not reflect real prices/availability. By using this platform you accept the Terms of Use and Privacy Policy.")}
      </div>
    </div>
""", unsafe_allow_html=True)

def _footer_block():
    st.markdown(f"""
    <div class="hl-footer">
      <div class="hl-org">
        {_logo_tag()}
        <div class="hl-badge">
          <div style="font-weight:700">Dar AL Khartoum Travel And Tourism CO LTD</div>
          <div style="opacity:.9">{t("شركة دار الخرطوم للسفر والسياحة المحدودة", "Dar Al Khartoum Travel & Tourism Co. Ltd.")}</div>
        </div>
      </div>
      <div class="hl-copy">
        {t("الهُويّة والعلامة محفوظة. الاستخدام الداخلي/العرضي فقط.", "Branding © reserved. Internal/demo use only.")}
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

def _language_pane():
    st.markdown('<div class="hl-grid"><div class="hl-pane">', unsafe_allow_html=True)
    st.markdown(f"<h3>🌐 {t('اللغة','Language')}</h3>", unsafe_allow_html=True)
    current = get_lang()
    # نستخدم عناصر Streamlit القياسية (ستظهر داخل البطاقة)
    lang = st.selectbox(
        t("اختر اللغة", "Choose language"),
        options=list(LANGS.keys()),
        index=0 if current == "ar" else 1,
        format_func=lambda k: LANGS[k],
        key="lang_select_gate",
    )
    if lang != current:
        set_lang(lang)
        st.experimental_rerun()

    st.caption(t("اضبط اللغة أولاً ثم تابع تسجيل الدخول.",
                 "Pick a language first, then continue to sign in."))
    st.markdown('<div class="hint">' + t("يمكنك تغيير اللغة لاحقًا من الشريط الجانبي.",
                                         "You can change language later from the sidebar.") + '</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def _auth_pane():
    st.markdown('<div class="hl-pane">', unsafe_allow_html=True)
    st.markdown(f"<h3>🔐 {t('تسجيل الدخول','Sign in')}</h3>", unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs([t("دخول","Login"), t("إنشاء حساب","Create account")])

    with tab_login:
        email = st.text_input(t("البريد الإلكتروني", "Email"), key="login_email")
        pw = st.text_input(t("كلمة المرور", "Password"), type="password", key="login_pw")
        if st.button(t("دخول","Login"), type="primary", use_container_width=True):
            u = get_user(email)
            if not u or not _verify_pw(pw, u[2]):
                st.error(t("بيانات الدخول غير صحيحة.", "Invalid credentials."))
                _audit("login_failed", email, "bad_credentials"); return
            st.session_state["AUTH_EMAIL"] = u[1]
            st.session_state["AUTH_ROLE"]  = u[3]
            touch_last_login(u[1])
            _audit("login_success", u[1], f"role={u[3]}")
            st.experimental_rerun()

    with tab_signup:
        n_email = st.text_input(t("البريد الإلكتروني", "Email"), key="new_email")
        n_pw = st.text_input(t("كلمة المرور", "Password"), type="password", key="new_pw")
        n_pw2 = st.text_input(t("تأكيد كلمة المرور", "Confirm password"), type="password", key="new_pw2")
        if st.button(t("إنشاء الحساب","Create account"), use_container_width=True):
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

    st.markdown('</div></div>', unsafe_allow_html=True)  # close pane + grid

def login_gate() -> bool:
    """
    تُستدعى في أعلى streamlit_app.py.
    لو المستخدم غير مسجل، نعرض شاشة الهبوط المرتّبة ونوقف بقية الصفحات.
    """
    if st.session_state.get("AUTH_EMAIL"):
        return True

    # رسم الهبوط
    _header_block()
    _language_pane()
    _auth_pane()
    _legal_block()
    _footer_block()

    # إيقاف التطبيق لحين تسجيل الدخول
    st.stop()
    return False

def signout_button():
    if st.sidebar.button("🔓 " + t("تسجيل خروج", "Sign out")):
        _audit("logout", st.session_state.get("AUTH_EMAIL"))
        for k in ["AUTH_EMAIL", "AUTH_ROLE"]:
            st.session_state.pop(k, None)
        st.experimental_rerun()

def track_page_view(page_name: str):
    _audit("page_view", st.session_state.get("AUTH_EMAIL"), page_name)
