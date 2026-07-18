import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3
import hashlib

st.set_page_config(page_title="SFT Fleet Management", layout="wide", page_icon="🚛")

conn = sqlite3.connect('sft_fleet.db', check_same_thread=False)
c = conn.cursor()

# Database Tables
c.executescript('''
CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT, full_name TEXT);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value REAL);
CREATE TABLE IF NOT EXISTS vehicles (
    unit TEXT PRIMARY KEY, type TEXT, status TEXT, vin TEXT, year INTEGER, make TEXT, model TEXT, 
    mileage INTEGER, plate_exp DATE, insurance_exp DATE, notes TEXT
);
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

# Dashboard with Notifications
if menu == "Dashboard":
    st.header("Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Vehicles", c.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] or 0)
    col2.metric("Open Repair Orders", c.execute("SELECT COUNT(*) FROM repair_orders WHERE status = 'Open'").fetchone()[0] or 0)
    col3.metric("Unpaid Invoices", c.execute("SELECT COUNT(*) FROM invoices WHERE status = 'Unpaid'").fetchone()[0] or 0)

    st.subheader("⚠️ Expiring Soon (Next 30 Days)")
    expiring = pd.read_sql("""
        SELECT unit, type, plate_exp, insurance_exp 
        FROM vehicles 
        WHERE plate_exp <= date('now','+30 days') OR insurance_exp <= date('now','+30 days')
    """, conn)
    if not expiring.empty:
        st.warning("Vehicles needing attention:")
        st.dataframe(expiring)
    else:
        st.success("✅ No items expiring soon.")

elif menu == "Vehicles":
    st.header("🚚 Vehicles - SFT Fleet")
    
    # Vehicle List
    st.subheader("All Vehicles")
    df = pd.read_sql("SELECT unit, type, status, vin, year, make, model, mileage, plate_exp, insurance_exp FROM vehicles", conn)
    st.dataframe(df, use_container_width=True)

    # Edit Existing Vehicle
    if not df.empty:
        st.subheader("Edit Vehicle")
        selected_unit = st.selectbox("Select Unit # to Edit", df['unit'].tolist())
        if selected_unit:
            vehicle = df[df['unit'] == selected_unit].iloc[0]
            with st.form("edit_vehicle"):
                status = st.selectbox("Status", ["Active", "Inactive"], 
                                    index=0 if vehicle['status'] == "Active" else 1)
                notes = st.text_area("Notes", value=vehicle.get('notes', ''))
                if st.form_submit_button("Save Changes"):
                    c.execute("UPDATE vehicles SET status=?, notes=? WHERE unit=?", 
                             (status, notes, selected_unit))
                    conn.commit()
                    st.success("✅ Vehicle Updated!")
                    st.rerun()

    # Add New Vehicle with VIN Lookup
    st.subheader("Add New Vehicle")
    with st.form("new_vehicle"):
        col1, col2 = st.columns(2)
        unit = col1.text_input("Unit # *")
        vtype = col2.selectbox("Type", ["Semi Truck", "Dry Van Trailer", "Reefer Trailer"])

        vin = st.text_input("VIN Number")
        if st.button("🔍 Lookup VIN"):
            if vin:
                try:
                    r = requests.get(f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json")
                    data = r.json()['Results']
                    year = next((x['Value'] for x in data if x['Variable'] == "Model Year"), "")
                    make = next((x['Value'] for x in data if x['Variable'] == "Make"), "")
                    model = next((x['Value'] for x in data if x['Variable'] == "Model"), "")
                    engine = next((x['Value'] for x in data if x['Variable'] == "Engine Model"), "")
                    st.success(f"✅ Found: {year} {make} {model}")
                except:
                    st.error("VIN lookup failed. Enter manually.")

        year = st.number_input("Year", 2010, 2030, 2025)
        make = st.text_input("Make")
        model = st.text_input("Model")
        engine = st.text_input("Engine")
        mileage = st.number_input("Mileage", 0)
        plate_exp = st.date_input("License Plate Expiration", date.today())
        insurance_exp = st.date_input("Insurance Expiration", date.today())
        notes = st.text_area("Notes")

        if st.form_submit_button("Add New Vehicle"):
            c.execute("INSERT OR REPLACE INTO vehicles VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                     (unit, vtype, "Active", vin, year, make, model, engine, mileage, plate_exp, insurance_exp, notes))
            conn.commit()
            st.success("✅ New Vehicle Added!")
            st.rerun()
# Repair Orders
elif menu == "Repair Orders":
    st.header("Repair Orders")
    df = pd.read_sql("SELECT * FROM repair_orders", conn)
    st.dataframe(df, use_container_width=True)

    tab1, tab2 = st.tabs(["New Repair Order", "Edit Existing"])

    with tab1:
        with st.form("new_ro"):
            ro_num = st.text_input("RO #", f"RO-{date.today().strftime('%Y%m%d')}")
            customer = st.text_input("Customer")
            unit = st.text_input("Unit #")
            vin = st.text_input("VIN")
            odometer = st.number_input("Odometer", 0)
            customer_states = st.text_area("Customer States")
            labor_hours = st.number_input("Labor Hours", 0.0, step=0.25)
            st.subheader("Parts")
            inventory = pd.read_sql("SELECT part_number, unit_cost FROM inventory", conn)
            total_parts = 0
            for i in range(5):
                part = st.selectbox(f"Part {i+1}", [""] + inventory['part_number'].tolist(), key=f"part{i}")
                if part:
                    qty = st.number_input("Qty", 1, key=f"qty{i}")
                    cost = inventory[inventory.part_number == part]['unit_cost'].iloc[0]
                    total_parts += cost * qty
            if st.form_submit_button("Create Repair Order"):
                labor_total = labor_hours * 130
                shop_supply = min(total_parts * 0.1, 150)
                total = labor_total + total_parts + shop_supply
                c.execute("INSERT INTO repair_orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", 
                         (ro_num, str(date.today()), customer, unit, vin, odometer, customer_states, "", labor_hours, 130, total_parts, labor_total, shop_supply, total, "Open"))
                conn.commit()
                st.success("✅ New Repair Order Created!")

    with tab2:
        selected = st.selectbox("Select to Edit", df['ro_number'].tolist() if not df.empty else [""])
        if selected:
            with st.form("edit_ro"):
                new_status = st.selectbox("Status", ["Open", "In Progress", "Completed"])
                new_notes = st.text_area("Notes")
                if st.form_submit_button("Save"):
                    c.execute("UPDATE repair_orders SET status=?, diagnostic_notes=? WHERE ro_number=?", (new_status, new_notes, selected))
                    conn.commit()
                    st.success("✅ Saved!")

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
    with st.expander("Create Professional Invoice"):
        with st.form("new_invoice"):
            inv_num = st.text_input("Invoice #", f"INV-{date.today().strftime('%Y%m%d')}")
            customer = st.text_input("Bill To")
            total = st.number_input("Total Amount $", 0.0)
            if st.form_submit_button("Create Invoice"):
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
