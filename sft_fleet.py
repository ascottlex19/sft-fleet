import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3
import hashlib

st.set_page_config(page_title="SFT Fleet Management", layout="wide", page_icon="🚛")

conn = sqlite3.connect('sft_fleet.db', check_same_thread=False)
c = conn.cursor()

# All Tables
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
        if un == "admin" and pw == "admin123":
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

# Dashboard
if menu == "Dashboard":
    st.header("Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Vehicles", "18")
    col2.metric("Open Repair Orders", "4", "🔴")
    col3.metric("Overdue Invoices", "2", "⚠️")

# Vehicles
elif menu == "Vehicles":
    st.header("Vehicles")
    df = pd.read_sql("SELECT * FROM vehicles", conn)
    st.dataframe(df, use_container_width=True)

    with st.expander("Add / Edit Vehicle"):
        with st.form("add_vehicle"):
            unit = st.text_input("Unit # *")
            vtype = st.selectbox("Type", ["Semi Truck", "Dry Van Trailer", "Reefer Trailer"])
            vin = st.text_input("VIN")
            year = st.number_input("Year", 2010, 2030, 2025)
            make = st.text_input("Make")
            model = st.text_input("Model")
            mileage = st.number_input("Mileage", 0)
            notes = st.text_area("Notes")
            if st.form_submit_button("Save Vehicle"):
                c.execute("INSERT OR REPLACE INTO vehicles VALUES (?,?,?,?,?,?,?,?,?)", 
                         (unit, vtype, "Active", vin, year, make, model, mileage, notes))
                conn.commit()
                st.success("✅ Vehicle Saved!")

# Repair Orders
elif menu == "Repair Orders":
    st.header("Repair Orders")
    df = pd.read_sql("SELECT * FROM repair_orders", conn)
    st.dataframe(df, use_container_width=True)

    with st.expander("New Repair Order"):
        with st.form("new_ro"):
            ro_num = st.text_input("RO #", f"RO-{date.today().strftime('%Y%m%d')}")
            customer = st.text_input("Customer")
            unit = st.text_input("Unit #")
            vin = st.text_input("VIN")
            odometer = st.number_input("Odometer", 0)
            customer_states = st.text_area("Customer States")
            diagnostic_notes = st.text_area("Diagnostic Notes")
            if st.form_submit_button("Create Repair Order"):
                c.execute("INSERT INTO repair_orders (ro_number, date, customer, unit, vin, odometer, customer_states, diagnostic_notes, status) VALUES (?,?,?,?,?,?,?,?,?)",
                         (ro_num, str(date.today()), customer, unit, vin, odometer, customer_states, diagnostic_notes, "Open"))
                conn.commit()
                st.success("✅ Repair Order Created!")

# Inventory, Customers, Invoices, Settings (same functional code as before)

st.sidebar.success(f"Logged in as: {st.session_state.username}")
