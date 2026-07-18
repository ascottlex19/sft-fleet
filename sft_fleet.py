import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3
import hashlib
import requests

st.set_page_config(page_title="SFT Fleet Management", layout="wide", page_icon="🚛")

conn = sqlite3.connect('sft_fleet.db', check_same_thread=False)
c = conn.cursor()

# Force correct Vehicles table structure
c.execute("DROP TABLE IF EXISTS vehicles")
c.execute('''
CREATE TABLE vehicles (
    unit TEXT PRIMARY KEY, 
    type TEXT, 
    status TEXT, 
    vin TEXT, 
    year INTEGER, 
    make TEXT, 
    model TEXT, 
    mileage INTEGER, 
    plate_exp DATE, 
    insurance_exp DATE, 
    notes TEXT
)
''')
conn.commit()

# Other tables
c.executescript('''
CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT, full_name TEXT);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value REAL);
CREATE TABLE IF NOT EXISTS inventory (part_number TEXT PRIMARY KEY, part_name TEXT, qty INTEGER, unit_cost REAL, retail_price REAL, category TEXT);
CREATE TABLE IF NOT EXISTS customers (customer_id TEXT PRIMARY KEY, name TEXT, contact TEXT, phone TEXT, email TEXT, vins TEXT);
CREATE TABLE IF NOT EXISTS repair_orders (ro_number TEXT PRIMARY KEY, date TEXT, customer TEXT, unit TEXT, vin TEXT, odometer INTEGER, 
    customer_states TEXT, diagnostic_notes TEXT, labor_hours REAL, labor_rate REAL, parts_total REAL, labor_total REAL, 
    shop_supply REAL, total REAL, status TEXT DEFAULT 'Open');
CREATE TABLE IF NOT EXISTS invoices (invoice_number TEXT PRIMARY KEY, date TEXT, ro_number TEXT, customer TEXT, total REAL, status TEXT, payment_terms TEXT, due_date TEXT);
''')
conn.commit()

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
    st.header("🚚 Vehicles - SFT Fleet")
    
    st.subheader("Vehicle List")
    df = pd.read_sql("SELECT * FROM vehicles", conn)
    st.dataframe(df, use_container_width=True)

    if st.button("➕ Add New Vehicle"):
        st.session_state.show_add = True

    if st.session_state.get('show_add', False):
        st.subheader("New Vehicle Form")
        unit = st.text_input("Unit # *")
        vtype = st.selectbox("Type", ["Semi Truck", "Dry Van Trailer", "Reefer Trailer"])
        vin = st.text_input("VIN Number")
        if st.button("🔍 Lookup VIN & Auto-Fill"):
            if vin:
                try:
                    r = requests.get(f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json")
                    data = r.json()['Results']
                    year = next((x['Value'] for x in data if x['Variable'] == "Model Year"), "")
                    make = next((x['Value'] for x in data if x['Variable'] == "Make"), "")
                    model = next((x['Value'] for x in data if x['Variable'] == "Model"), "")
                    st.session_state.vin_year = int(year) if year.isdigit() else 2025
                    st.session_state.vin_make = make
                    st.session_state.vin_model = model
                    st.success(f"✅ Auto-filled: {year} {make} {model}")
                except:
                    st.error("Lookup failed")
        year = st.number_input("Year", 2010, 2030, value=st.session_state.get('vin_year', 2025))
        make = st.text_input("Make", value=st.session_state.get('vin_make', ''))
        model = st.text_input("Model", value=st.session_state.get('vin_model', ''))
        mileage = st.number_input("Mileage", 0)
        plate_exp = st.date_input("Plate Expiration", date.today())
        insurance_exp = st.date_input("Insurance Expiration", date.today())
        notes = st.text_area("Notes")
        col1, col2 = st.columns(2)
        if col1.button("Save New Vehicle"):
            c.execute("INSERT OR REPLACE INTO vehicles VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                     (unit, vtype, "Active", vin, year, make, model, mileage, plate_exp, insurance_exp, notes))
            conn.commit()
            st.success("✅ Vehicle Added!")
            st.session_state.show_add = False
            st.rerun()
        if col2.button("Cancel"):
            st.session_state.show_add = False
            st.rerun()

    st.subheader("Edit Vehicle")
    if not df.empty:
        selected_unit = st.selectbox("Select Unit Number to Edit", df['unit'].tolist())
        if st.button("Open Edit Form"):
            st.session_state.edit_unit = selected_unit

    if 'edit_unit' in st.session_state:
        vehicle = df[df['unit'] == st.session_state.edit_unit].iloc[0]
        st.subheader(f"Editing Unit: {st.session_state.edit_unit}")
        vtype = st.selectbox("Type", ["Semi Truck", "Dry Van Trailer", "Reefer Trailer"], index=0)
        vin = st.text_input("VIN", value=vehicle.get('vin', ''))
        year = st.number_input("Year", 2010, 2030, value=int(vehicle.get('year', 2025)))
        make = st.text_input("Make", value=vehicle.get('make', ''))
        model = st.text_input("Model", value=vehicle.get('model', ''))
        mileage = st.number_input("Mileage", 0, value=int(vehicle.get('mileage', 0)))
        plate_exp = st.date_input("Plate Expiration", value=vehicle.get('plate_exp', date.today()))
        insurance_exp = st.date_input("Insurance Expiration", value=vehicle.get('insurance_exp', date.today()))
        status = st.selectbox("Status", ["Active", "Inactive"])
        notes = st.text_area("Notes", value=vehicle.get('notes', ''))
        col1, col2 = st.columns(2)
        if col1.button("Save Changes"):
            c.execute("UPDATE vehicles SET type=?, vin=?, year=?, make=?, model=?, mileage=?, plate_exp=?, insurance_exp=?, status=?, notes=? WHERE unit=?", 
                     (vtype, vin, year, make, model, mileage, plate_exp, insurance_exp, status, notes, st.session_state.edit_unit))
            conn.commit()
            st.success("✅ Vehicle Updated!")
            del st.session_state.edit_unit
            st.rerun()
        if col2.button("Cancel"):
            del st.session_state.edit_unit
            st.rerun()

# Repair Orders
elif menu == "Repair Orders":
    st.header("Repair Orders")
    df = pd.read_sql("SELECT * FROM repair_orders", conn)
    st.dataframe(df, use_container_width=True)

    selected = st.selectbox("Select Repair Order to Edit", df['ro_number'].tolist() if not df.empty else [""])
    if selected:
        with st.expander("Edit Repair Order"):
            with st.form("edit_ro"):
                new_status = st.selectbox("Status", ["Open", "In Progress", "Completed"])
                nouotes = st.text_area("Diagnostic Notes")
                if st.form_submit_button("Save Changes"):
                    c.execute("UPDATE repair_orders SET status=?, diagnostic_notes=? WHERE ro_number=?", (new_status, new_notes, selected))
                    conn.commit()
                    st.success("✅ Updated!")

# Inventory
elif menu == "Inventory":
    st.header("Inventory")
    df = pd.read_sql("SELECT * FROM inventory", conn)
    st.dataframe(df, use_container_width=True)
    with st.expander("Add Part"):
        with st.form("add_part"):
            pn = st.text_input("Part Number")
            name = st.text_input("Part Name")
            qty = st.number_input("Quantity", 0)
            cost = st.number_input("Unit Cost $", 0.0)
            if st.form_submit_button("Save"):
                retail = round(cost * 1.45, 2)
                c.execute("INSERT OR REPLACE INTO inventory VALUES (?,?,?,?,?,?)", (pn, name, qty, cost, retail, "General"))
                conn.commit()
                st.success("✅ Part Saved!")

# Customers
elif menu == "Customers":
    st.header("Customers")
    df = pd.read_sql("SELECT * FROM customers", conn)
    st.dataframe(df, use_container_width=True)
    with st.expander("Add Customer"):
        with st.form("add_customer"):
            cid = st.text_input("Customer ID")
            name = st.text_input("Customer Name")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            if st.form_submit_button("Save"):
                c.execute("INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?,?)", (cid, name, "", phone, email, ""))
                conn.commit()
                st.success("✅ Customer Saved!")

# Invoices
elif menu == "Invoices":
    st.header("Invoices")
    df = pd.read_sql("SELECT * FROM invoices", conn)
    st.dataframe(df, use_container_width=True)
    with st.expander("Create Invoice"):
        with st.form("new_invoice"):
            inv_num = st.text_input("Invoice #", f"INV-{date.today().strftime('%Y%m%d')}")
            customer = st.text_input("Customer")
            total = st.number_input("Total $", 0.0)
            if st.form_submit_button("Create"):
                c.execute("INSERT INTO invoices VALUES (?,?,?,?,?,?,?,?)", (inv_num, str(date.today()), "", customer, total, "Unpaid", "Net 30", str(date.today() + timedelta(days=30))))
                conn.commit()
                st.success("✅ Invoice Created!")

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
