import streamlit as st
import pandas as pd
from datetime import date
import sqlite3
import hashlib
import os
import requests

st.set_page_config(page_title="SFT Fleet Management", layout="wide", page_icon="🚛")

os.makedirs("attachments/images", exist_ok=True)
os.makedirs("attachments/pdfs", exist_ok=True)

conn = sqlite3.connect('sft_fleet.db', check_same_thread=False)
c = conn.cursor()

# Fixed Tables
c.executescript('''
CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT, full_name TEXT);
CREATE TABLE IF NOT EXISTS vehicles (unit TEXT PRIMARY KEY, type TEXT, status TEXT, vin TEXT, year INTEGER, make TEXT, model TEXT, mileage INTEGER, 
    dot_due DATE, plate_exp DATE, insurance_exp DATE, pm_interval INTEGER, grease1_interval INTEGER, grease2_interval INTEGER, notes TEXT);
CREATE TABLE IF NOT EXISTS inventory (part_number TEXT PRIMARY KEY, part_name TEXT, qty INTEGER, unit_cost REAL, retail_price REAL, category TEXT);
CREATE TABLE IF NOT EXISTS customers (customer_id TEXT PRIMARY KEY, name TEXT, contact TEXT, phone TEXT, email TEXT);
CREATE TABLE IF NOT EXISTS work_orders (wo_number TEXT PRIMARY KEY, date TEXT, unit TEXT, description TEXT, status TEXT DEFAULT 'Open');
CREATE TABLE IF NOT EXISTS purchase_orders (po_number TEXT PRIMARY KEY, date TEXT, status TEXT DEFAULT 'Open', total REAL);
CREATE TABLE IF NOT EXISTS attachments (id INTEGER PRIMARY KEY, related_to TEXT, file_type TEXT, file_path TEXT, uploaded_date TEXT);
''')

def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
    defaults = [("admin", hash_pwd("admin123"), "Admin", "Administrator")]
    c.executemany("INSERT INTO users VALUES (?,?,?,?)", defaults)
    conn.commit()

# Login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🚛 SFT SYSTEMS LLC")
    st.subheader("Fleet Management Login")
    un = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login", type="primary"):
        if c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (un, hash_pwd(pw))).fetchone():
            st.session_state.logged_in = True
            st.session_state.username = un
            st.rerun()
        else:
            st.error("❌ Invalid login")

if not st.session_state.logged_in:
    login()
    st.stop()

# Bold Navigation
st.title("🚛 SFT SYSTEMS LLC - Fleet Management System")

col1, col2, col3, col4, col5, col6 = st.columns(6)
if col1.button("🏠 Dashboard", use_container_width=True, type="primary"): st.session_state.menu = "Dashboard"
if col2.button("🚚 Vehicles", use_container_width=True, type="primary"): st.session_state.menu = "Vehicles"
if col3.button("📦 Purchase Orders", use_container_width=True, type="primary"): st.session_state.menu = "Purchase Orders"
if col4.button("📋 Inventory", use_container_width=True, type="primary"): st.session_state.menu = "Inventory"
if col5.button("👥 Customers", use_container_width=True, type="primary"): st.session_state.menu = "Customers"
if col6.button("🔧 Work Orders", use_container_width=True, type="primary"): st.session_state.menu = "Work Orders"

if 'menu' not in st.session_state:
    st.session_state.menu = "Dashboard"

menu = st.session_state.menu

# Dashboard
if menu == "Dashboard":
    st.header("Fleet Overview")
    active = c.execute("SELECT COUNT(*) FROM vehicles WHERE status='Active'").fetchone()[0] or 0
    st.metric("Active Vehicles", active)

# Vehicles with VIN Lookup
elif menu == "Vehicles":
    st.header("Vehicles & Trailers")
    df = pd.read_sql("SELECT * FROM vehicles", conn)
    st.dataframe(df, use_container_width=True)

    with st.expander("➕ Add / Edit Vehicle"):
        with st.form("add_vehicle"):
            unit = st.text_input("Unit # *")
            vin = st.text_input("VIN Number")
            if st.form_submit_button("🔍 Lookup VIN") and vin:
                try:
                    r = requests.get(f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json", timeout=5)
                    data = r.json()
                    for item in data.get('Results', []):
                        if item['Variable'] == "Make" and item['Value']: st.session_state.vin_make = item['Value']
                        if item['Variable'] == "Model Year" and item['Value']: st.session_state.vin_year = int(item['Value'])
                        if item['Variable'] == "Model" and item['Value']: st.session_state.vin_model = item['Value']
                    st.success("✅ VIN information loaded!")
                except:
                    st.warning("Could not lookup VIN.")

            vtype = st.selectbox("Type", ["Semi Truck", "Dry Van Trailer", "Reefer Trailer"])
            year = st.number_input("Year", 2010, 2030, st.session_state.get('vin_year', 2025))
            make = st.text_input("Make", st.session_state.get('vin_make', "FRT"))
            model = st.text_input("Model", st.session_state.get('vin_model', "CASCADIA"))
            
            colA, colB = st.columns(2)
            dot_due = colA.date_input("DOT Due", date.today())
            plate_exp = colA.date_input("Plate Exp", date.today())
            insurance_exp = colB.date_input("Insurance Exp", date.today())
            pm_interval = colB.number_input("PM Interval (miles)", value=10000)
            grease1 = colA.number_input("Grease 1 Interval", value=5000)
            grease2 = colB.number_input("Grease 2 Interval", value=10000)

            if st.form_submit_button("Save Vehicle"):
                c.execute("""INSERT OR REPLACE INTO vehicles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (unit, vtype, "Active", vin, year, make, model, 0, dot_due, plate_exp, insurance_exp, pm_interval, grease1, grease2, ""))
                conn.commit()
                st.success(f"Vehicle {unit} saved!")

# Inventory
elif menu == "Inventory":
    st.header("Inventory")
    df = pd.read_sql("SELECT * FROM inventory", conn)
    st.dataframe(df, use_container_width=True)
    with st.expander("Add New Part"):
        with st.form("add_part"):
            pn = st.text_input("Part Number")
            name = st.text_input("Part Name")
            qty = st.number_input("Quantity", 0)
            cost = st.number_input("Unit Cost $", 0.0)
            if st.form_submit_button("Add Part"):
                retail = round(cost * 1.45, 2)
                c.execute("INSERT OR REPLACE INTO inventory VALUES (?,?,?,?,?,?)", (pn, name, qty, cost, retail, "General"))
                conn.commit()
                st.success("✅ Part added!")

# Customers - FIXED
elif menu == "Customers":
    st.header("Customers")
    df = pd.read_sql("SELECT * FROM customers", conn)
    st.dataframe(df, use_container_width=True)
    with st.expander("Add New Customer"):
        with st.form("add_customer"):
            cid = st.text_input("Customer ID")
            name = st.text_input("Customer Name")
            contact = st.text_input("Contact Person")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            if st.form_submit_button("Add Customer"):
                c.execute("INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?)", (cid, name, contact, phone, email))
                conn.commit()
                st.success("✅ Customer added!")

# Other sections
elif menu in ["Purchase Orders", "Work Orders"]:
    st.header(menu)
    st.info(f"{menu} module is ready for further expansion.")

st.sidebar.success(f"👤 {st.session_state.get('username', 'User')}")
