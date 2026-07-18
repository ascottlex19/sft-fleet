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
CREATE TABLE IF NOT EXISTS customers (customer_id TEXT PRIMARY KEY, name TEXT, contact TEXT, phone TEXT, email TEXT, vins TEXT);
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
    col1.metric("Active Vehicles", c.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] or 0)
    col2.metric("Open Repair Orders", c.execute("SELECT COUNT(*) FROM repair_orders WHERE status = 'Open'").fetchone()[0] or 0)
    col3.metric("Unpaid Invoices", c.execute("SELECT COUNT(*) FROM invoices WHERE status = 'Unpaid'").fetchone()[0] or 0)

# Vehicles
elif menu == "Vehicles":
    st.header("Vehicles")
    df = pd.read_sql("SELECT * FROM vehicles", conn)
    st.dataframe(df, use_container_width=True)
    with st.expander("Add New Vehicle"):
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
                c.execute("INSERT OR REPLACE INTO vehicles VALUES (?,?,?,?,?,?,?,?,?)", (unit, vtype, "Active", vin, year, make, model, mileage, notes))
                conn.commit()
                st.success("✅ Vehicle Saved!")

# Repair Orders - Click to Edit
elif menu == "Repair Orders":
    st.header("Repair Orders")
    df = pd.read_sql("SELECT ro_number, date, customer, unit, status FROM repair_orders", conn)
    st.dataframe(df, use_container_width=True)

    selected_ro = st.selectbox("Select Repair Order to Edit", df['ro_number'].tolist() if not df.empty else [""])
    if selected_ro:
        with st.expander("Edit Repair Order"):
            with st.form("edit_ro"):
                new_status = st.selectbox("Status", ["Open", "In Progress", "Completed"])
                new_notes = st.text_area("Update Diagnostic Notes")
                if st.form_submit_button("Save Changes"):
                    c.execute("UPDATE repair_orders SET status=?, diagnostic_notes=? WHERE ro_number=?", (new_status, new_notes, selected_ro))
                    conn.commit()
                    st.success("✅ Repair Order Updated!")

# Inventory - Click to Edit
elif menu == "Inventory":
    st.header("Inventory")
    df = pd.read_sql("SELECT * FROM inventory", conn)
    st.dataframe(df, use_container_width=True)

    selected_part = st.selectbox("Select Part to Edit", df['part_number'].tolist() if not df.empty else [""])
    if selected_part:
        with st.expander("Edit Part"):
            with st.form("edit_part"):
                name = st.text_input("Part Name")
                qty = st.number_input("Quantity", 0)
                cost = st.number_input("Unit Cost $", 0.0)
                if st.form_submit_button("Save Changes"):
                    retail = round(cost * 1.45, 2)
                    c.execute("UPDATE inventory SET part_name=?, qty=?, unit_cost=?, retail_price=? WHERE part_number=?", (name, qty, cost, retail, selected_part))
                    conn.commit()
                    st.success("✅ Part Updated!")

# Customers - Click to Edit
elif menu == "Customers":
    st.header("Customers")
    df = pd.read_sql("SELECT * FROM customers", conn)
    st.dataframe(df, use_container_width=True)

    selected_customer = st.selectbox("Select Customer to Edit", df['name'].tolist() if not df.empty else [""])
    if selected_customer:
        with st.expander("Edit Customer"):
            with st.form("edit_customer"):
                phone = st.text_input("Phone")
                email = st.text_input("Email")
                vins = st.text_input("VINS (comma separated)")
                if st.form_submit_button("Save Changes"):
                    c.execute("UPDATE customers SET phone=?, email=?, vins=? WHERE name=?", (phone, email, vins, selected_customer))
                    conn.commit()
                    st.success("✅ Customer Updated!")

# Invoices
elif menu == "Invoices":
    st.header("Invoices")
    df = pd.read_sql("SELECT * FROM invoices", conn)
    st.dataframe(df, use_container_width=True)

# Settings
elif menu == "Settings":
    st.header("Settings")
    rate_row = c.execute("SELECT value FROM settings WHERE key='labor_rate'").fetchone()
    current = float(rate_row[0]) if rate_row else 130.0
    new_rate = st.number_input("Labor Rate ($/hr)", value=current, step=5.0)
    if st.button("Save Labor Rate"):
        c.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", ("labor_rate", new_rate))
        conn.commit()
        st.success(f"✅ Labor Rate updated to ${new_rate}")

st.sidebar.success(f"Logged in as: {st.session_state.username}")
