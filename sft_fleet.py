import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sqlite3
import hashlib
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

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
    st.header("Vehicles - SFT Fleet")
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
                new_notes = st.text_area("Diagnostic Notes")
                if st.form_submit_button("Save Changes"):
                    c.execute("UPDATE repair_orders SET status=?, diagnostic_notes=? WHERE ro_number=?", (new_status, new_notes, selected))
                    conn.commit()
                    st.success("✅ Updated!")

# Inventory with PDF Export
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

    if st.button("📄 Export Inventory to PDF"):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(1*inch, 10*inch, "SFT SYSTEMS LLC - Inventory List")
        p.setFont("Helvetica", 12)
        p.drawString(1*inch, 9.7*inch, "9811 West State Rd 2, La Porte, IN 46350")
        y = 9*inch
        for _, row in df.iterrows():
            p.drawString(1*inch, y, f"{row['part_number']} - {row['part_name']} | Qty: {row['qty']} | Cost: ${row['unit_cost']}")
            y -= 0.3*inch
        p.save()
        buffer.seek(0)
        st.download_button("Download Inventory PDF", buffer, "inventory.pdf", "application/pdf")

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

# Invoices - Professional
elif menu == "Invoices":
    st.header("SFT SYSTEMS LLC - Invoices")
    st.subheader("9811 West State Rd 2, La Porte, IN 46350 | (219) 785-0042")
    df = pd.read_sql("SELECT * FROM invoices", conn)
    st.dataframe(df, use_container_width=True)

    with st.expander("Create Professional Invoice"):
        inv_num = st.text_input("Invoice #", f"INV-{date.today().strftime('%Y%m%d')}")
        customer = st.text_input("Bill To")
        total = st.number_input("Total Amount $", 0.0)
        terms = st.selectbox("Payment Terms", ["Due on Receipt", "Net 15", "Net 30"])
        if st.button("Generate PDF Invoice"):
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.setFont("Helvetica-Bold", 20)
            p.drawString(1*inch, 10*inch, "SFT SYSTEMS LLC")
            p.setFont("Helvetica", 12)
            p.drawString(1*inch, 9.7*inch, "9811 West State Rd 2, La Porte, IN 46350")
            p.drawString(1*inch, 9.4*inch, "Phone: 219-785-0042")
            p.drawString(1*inch, 8.5*inch, f"Invoice #: {inv_num}")
            p.drawString(1*inch, 8*inch, f"Bill To: {customer}")
            p.drawString(1*inch, 7*inch, f"Total Due: ${total:,.2f}")
            p.drawString(1*inch, 6.5*inch, f"Terms: {terms}")
            p.save()
            buffer.seek(0)
            st.download_button("📥 Download Professional Invoice PDF", buffer, f"{inv_num}.pdf", "application/pdf")

st.sidebar.success(f"Logged in as: {st.session_state.username}")
