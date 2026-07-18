"""
SFT SYSTEMS LLC — Fleet Management System
Professional Streamlit app for vehicles, repair orders, inventory, customers, and invoices.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import sqlite3
import hashlib
import requests
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SFT Fleet Management",
    layout="wide",
    page_icon="🚛",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Modern UI CSS
# ─────────────────────────────────────────────
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Main background */
    .stApp {
        background: linear-gradient(160deg, #0f172a 0%, #1e293b 45%, #0f172a 100%);
        color: #e2e8f0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1220 0%, #111827 100%);
        border-right: 1px solid #1e293b;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {
        color: #cbd5e1 !important;
    }

    /* Headers */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 1rem 1.25rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-weight: 700 !important;
    }

    /* Primary buttons */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(2, 132, 199, 0.45);
    }

    /* Secondary / default buttons */
    .stButton > button {
        border-radius: 10px !important;
        border: 1px solid #334155 !important;
        background: #1e293b !important;
        color: #e2e8f0 !important;
        font-weight: 500 !important;
    }
    .stButton > button:hover {
        border-color: #38bdf8 !important;
        color: #38bdf8 !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox > div > div,
    .stDateInput > div > div > input {
        border-radius: 10px !important;
        border: 1px solid #334155 !important;
        background-color: #0f172a !important;
        color: #f1f5f9 !important;
    }

    /* Expanders */
    div[data-testid="stExpander"] {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        overflow: hidden;
    }

    /* Dataframes */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #334155;
    }

    /* Alert / card helpers */
    .sft-card {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 1.1rem 1.35rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    .sft-alert-warn {
        background: linear-gradient(135deg, #422006 0%, #78350f 100%);
        border-left: 4px solid #f59e0b;
        border-radius: 10px;
        padding: 0.85rem 1.1rem;
        margin: 0.4rem 0;
        color: #fef3c7;
    }
    .sft-alert-danger {
        background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%);
        border-left: 4px solid #ef4444;
        border-radius: 10px;
        padding: 0.85rem 1.1rem;
        margin: 0.4rem 0;
        color: #fecaca;
    }
    .sft-alert-info {
        background: linear-gradient(135deg, #0c4a6e 0%, #075985 100%);
        border-left: 4px solid #38bdf8;
        border-radius: 10px;
        padding: 0.85rem 1.1rem;
        margin: 0.4rem 0;
        color: #e0f2fe;
    }
    .sft-alert-ok {
        background: linear-gradient(135deg, #052e16 0%, #14532d 100%);
        border-left: 4px solid #22c55e;
        border-radius: 10px;
        padding: 0.85rem 1.1rem;
        margin: 0.4rem 0;
        color: #dcfce7;
    }
    .sft-brand {
        font-size: 1.35rem;
        font-weight: 700;
        color: #38bdf8;
        letter-spacing: -0.02em;
    }
    .sft-muted {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    .sft-login-box {
        max-width: 420px;
        margin: 4rem auto;
        padding: 2rem;
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 18px;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
    }
    .sft-badge {
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        background: #0ea5e9;
        color: white;
    }
    hr {
        border-color: #334155 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# Database helpers
# ─────────────────────────────────────────────
DB_PATH = Path(__file__).resolve().parent / "sft_fleet.db"


@contextmanager
def get_conn():
    """Yield a SQLite connection with row factory; always close cleanly."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def hash_pwd(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db() -> None:
    """Create tables if missing. NEVER drop existing data."""
    with get_conn() as conn:
        c = conn.cursor()
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value REAL
            );

            CREATE TABLE IF NOT EXISTS vehicles (
                unit TEXT PRIMARY KEY,
                type TEXT,
                status TEXT,
                vin TEXT,
                year INTEGER,
                make TEXT,
                model TEXT,
                mileage INTEGER,
                plate_exp TEXT,
                insurance_exp TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS inventory (
                part_number TEXT PRIMARY KEY,
                part_name TEXT,
                qty INTEGER,
                unit_cost REAL,
                retail_price REAL,
                category TEXT
            );

            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT,
                contact TEXT,
                phone TEXT,
                email TEXT,
                vins TEXT
            );

            CREATE TABLE IF NOT EXISTS repair_orders (
                ro_number TEXT PRIMARY KEY,
                date TEXT,
                customer TEXT,
                unit TEXT,
                vin TEXT,
                odometer INTEGER,
                customer_states TEXT,
                diagnostic_notes TEXT,
                labor_hours REAL,
                labor_rate REAL,
                parts_total REAL,
                labor_total REAL,
                shop_supply REAL,
                total REAL,
                status TEXT DEFAULT 'Open'
            );

            CREATE TABLE IF NOT EXISTS invoices (
                invoice_number TEXT PRIMARY KEY,
                date TEXT,
                ro_number TEXT,
                customer TEXT,
                total REAL,
                status TEXT,
                payment_terms TEXT,
                due_date TEXT
            );
            """
        )

        # Seed admin user if none exist
        count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            c.execute(
                "INSERT INTO users (username, password_hash, role, full_name) VALUES (?,?,?,?)",
                ("admin", hash_pwd("admin123"), "Admin", "Administrator"),
            )

        # Default labor rate
        rate = c.execute("SELECT value FROM settings WHERE key='labor_rate'").fetchone()
        if rate is None:
            c.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)",
                ("labor_rate", 130.0),
            )


def authenticate(username: str, password: str) -> Optional[dict]:
    """Verify credentials against the users table. Returns user row dict or None."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT username, role, full_name FROM users WHERE username = ? AND password_hash = ?",
            (username.strip(), hash_pwd(password)),
        ).fetchone()
        if row:
            return dict(row)
    return None


def get_setting(key: str, default: float = 0.0) -> float:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return float(row["value"]) if row else default


def set_setting(key: str, value: float) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )


def read_table(sql: str, params: tuple = ()) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def next_ro_number() -> str:
    """Generate RO-YYYYMMDD-NNN style numbers."""
    prefix = f"RO-{date.today().strftime('%Y%m%d')}"
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT ro_number FROM repair_orders WHERE ro_number LIKE ? ORDER BY ro_number DESC",
            (f"{prefix}%",),
        ).fetchall()
    if not rows:
        return f"{prefix}-001"
    last = rows[0]["ro_number"]
    try:
        seq = int(last.split("-")[-1]) + 1
    except ValueError:
        seq = 1
    return f"{prefix}-{seq:03d}"


def next_invoice_number() -> str:
    prefix = f"INV-{date.today().strftime('%Y%m%d')}"
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT invoice_number FROM invoices WHERE invoice_number LIKE ? ORDER BY invoice_number DESC",
            (f"{prefix}%",),
        ).fetchall()
    if not rows:
        return f"{prefix}-001"
    last = rows[0]["invoice_number"]
    try:
        seq = int(last.split("-")[-1]) + 1
    except ValueError:
        seq = 1
    return f"{prefix}-{seq:03d}"


def parse_date_safe(value) -> Optional[date]:
    """Parse stored date strings safely; return None if invalid."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    if not s or s.lower() in ("none", "nat", "nan"):
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(s).date()
    except Exception:
        return None


def lookup_vin(vin: str) -> dict:
    """NHTSA vPIC decode. Returns year/make/model or empty fields on failure."""
    result = {"year": None, "make": "", "model": ""}
    vin = (vin or "").strip().upper()
    if len(vin) < 11:
        return result
    try:
        r = requests.get(
            f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json",
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("Results", [])
        year = next((x["Value"] for x in data if x["Variable"] == "Model Year"), "") or ""
        make = next((x["Value"] for x in data if x["Variable"] == "Make"), "") or ""
        model = next((x["Value"] for x in data if x["Variable"] == "Model"), "") or ""
        result["year"] = int(year) if str(year).isdigit() else None
        result["make"] = make
        result["model"] = model
    except Exception:
        pass
    return result


# ─────────────────────────────────────────────
# Init DB once per process
# ─────────────────────────────────────────────
init_db()

# ─────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "full_name" not in st.session_state:
    st.session_state.full_name = ""
if "menu" not in st.session_state:
    st.session_state.menu = "Dashboard"
if "show_add_vehicle" not in st.session_state:
    st.session_state.show_add_vehicle = False
if "edit_unit" not in st.session_state:
    st.session_state.edit_unit = None
if "show_create_ro" not in st.session_state:
    st.session_state.show_create_ro = False
if "edit_ro" not in st.session_state:
    st.session_state.edit_ro = None
if "vin_year" not in st.session_state:
    st.session_state.vin_year = 2025
if "vin_make" not in st.session_state:
    st.session_state.vin_make = ""
if "vin_model" not in st.session_state:
    st.session_state.vin_model = ""


# ─────────────────────────────────────────────
# Login page
# ─────────────────────────────────────────────
def page_login() -> None:
    st.markdown(
        """
        <div style="text-align:center; margin-top:2rem;">
            <div class="sft-brand">🚛 SFT SYSTEMS LLC</div>
            <p class="sft-muted">Professional Fleet Management System</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        st.markdown("### Sign in")
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                user = authenticate(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user["username"]
                    st.session_state.role = user["role"]
                    st.session_state.full_name = user.get("full_name") or user["username"]
                    st.session_state.menu = "Dashboard"
                    st.success(f"Welcome, {st.session_state.full_name}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        st.caption("Default admin: `admin` / `admin123` — change after first login.")


if not st.session_state.logged_in:
    page_login()
    st.stop()


# ─────────────────────────────────────────────
# Sidebar navigation + logout
# ─────────────────────────────────────────────
NAV_ITEMS = [
    ("Dashboard", "🏠"),
    ("Vehicles", "🚚"),
    ("Repair Orders", "🔧"),
    ("Inventory", "📋"),
    ("Customers", "👥"),
    ("Invoices", "📦"),
    ("Settings", "⚙️"),
]

with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 0.5rem 0 1rem 0;">
            <div class="sft-brand">🚛 SFT Fleet</div>
            <div class="sft-muted">{st.session_state.full_name} · {st.session_state.role}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    for label, icon in NAV_ITEMS:
        is_active = st.session_state.menu == label
        btn_type = "primary" if is_active else "secondary"
        if st.button(
            f"{icon}  {label}",
            key=f"nav_{label}",
            use_container_width=True,
            type=btn_type,
        ):
            st.session_state.menu = label
            st.rerun()

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.caption(f"DB: `{DB_PATH.name}`")


# ─────────────────────────────────────────────
# Top header
# ─────────────────────────────────────────────
st.markdown(
    f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
        <div>
            <h1 style="margin:0; font-size:1.75rem;">🚛 SFT SYSTEMS LLC</h1>
            <p class="sft-muted" style="margin:0.15rem 0 0 0;">Fleet Management · {st.session_state.menu}</p>
        </div>
        <div><span class="sft-badge">{st.session_state.username}</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

menu = st.session_state.menu


# ═════════════════════════════════════════════
# DASHBOARD
# ═════════════════════════════════════════════
if menu == "Dashboard":
    st.subheader("Dashboard Overview")

    vehicles_df = read_table("SELECT * FROM vehicles")
    ro_df = read_table("SELECT * FROM repair_orders")
    inv_df = read_table("SELECT * FROM invoices")
    stock_df = read_table("SELECT * FROM inventory")

    active_vehicles = (
        int((vehicles_df["status"] == "Active").sum())
        if not vehicles_df.empty and "status" in vehicles_df.columns
        else (len(vehicles_df) if not vehicles_df.empty else 0)
    )
    open_ros = (
        int(ro_df["status"].isin(["Open", "In Progress"]).sum())
        if not ro_df.empty
        else 0
    )
    unpaid_inv = (
        int(inv_df["status"].isin(["Unpaid", "Overdue", "Partial"]).sum())
        if not inv_df.empty
        else 0
    )
    low_stock = (
        int((stock_df["qty"] <= 5).sum()) if not stock_df.empty else 0
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Vehicles", active_vehicles)
    m2.metric("Open / In-Progress ROs", open_ros)
    m3.metric("Unpaid Invoices", unpaid_inv)
    m4.metric("Low Stock Parts (≤5)", low_stock)

    st.markdown("### 🔔 Alerts")
    alerts: list[tuple[str, str]] = []  # (level, message)
    today = date.today()
    warn_days = 30

    # Plate / insurance expirations
    if not vehicles_df.empty:
        for _, v in vehicles_df.iterrows():
            unit = v.get("unit", "?")
            plate = parse_date_safe(v.get("plate_exp"))
            ins = parse_date_safe(v.get("insurance_exp"))
            if plate:
                days = (plate - today).days
                if days < 0:
                    alerts.append(
                        ("danger", f"Unit **{unit}**: plate expired {abs(days)} day(s) ago ({plate}).")
                    )
                elif days <= warn_days:
                    alerts.append(
                        ("warn", f"Unit **{unit}**: plate expires in {days} day(s) ({plate}).")
                    )
            if ins:
                days = (ins - today).days
                if days < 0:
                    alerts.append(
                        ("danger", f"Unit **{unit}**: insurance expired {abs(days)} day(s) ago ({ins}).")
                    )
                elif days <= warn_days:
                    alerts.append(
                        ("warn", f"Unit **{unit}**: insurance expires in {days} day(s) ({ins}).")
                    )

    # Overdue invoices
    if not inv_df.empty:
        for _, inv in inv_df.iterrows():
            status = str(inv.get("status", ""))
            due = parse_date_safe(inv.get("due_date"))
            inv_no = inv.get("invoice_number", "?")
            if status in ("Unpaid", "Partial", "Overdue") and due and due < today:
                alerts.append(
                    (
                        "danger",
                        f"Invoice **{inv_no}** overdue (due {due}) — ${float(inv.get('total') or 0):,.2f} · {inv.get('customer', '')}.",
                    )
                )
            elif status == "Unpaid" and due and 0 <= (due - today).days <= 7:
                alerts.append(
                    (
                        "warn",
                        f"Invoice **{inv_no}** due in {(due - today).days} day(s) — ${float(inv.get('total') or 0):,.2f}.",
                    )
                )

    # Open repair orders aging
    if not ro_df.empty:
        open_mask = ro_df["status"].isin(["Open", "In Progress"])
        for _, ro in ro_df[open_mask].iterrows():
            ro_date = parse_date_safe(ro.get("date"))
            if ro_date and (today - ro_date).days >= 7:
                alerts.append(
                    (
                        "info",
                        f"RO **{ro.get('ro_number')}** has been {ro.get('status')} for {(today - ro_date).days} day(s) · Unit {ro.get('unit', '—')}.",
                    )
                )

    # Low stock
    if not stock_df.empty:
        for _, p in stock_df[stock_df["qty"] <= 5].iterrows():
            alerts.append(
                (
                    "warn",
                    f"Low stock: **{p.get('part_number')}** — {p.get('part_name')} (qty {int(p.get('qty') or 0)}).",
                )
            )

    if not alerts:
        st.markdown(
            '<div class="sft-alert-ok">✅ No alerts right now. Fleet status looks good.</div>',
            unsafe_allow_html=True,
        )
    else:
        # Sort danger first
        order = {"danger": 0, "warn": 1, "info": 2}
        alerts.sort(key=lambda x: order.get(x[0], 9))
        for level, msg in alerts:
            css = {
                "danger": "sft-alert-danger",
                "warn": "sft-alert-warn",
                "info": "sft-alert-info",
            }.get(level, "sft-alert-info")
            st.markdown(f'<div class="{css}">{msg}</div>', unsafe_allow_html=True)

    # Recent activity
    st.markdown("### Recent Repair Orders")
    if ro_df.empty:
        st.info("No repair orders yet. Create one under **Repair Orders**.")
    else:
        recent = ro_df.sort_values("date", ascending=False).head(8)
        st.dataframe(recent, use_container_width=True, hide_index=True)


# ═════════════════════════════════════════════
# VEHICLES
# ═════════════════════════════════════════════
elif menu == "Vehicles":
    st.subheader("🚚 Vehicles — SFT Fleet")

    vehicles_df = read_table("SELECT * FROM vehicles ORDER BY unit")

    st.markdown("#### Vehicle List")
    if vehicles_df.empty:
        st.info("No vehicles on file. Add your first unit below.")
    else:
        st.dataframe(vehicles_df, use_container_width=True, hide_index=True)

    c_add, c_spacer = st.columns([1, 3])
    with c_add:
        if st.button("➕ Add New Vehicle", type="primary", use_container_width=True):
            st.session_state.show_add_vehicle = True
            st.session_state.edit_unit = None

    # ── Add vehicle form ──
    if st.session_state.show_add_vehicle:
        st.markdown("---")
        st.markdown("#### New Vehicle")
        with st.form("add_vehicle_form"):
            a1, a2 = st.columns(2)
            with a1:
                unit = st.text_input("Unit # *", placeholder="e.g. T-101")
                vtype = st.selectbox(
                    "Type",
                    ["Semi Truck", "Dry Van Trailer", "Reefer Trailer", "Other"],
                )
                vin = st.text_input("VIN Number", placeholder="17-character VIN")
            with a2:
                year = st.number_input(
                    "Year",
                    min_value=1980,
                    max_value=2035,
                    value=int(st.session_state.vin_year or 2025),
                )
                make = st.text_input("Make", value=st.session_state.vin_make or "")
                model = st.text_input("Model", value=st.session_state.vin_model or "")

            b1, b2, b3 = st.columns(3)
            with b1:
                mileage = st.number_input("Mileage", min_value=0, value=0, step=100)
            with b2:
                plate_exp = st.date_input("Plate Expiration", value=date.today() + timedelta(days=365))
            with b3:
                insurance_exp = st.date_input(
                    "Insurance Expiration", value=date.today() + timedelta(days=365)
                )
            notes = st.text_area("Notes", placeholder="Optional notes")

            f1, f2, f3 = st.columns(3)
            with f1:
                do_vin = st.form_submit_button("🔍 Lookup VIN", use_container_width=True)
            with f2:
                save = st.form_submit_button("💾 Save Vehicle", type="primary", use_container_width=True)
            with f3:
                cancel = st.form_submit_button("Cancel", use_container_width=True)

        if do_vin:
            if not vin:
                st.warning("Enter a VIN first.")
            else:
                decoded = lookup_vin(vin)
                if decoded["make"] or decoded["model"] or decoded["year"]:
                    st.session_state.vin_year = decoded["year"] or st.session_state.vin_year
                    st.session_state.vin_make = decoded["make"]
                    st.session_state.vin_model = decoded["model"]
                    st.success(
                        f"Auto-filled: {decoded['year'] or '—'} {decoded['make']} {decoded['model']}"
                    )
                    st.rerun()
                else:
                    st.error("VIN lookup failed or returned no data.")

        if cancel:
            st.session_state.show_add_vehicle = False
            st.session_state.vin_year = 2025
            st.session_state.vin_make = ""
            st.session_state.vin_model = ""
            st.rerun()

        if save:
            if not unit or not unit.strip():
                st.error("Unit # is required.")
            else:
                try:
                    with get_conn() as conn:
                        existing = conn.execute(
                            "SELECT unit FROM vehicles WHERE unit = ?",
                            (unit.strip(),),
                        ).fetchone()
                        if existing:
                            st.error(f"Unit **{unit.strip()}** already exists. Edit it instead.")
                        else:
                            conn.execute(
                                """
                                INSERT INTO vehicles
                                (unit, type, status, vin, year, make, model, mileage, plate_exp, insurance_exp, notes)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                                """,
                                (
                                    unit.strip(),
                                    vtype,
                                    "Active",
                                    (vin or "").strip().upper(),
                                    int(year),
                                    make.strip(),
                                    model.strip(),
                                    int(mileage),
                                    str(plate_exp),
                                    str(insurance_exp),
                                    notes or "",
                                ),
                            )
                            st.success(f"✅ Vehicle **{unit.strip()}** added.")
                            st.session_state.show_add_vehicle = False
                            st.session_state.vin_year = 2025
                            st.session_state.vin_make = ""
                            st.session_state.vin_model = ""
                            st.rerun()
                except Exception as e:
                    st.error(f"Could not save vehicle: {e}")

    # ── Edit vehicle ──
    st.markdown("---")
    st.markdown("#### Edit Vehicle")
    if vehicles_df.empty:
        st.caption("Add a vehicle first to enable editing.")
    else:
        units = vehicles_df["unit"].astype(str).tolist()
        selected_unit = st.selectbox(
            "Select unit to edit",
            units,
            key="vehicle_edit_select",
        )
        if st.button("Open Edit Form", key="open_edit_vehicle"):
            st.session_state.edit_unit = selected_unit
            st.session_state.show_add_vehicle = False

        if st.session_state.edit_unit:
            unit_key = st.session_state.edit_unit
            row = vehicles_df[vehicles_df["unit"].astype(str) == str(unit_key)]
            if row.empty:
                st.warning("Selected vehicle no longer exists.")
                st.session_state.edit_unit = None
            else:
                vehicle = row.iloc[0]
                st.markdown(f"**Editing unit:** `{unit_key}`")

                type_options = ["Semi Truck", "Dry Van Trailer", "Reefer Trailer", "Other"]
                cur_type = str(vehicle.get("type") or "Semi Truck")
                type_idx = type_options.index(cur_type) if cur_type in type_options else 0

                status_options = ["Active", "Inactive", "In Shop", "Out of Service"]
                cur_status = str(vehicle.get("status") or "Active")
                status_idx = (
                    status_options.index(cur_status) if cur_status in status_options else 0
                )

                plate_default = parse_date_safe(vehicle.get("plate_exp")) or date.today()
                ins_default = parse_date_safe(vehicle.get("insurance_exp")) or date.today()
                year_val = int(vehicle.get("year") or 2025)
                mileage_val = int(vehicle.get("mileage") or 0)

                with st.form("edit_vehicle_form"):
                    e1, e2 = st.columns(2)
                    with e1:
                        vtype = st.selectbox("Type", type_options, index=type_idx)
                        vin = st.text_input("VIN", value=str(vehicle.get("vin") or ""))
                        year = st.number_input(
                            "Year", min_value=1980, max_value=2035, value=year_val
                        )
                        make = st.text_input("Make", value=str(vehicle.get("make") or ""))
                    with e2:
                        model = st.text_input("Model", value=str(vehicle.get("model") or ""))
                        mileage = st.number_input(
                            "Mileage", min_value=0, value=mileage_val, step=100
                        )
                        status = st.selectbox("Status", status_options, index=status_idx)
                        plate_exp = st.date_input("Plate Expiration", value=plate_default)
                        insurance_exp = st.date_input(
                            "Insurance Expiration", value=ins_default
                        )
                    notes = st.text_area("Notes", value=str(vehicle.get("notes") or ""))

                    s1, s2 = st.columns(2)
                    with s1:
                        save_edit = st.form_submit_button(
                            "💾 Save Changes", type="primary", use_container_width=True
                        )
                    with s2:
                        cancel_edit = st.form_submit_button("Cancel", use_container_width=True)

                if cancel_edit:
                    st.session_state.edit_unit = None
                    st.rerun()

                if save_edit:
                    try:
                        with get_conn() as conn:
                            conn.execute(
                                """
                                UPDATE vehicles SET
                                    type=?, vin=?, year=?, make=?, model=?,
                                    mileage=?, plate_exp=?, insurance_exp=?, status=?, notes=?
                                WHERE unit=?
                                """,
                                (
                                    vtype,
                                    (vin or "").strip().upper(),
                                    int(year),
                                    make.strip(),
                                    model.strip(),
                                    int(mileage),
                                    str(plate_exp),
                                    str(insurance_exp),
                                    status,
                                    notes or "",
                                    unit_key,
                                ),
                            )
                        st.success(f"✅ Vehicle **{unit_key}** updated.")
                        st.session_state.edit_unit = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Update failed: {e}")


# ═════════════════════════════════════════════
# REPAIR ORDERS
# ═════════════════════════════════════════════
elif menu == "Repair Orders":
    st.subheader("🔧 Repair Orders")

    ro_df = read_table("SELECT * FROM repair_orders ORDER BY date DESC, ro_number DESC")
    vehicles_df = read_table("SELECT unit, vin, mileage, status FROM vehicles ORDER BY unit")
    customers_df = read_table("SELECT customer_id, name FROM customers ORDER BY name")
    labor_rate_default = get_setting("labor_rate", 130.0)

    if ro_df.empty:
        st.info("No repair orders yet.")
    else:
        st.dataframe(ro_df, use_container_width=True, hide_index=True)

    b1, b2, _ = st.columns([1, 1, 2])
    with b1:
        if st.button("➕ Create Repair Order", type="primary", use_container_width=True):
            st.session_state.show_create_ro = True
            st.session_state.edit_ro = None
    with b2:
        if st.button("✏️ Edit Selected RO", use_container_width=True, disabled=ro_df.empty):
            if not ro_df.empty:
                st.session_state.edit_ro = True
                st.session_state.show_create_ro = False

    # ── Create RO form ──
    if st.session_state.show_create_ro:
        st.markdown("---")
        st.markdown("#### Create Repair Order")

        unit_list = vehicles_df["unit"].astype(str).tolist() if not vehicles_df.empty else []
        cust_names = (
            customers_df["name"].astype(str).tolist() if not customers_df.empty else []
        )
        cust_options = ["— Walk-in / Other —"] + cust_names

        with st.form("create_ro_form"):
            r1, r2 = st.columns(2)
            with r1:
                ro_number = st.text_input("RO Number", value=next_ro_number())
                ro_date = st.date_input("Date", value=date.today())
                customer_sel = st.selectbox("Customer", cust_options)
                if customer_sel == "— Walk-in / Other —":
                    customer = st.text_input("Customer name", placeholder="Name")
                else:
                    customer = customer_sel
                    st.text_input("Customer name", value=customer, disabled=True)
            with r2:
                unit = st.selectbox(
                    "Unit",
                    ["— None —"] + unit_list if unit_list else ["— None —"],
                )
                # Pre-fill VIN / odometer from vehicle
                pre_vin, pre_odo = "", 0
                if unit != "— None —" and not vehicles_df.empty:
                    match = vehicles_df[vehicles_df["unit"].astype(str) == unit]
                    if not match.empty:
                        pre_vin = str(match.iloc[0].get("vin") or "")
                        pre_odo = int(match.iloc[0].get("mileage") or 0)
                vin = st.text_input("VIN", value=pre_vin)
                odometer = st.number_input("Odometer", min_value=0, value=pre_odo, step=1)
                status = st.selectbox("Status", ["Open", "In Progress", "Completed", "Closed"])

            customer_states = st.text_area(
                "Customer complaint / stated issues",
                placeholder="What the customer reported…",
            )
            diagnostic_notes = st.text_area(
                "Diagnostic notes",
                placeholder="Technician findings…",
            )

            st.markdown("**Labor & parts**")
            l1, l2, l3 = st.columns(3)
            with l1:
                labor_hours = st.number_input(
                    "Labor hours", min_value=0.0, value=1.0, step=0.5, format="%.1f"
                )
            with l2:
                labor_rate = st.number_input(
                    "Labor rate ($/hr)",
                    min_value=0.0,
                    value=float(labor_rate_default),
                    step=5.0,
                    format="%.2f",
                )
            with l3:
                parts_total = st.number_input(
                    "Parts total ($)", min_value=0.0, value=0.0, step=1.0, format="%.2f"
                )

            labor_total = round(labor_hours * labor_rate, 2)
            shop_supply = round((labor_total + parts_total) * 0.05, 2)  # 5% shop supply
            grand_total = round(labor_total + parts_total + shop_supply, 2)

            st.caption(
                f"Labor total: **${labor_total:,.2f}** · Shop supply (5%): **${shop_supply:,.2f}** · "
                f"**Grand total: ${grand_total:,.2f}**"
            )

            s1, s2 = st.columns(2)
            with s1:
                submit_ro = st.form_submit_button(
                    "💾 Save Repair Order", type="primary", use_container_width=True
                )
            with s2:
                cancel_ro = st.form_submit_button("Cancel", use_container_width=True)

        if cancel_ro:
            st.session_state.show_create_ro = False
            st.rerun()

        if submit_ro:
            if not ro_number.strip():
                st.error("RO number is required.")
            elif not (customer or "").strip():
                st.error("Customer is required.")
            else:
                unit_val = "" if unit == "— None —" else unit
                try:
                    with get_conn() as conn:
                        exists = conn.execute(
                            "SELECT ro_number FROM repair_orders WHERE ro_number = ?",
                            (ro_number.strip(),),
                        ).fetchone()
                        if exists:
                            st.error(f"RO **{ro_number}** already exists.")
                        else:
                            conn.execute(
                                """
                                INSERT INTO repair_orders (
                                    ro_number, date, customer, unit, vin, odometer,
                                    customer_states, diagnostic_notes, labor_hours, labor_rate,
                                    parts_total, labor_total, shop_supply, total, status
                                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                                """,
                                (
                                    ro_number.strip(),
                                    str(ro_date),
                                    customer.strip(),
                                    unit_val,
                                    (vin or "").strip().upper(),
                                    int(odometer),
                                    customer_states or "",
                                    diagnostic_notes or "",
                                    float(labor_hours),
                                    float(labor_rate),
                                    float(parts_total),
                                    float(labor_total),
                                    float(shop_supply),
                                    float(grand_total),
                                    status,
                                ),
                            )
                            # Optionally update vehicle mileage
                            if unit_val and odometer:
                                conn.execute(
                                    "UPDATE vehicles SET mileage = ? WHERE unit = ?",
                                    (int(odometer), unit_val),
                                )
                            st.success(f"✅ Repair order **{ro_number.strip()}** created.")
                            st.session_state.show_create_ro = False
                            st.rerun()
                except Exception as e:
                    st.error(f"Could not create RO: {e}")

    # ── Edit RO ──
    if st.session_state.edit_ro and not ro_df.empty:
        st.markdown("---")
        st.markdown("#### Edit Repair Order")
        ro_list = ro_df["ro_number"].astype(str).tolist()
        selected_ro = st.selectbox("Select RO", ro_list, key="edit_ro_select")
        row = ro_df[ro_df["ro_number"].astype(str) == selected_ro]
        if not row.empty:
            ro = row.iloc[0]
            status_opts = ["Open", "In Progress", "Completed", "Closed"]
            cur_status = str(ro.get("status") or "Open")
            status_idx = status_opts.index(cur_status) if cur_status in status_opts else 0

            with st.form("edit_ro_form"):
                new_status = st.selectbox("Status", status_opts, index=status_idx)
                new_notes = st.text_area(
                    "Diagnostic Notes",
                    value=str(ro.get("diagnostic_notes") or ""),
                )
                new_customer_states = st.text_area(
                    "Customer complaint / stated issues",
                    value=str(ro.get("customer_states") or ""),
                )
                e1, e2, e3 = st.columns(3)
                with e1:
                    labor_hours = st.number_input(
                        "Labor hours",
                        min_value=0.0,
                        value=float(ro.get("labor_hours") or 0),
                        step=0.5,
                        format="%.1f",
                    )
                with e2:
                    labor_rate = st.number_input(
                        "Labor rate ($/hr)",
                        min_value=0.0,
                        value=float(ro.get("labor_rate") or labor_rate_default),
                        step=5.0,
                        format="%.2f",
                    )
                with e3:
                    parts_total = st.number_input(
                        "Parts total ($)",
                        min_value=0.0,
                        value=float(ro.get("parts_total") or 0),
                        step=1.0,
                        format="%.2f",
                    )

                labor_total = round(labor_hours * labor_rate, 2)
                shop_supply = round((labor_total + parts_total) * 0.05, 2)
                grand_total = round(labor_total + parts_total + shop_supply, 2)
                st.caption(
                    f"Labor: **${labor_total:,.2f}** · Shop supply: **${shop_supply:,.2f}** · "
                    f"Total: **${grand_total:,.2f}**"
                )

                s1, s2 = st.columns(2)
                with s1:
                    save_ro = st.form_submit_button(
                        "💾 Save Changes", type="primary", use_container_width=True
                    )
                with s2:
                    cancel_edit_ro = st.form_submit_button("Cancel", use_container_width=True)

            if cancel_edit_ro:
                st.session_state.edit_ro = None
                st.rerun()

            if save_ro:
                try:
                    with get_conn() as conn:
                        conn.execute(
                            """
                            UPDATE repair_orders SET
                                status=?, diagnostic_notes=?, customer_states=?,
                                labor_hours=?, labor_rate=?, parts_total=?,
                                labor_total=?, shop_supply=?, total=?
                            WHERE ro_number=?
                            """,
                            (
                                new_status,
                                new_notes or "",
                                new_customer_states or "",
                                float(labor_hours),
                                float(labor_rate),
                                float(parts_total),
                                float(labor_total),
                                float(shop_supply),
                                float(grand_total),
                                selected_ro,
                            ),
                        )
                    st.success(f"✅ RO **{selected_ro}** updated.")
                    st.session_state.edit_ro = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")

    # ── Generate invoice from RO ──
    st.markdown("---")
    st.markdown("#### Generate Invoice from RO")
    if ro_df.empty:
        st.caption("Create a repair order first.")
    else:
        billable = ro_df[ro_df["status"].isin(["Completed", "Closed", "In Progress", "Open"])]
        ro_choices = billable["ro_number"].astype(str).tolist()
        inv_ro = st.selectbox("Select RO to invoice", ro_choices, key="invoice_from_ro")
        ro_row = billable[billable["ro_number"].astype(str) == inv_ro]
        if not ro_row.empty:
            r = ro_row.iloc[0]
            st.markdown(
                f"""
                <div class="sft-card">
                    <strong>{r.get('ro_number')}</strong> · {r.get('customer')} · Unit {r.get('unit') or '—'}<br/>
                    Status: {r.get('status')} · Total: <strong>${float(r.get('total') or 0):,.2f}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
            terms = st.selectbox(
                "Payment terms",
                ["Due on Receipt", "Net 15", "Net 30", "Net 45"],
                index=2,
                key="inv_terms_from_ro",
            )
            terms_days = {"Due on Receipt": 0, "Net 15": 15, "Net 30": 30, "Net 45": 45}[terms]
            if st.button(
                "📄 Generate Invoice",
                type="primary",
                key="gen_invoice_btn",
            ):
                # Prevent duplicate invoice for same RO (unpaid/paid already linked)
                with get_conn() as conn:
                    existing = conn.execute(
                        "SELECT invoice_number FROM invoices WHERE ro_number = ?",
                        (inv_ro,),
                    ).fetchone()
                    if existing:
                        st.warning(
                            f"Invoice **{existing['invoice_number']}** already exists for this RO."
                        )
                    else:
                        inv_num = next_invoice_number()
                        inv_date = date.today()
                        due = inv_date + timedelta(days=terms_days)
                        total = float(r.get("total") or 0)
                        customer = str(r.get("customer") or "")
                        conn.execute(
                            """
                            INSERT INTO invoices
                            (invoice_number, date, ro_number, customer, total, status, payment_terms, due_date)
                            VALUES (?,?,?,?,?,?,?,?)
                            """,
                            (
                                inv_num,
                                str(inv_date),
                                inv_ro,
                                customer,
                                total,
                                "Unpaid",
                                terms,
                                str(due),
                            ),
                        )
                        # Mark RO completed when invoiced if still open
                        if str(r.get("status")) in ("Open", "In Progress"):
                            conn.execute(
                                "UPDATE repair_orders SET status = ? WHERE ro_number = ?",
                                ("Completed", inv_ro),
                            )
                        st.success(
                            f"✅ Invoice **{inv_num}** created for RO **{inv_ro}** "
                            f"(${total:,.2f}, due {due})."
                        )
                        st.rerun()


# ═════════════════════════════════════════════
# INVENTORY
# ═════════════════════════════════════════════
elif menu == "Inventory":
    st.subheader("📋 Inventory")

    inv_df = read_table("SELECT * FROM inventory ORDER BY part_number")
    if inv_df.empty:
        st.info("No parts in inventory.")
    else:
        st.dataframe(inv_df, use_container_width=True, hide_index=True)

    with st.expander("➕ Add / Update Part", expanded=False):
        with st.form("add_part_form"):
            p1, p2 = st.columns(2)
            with p1:
                pn = st.text_input("Part Number *")
                name = st.text_input("Part Name *")
                category = st.selectbox(
                    "Category",
                    ["General", "Filters", "Brakes", "Electrical", "Fluids", "Tires", "Other"],
                )
            with p2:
                qty = st.number_input("Quantity", min_value=0, value=0, step=1)
                cost = st.number_input("Unit Cost ($)", min_value=0.0, value=0.0, step=0.5, format="%.2f")
                markup = st.number_input(
                    "Markup %", min_value=0.0, value=45.0, step=5.0, format="%.1f"
                )
            retail = round(cost * (1 + markup / 100.0), 2)
            st.caption(f"Retail price will be **${retail:,.2f}**")
            if st.form_submit_button("Save Part", type="primary"):
                if not pn.strip() or not name.strip():
                    st.error("Part number and name are required.")
                else:
                    with get_conn() as conn:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO inventory
                            (part_number, part_name, qty, unit_cost, retail_price, category)
                            VALUES (?,?,?,?,?,?)
                            """,
                            (
                                pn.strip(),
                                name.strip(),
                                int(qty),
                                float(cost),
                                float(retail),
                                category,
                            ),
                        )
                    st.success(f"✅ Part **{pn.strip()}** saved.")
                    st.rerun()


# ═════════════════════════════════════════════
# CUSTOMERS
# ═════════════════════════════════════════════
elif menu == "Customers":
    st.subheader("👥 Customers")

    cust_df = read_table("SELECT * FROM customers ORDER BY name")
    if cust_df.empty:
        st.info("No customers yet.")
    else:
        st.dataframe(cust_df, use_container_width=True, hide_index=True)

    with st.expander("➕ Add Customer", expanded=False):
        with st.form("add_customer_form"):
            c1, c2 = st.columns(2)
            with c1:
                cid = st.text_input("Customer ID *", placeholder="e.g. C-001")
                name = st.text_input("Customer Name *")
                contact = st.text_input("Contact person")
            with c2:
                phone = st.text_input("Phone")
                email = st.text_input("Email")
                vins = st.text_input("Associated VINs", placeholder="Comma-separated")
            if st.form_submit_button("Save Customer", type="primary"):
                if not cid.strip() or not name.strip():
                    st.error("Customer ID and name are required.")
                else:
                    with get_conn() as conn:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO customers
                            (customer_id, name, contact, phone, email, vins)
                            VALUES (?,?,?,?,?,?)
                            """,
                            (
                                cid.strip(),
                                name.strip(),
                                contact or "",
                                phone or "",
                                email or "",
                                vins or "",
                            ),
                        )
                    st.success(f"✅ Customer **{name.strip()}** saved.")
                    st.rerun()


# ═════════════════════════════════════════════
# INVOICES
# ═════════════════════════════════════════════
elif menu == "Invoices":
    st.subheader("📦 Invoices")

    inv_df = read_table("SELECT * FROM invoices ORDER BY date DESC, invoice_number DESC")
    if inv_df.empty:
        st.info("No invoices yet. Generate one from a Repair Order or create manually.")
    else:
        st.dataframe(inv_df, use_container_width=True, hide_index=True)

        # Mark paid
        unpaid = inv_df[inv_df["status"].isin(["Unpaid", "Partial", "Overdue"])]
        if not unpaid.empty:
            st.markdown("#### Update Invoice Status")
            inv_sel = st.selectbox(
                "Invoice",
                unpaid["invoice_number"].astype(str).tolist(),
                key="inv_status_select",
            )
            new_status = st.selectbox(
                "New status",
                ["Unpaid", "Partial", "Paid", "Overdue", "Void"],
                key="inv_new_status",
            )
            if st.button("Update Status", type="primary", key="upd_inv_status"):
                with get_conn() as conn:
                    conn.execute(
                        "UPDATE invoices SET status = ? WHERE invoice_number = ?",
                        (new_status, inv_sel),
                    )
                st.success(f"✅ Invoice **{inv_sel}** → {new_status}")
                st.rerun()

    with st.expander("➕ Create Manual Invoice", expanded=False):
        with st.form("new_invoice_form"):
            inv_num = st.text_input("Invoice #", value=next_invoice_number())
            customer = st.text_input("Customer")
            ro_link = st.text_input("Linked RO # (optional)")
            total = st.number_input("Total ($)", min_value=0.0, value=0.0, step=1.0, format="%.2f")
            terms = st.selectbox(
                "Payment terms",
                ["Due on Receipt", "Net 15", "Net 30", "Net 45"],
                index=2,
            )
            if st.form_submit_button("Create Invoice", type="primary"):
                if not inv_num.strip() or not customer.strip():
                    st.error("Invoice number and customer are required.")
                else:
                    days = {
                        "Due on Receipt": 0,
                        "Net 15": 15,
                        "Net 30": 30,
                        "Net 45": 45,
                    }[terms]
                    try:
                        with get_conn() as conn:
                            exists = conn.execute(
                                "SELECT 1 FROM invoices WHERE invoice_number = ?",
                                (inv_num.strip(),),
                            ).fetchone()
                            if exists:
                                st.error("Invoice number already exists.")
                            else:
                                conn.execute(
                                    """
                                    INSERT INTO invoices
                                    (invoice_number, date, ro_number, customer, total, status, payment_terms, due_date)
                                    VALUES (?,?,?,?,?,?,?,?)
                                    """,
                                    (
                                        inv_num.strip(),
                                        str(date.today()),
                                        (ro_link or "").strip(),
                                        customer.strip(),
                                        float(total),
                                        "Unpaid",
                                        terms,
                                        str(date.today() + timedelta(days=days)),
                                    ),
                                )
                                st.success(f"✅ Invoice **{inv_num.strip()}** created.")
                                st.rerun()
                    except Exception as e:
                        st.error(f"Could not create invoice: {e}")


# ═════════════════════════════════════════════
# SETTINGS
# ═════════════════════════════════════════════
elif menu == "Settings":
    st.subheader("⚙️ Settings")

    st.markdown("#### Shop rates")
    current_rate = get_setting("labor_rate", 130.0)
    new_rate = st.number_input(
        "Default labor rate ($/hr)",
        min_value=0.0,
        value=float(current_rate),
        step=5.0,
        format="%.2f",
    )
    if st.button("Save Labor Rate", type="primary"):
        set_setting("labor_rate", float(new_rate))
        st.success(f"✅ Labor rate updated to **${new_rate:,.2f}/hr**")

    st.markdown("---")
    st.markdown("#### Change password")
    with st.form("change_password_form"):
        current_pw = st.text_input("Current password", type="password")
        new_pw = st.text_input("New password", type="password")
        confirm_pw = st.text_input("Confirm new password", type="password")
        if st.form_submit_button("Update Password", type="primary"):
            if not current_pw or not new_pw:
                st.error("Fill in all password fields.")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match.")
            elif len(new_pw) < 6:
                st.error("New password must be at least 6 characters.")
            else:
                user = authenticate(st.session_state.username, current_pw)
                if not user:
                    st.error("Current password is incorrect.")
                else:
                    with get_conn() as conn:
                        conn.execute(
                            "UPDATE users SET password_hash = ? WHERE username = ?",
                            (hash_pwd(new_pw), st.session_state.username),
                        )
                    st.success("✅ Password updated.")

    st.markdown("---")
    st.markdown("#### About")
    st.markdown(
        f"""
        <div class="sft-card">
            <strong>SFT SYSTEMS LLC</strong> — Fleet Management System<br/>
            <span class="sft-muted">Database: {DB_PATH}</span><br/>
            <span class="sft-muted">Logged in as {st.session_state.username} ({st.session_state.role})</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
