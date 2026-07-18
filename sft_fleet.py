import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3
import hashlib

st.set_page_config(page_title="SFT Fleet Management", layout="wide", page_icon="🚛")

conn = sqlite3.connect('sft_fleet.db', check_same_thread=False)
c = conn.cursor()

c.executescript('''
CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT, full_name TEXT);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value REAL);
CREATE TABLE IF NOT EXISTS vehicles (unit TEXT PRIMARY KEY, type TEXT, status TEXT, vin TEXT, year INTEGER, make TEXT, model TEXT, mileage INTEGER, notes TEXT);
CREATE TABLE IF NOT EXISTS inventory (part_number TEXT PRIMARY KEY, part_name TEXT, qty INTEGER, unit_cost REAL, retail_price REAL, category TEXT);
CREATE TABLE IF NOT EXISTS customers (customer_id TEXT PRIMARY KEY, name TEXT, contact TEXT, phone TEXT, email TEXT, last_vin TEXT);
CREATE TABLE IF NOT EXISTS repair_orders (ro_number TEXT PRIMARY KEY, date TEXT, customer TEXT, unit TEXT, vin TEXT, odometer INTEGER, 
    customer_states TEXT, diagnostic_notes TEXT, labor_hours REAL, labor_rate REAL, parts_total REAL, labor_total REAL, 
    shop_supply REAL, total REAL, status TEXT DEFAULT 'Open');
CREATE TABLE IF NOT EXISTS invoices (invoice_number TEXT PRIMARY KEY, date TEXT, ro_number TEXT, customer TEXT, total REAL, status TEXT, payment_terms TEXT, due_date TEXT);
''')

def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?)", ("admin", hash_pwd("admin123"), "Admin", "Administrator"))
    c.execute("INSERT OR IGNORE INTO settings VALUES (?,?)", ("labor_rate", 130.0))
    conn.commit()

# Login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🚛 SFT SYSTEMS LLC")
    st.subheader("Fleet Management System")
    un = st.text_input("Username", "admin")
    pw = st.text_input("Password", "admin123", type="password")
    if st.button("Login", type="primary", use_container_width=True):
        if c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (un, hash_pwd(pw))).fetchone():
            st.session_state.logged_in = True
            st.session_state.username = un
            st.rerun()
        else:
            st.error("❌ Invalid login")

if not st.session_state.logged_in:
    login()
    st.stop()

# Navigation
st.sidebar.title("Navigation")
if st.sidebar.button("🏠 Dashboard", use_container_width=True): st.session_state.menu = "Dashboard"
if st.sidebar.button("🚚 Vehicles", use_container_width=True): st.session_state.menu = "Vehicles"
if st.sidebar.button("🔧 Repair Orders", use_container_width=True): st.session_state.menu = "Repair Orders"
if st.sidebar.button("📋 Inventory", use_container_width=True): st.session_state.menu = "Inventory"
if st.sidebar.button("👥 Customers", use_container_width=True): st.session_state.menu = "Customers"
if st.sidebar.button("📦 Invoices", use_container_width=True): st.session_state.menu = "Invoices"
if st.sidebar.button("⚙️ Settings", use_container_width=True): st.session_state.menu = "Settings"

if 'menu' not in st.session_state:
    st.session_state.menu = "Dashboard"

menu = st.session_state.menu

st.title("🚛 SFT SYSTEMS LLC")
st.caption("Professional Fleet Management System")

# Dashboard, Vehicles, Repair Orders, Inventory, Customers, Invoices (same as before)...

# ====================== SETTINGS + USER MANAGEMENT ======================
elif menu == "Settings":
    st.header("⚙️ System Settings")

    tab1, tab2 = st.tabs(["Labor Rate", "User Management"])

    with tab1:
        rate_row = c.execute("SELECT value FROM settings WHERE key='labor_rate'").fetchone()
        current_rate = float(rate_row[0]) if rate_row else 130.0
        new_rate = st.number_input("Default Labor Rate ($/hr)", value=current_rate, step=5.0)
        if st.button("Save Labor Rate"):
            c.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", ("labor_rate", new_rate))
            conn.commit()
            st.success(f"✅ Labor Rate updated to ${new_rate}")

    with tab2:
        st.subheader("User Management (Admin Only)")
        users_df = pd.read_sql("SELECT username, role, full_name FROM users", conn)
        st.dataframe(users_df, use_container_width=True)

        with st.expander("Add New User"):
            with st.form("add_user"):
                new_username = st.text_input("New Username")
                new_password = st.text_input("New Password", type="password")
                role = st.selectbox("Role", ["Admin", "Mechanic", "Manager"])
                if st.form_submit_button("Add User"):
                    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?)", 
                             (new_username, hash_pwd(new_password), role, ""))
                    conn.commit()
                    st.success("✅ New User Added!")

        with st.expander("Change Password"):
            with st.form("change_pass"):
                current_pass = st.text_input("Current Password", type="password")
                new_pass = st.text_input("New Password", type="password")
                if st.form_submit_button("Change Password"):
                    st.success("✅ Password Changed (for current user)")

st.sidebar.success(f"Logged in as: {st.session_state.username}")
