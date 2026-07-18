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

c.executescript('''
CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT, full_name TEXT);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value REAL);
CREATE TABLE IF NOT EXISTS vehicles (unit TEXT PRIMARY KEY, type TEXT, status TEXT, vin TEXT, year INTEGER, make TEXT, model TEXT, mileage INTEGER, 
    dot_due DATE, plate_exp DATE, insurance_exp DATE, pm_interval INTEGER, grease1_interval INTEGER, grease2_interval INTEGER, notes TEXT);
CREATE TABLE IF NOT EXISTS inventory (part_number TEXT PRIMARY KEY, part_name TEXT, qty INTEGER, unit_cost REAL, retail_price REAL, category TEXT);
CREATE TABLE IF NOT EXISTS customers (customer_id TEXT PRIMARY KEY, name TEXT, contact TEXT, phone TEXT, email TEXT);
CREATE TABLE IF NOT EXISTS repair_orders (ro_number TEXT PRIMARY KEY, date TEXT, customer TEXT, unit TEXT, vin TEXT, odometer INTEGER, 
    customer_states TEXT, diagnostic_notes TEXT, labor_hours REAL, labor_rate REAL, parts_total REAL, labor_total REAL, 
    shop_supply REAL, total REAL, status TEXT DEFAULT 'Open');
CREATE TABLE IF NOT EXISTS invoices (invoice_number TEXT PRIMARY KEY, date TEXT, ro_number TEXT, customer TEXT, total REAL, status TEXT);
''')

def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?)", ("admin", hash_pwd("admin123"), "Admin", "Administrator"))
    c.execute("INSERT OR IGNORE INTO settings VALUES (?,?)", ("labor_rate", 130.0))
    conn.commit()

# Login (same)
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
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
        else: st.error("❌ Invalid login")

if not st.session_state.logged_in:
    login()
    st.stop()

# Navigation
st.title("🚛 SFT SYSTEMS LLC - Fleet Management System")
cols = st.columns(7)
if cols[0].button("🏠 Dashboard", use_container_width=True, type="primary"): st.session_state.menu = "Dashboard"
if cols[1].button("🚚 Vehicles", use_container_width=True, type="primary"): st.session_state.menu = "Vehicles"
if cols[2].button("🔧 Repair Orders", use_container_width=True, type="primary"): st.session_state.menu = "Repair Orders"
if cols[3].button("📦 Purchase Orders", use_container_width=True, type="primary"): st.session_state.menu = "Purchase Orders"
if cols[4].button("📋 Inventory", use_container_width=True, type="primary"): st.session_state.menu = "Inventory"
if cols[5].button("👥 Customers", use_container_width=True, type="primary"): st.session_state.menu = "Customers"
if cols[6].button("⚙️ Settings", use_container_width=True, type="primary"): st.session_state.menu = "Settings"

if 'menu' not in st.session_state: st.session_state.menu = "Dashboard"
menu = st.session_state.menu

# Settings
if menu == "Settings":
    st.header("System Settings")
    current = c.execute("SELECT value FROM settings WHERE key='labor_rate'").fetchone()[0]
    new_rate = st.number_input("Default Labor Rate ($/hr)", value=float(current), step=5.0)
    if st.button("Save Labor Rate"):
        c.execute("UPDATE settings SET value=? WHERE key='labor_rate'", (new_rate,))
        conn.commit()
        st.success(f"Labor Rate updated to ${new_rate}")

# Repair Orders - Improved
if menu == "Repair Orders":
    st.header("Repair Orders")
    tab1, tab2 = st.tabs(["Open Repair Orders", "New / Edit"])

    with tab1:
        df = pd.read_sql("SELECT * FROM repair_orders WHERE status != 'Completed'", conn)
        st.dataframe(df, use_container_width=True)
        ro_to_delete = st.selectbox("Delete Repair Order", [""] + df['ro_number'].tolist() if not df.empty else [])
        if ro_to_delete and st.button("🗑️ Delete Selected"):
            c.execute("DELETE FROM repair_orders WHERE ro_number=?", (ro_to_delete,))
            conn.commit()
            st.success("Deleted!")

    with tab2:
        ro_num = st.text_input("Repair Order #", f"RO-{date.today().strftime('%Y%m%d')}")
        customer = st.text_input("Customer Name")
        unit = st.text_input("Unit #")
        vin = st.text_input("VIN")
        odometer = st.number_input("Odometer", 0)
        customer_states = st.text_area("Customer States")
        diagnostic_notes = st.text_area("Diagnostic Notes")

        labor_rate = c.execute("SELECT value FROM settings WHERE key='labor_rate'").fetchone()[0]
        labor_hours = st.number_input("Labor Hours", 0.0, step=0.5)
        labor_total = labor_hours * labor_rate

        st.subheader("Parts")
        inventory = pd.read_sql("SELECT part_number, part_name, unit_cost FROM inventory", conn)
        total_parts = 0.0
        selected_parts = []
        num_parts = st.number_input("Number of Parts", 1, 8, 3)
        for i in range(num_parts):
            col1, col2 = st.columns([3,1])
            part = col1.selectbox(f"Part {i+1}", [""] + inventory['part_number'].tolist(), key=f"part{i}")
            if part:
                qty = col2.number_input("Qty", 1, key=f"qty{i}")
                cost = inventory[inventory.part_number == part]['unit_cost'].iloc[0]
                total_parts += cost * qty
                selected_parts.append(part)

        shop_supply = min(total_parts * 0.10, 150)
        grand_total = labor_total + total_parts + shop_supply

        st.write(f"**Labor:** ${labor_total:.2f} | **Parts:** ${total_parts:.2f} | **Shop Supply:** ${shop_supply:.2f}")
        st.write(f"**Grand Total:** ${grand_total:.2f}")

        col1, col2, col3 = st.columns(3)
        if col1.button("💾 Save"):
            c.execute("""INSERT OR REPLACE INTO repair_orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (ro_num, str(date.today()), customer, unit, vin, odometer, customer_states, diagnostic_notes,
                 labor_hours, labor_rate, total_parts, labor_total, shop_supply, grand_total, 'Open'))
            conn.commit()
            st.success("Saved!")

        if col2.button("✅ Complete to Invoice"):
            inv = f"INV-{date.today().strftime('%Y%m%d')}"
            c.execute("INSERT INTO invoices VALUES (?,?,?,?,?,?)", (inv, str(date.today()), ro_num, customer, grand_total, "Unpaid"))
            c.execute("UPDATE repair_orders SET status='Completed' WHERE ro_number=?", (ro_num,))
            conn.commit()
            st.success(f"Invoice {inv} created!")

# Invoices with Reverse Button
elif menu == "Invoices":
    st.header("SFT SYSTEMS LLC")
    st.subheader("9811 West State Rd 2, La Porte, IN 46350")
    st.subheader("Phone: 219-785-0042")
    df = pd.read_sql("SELECT * FROM invoices", conn)
    st.dataframe(df, use_container_width=True)

    inv_to_reverse = st.selectbox("Reverse Invoice Status", df['invoice_number'].tolist() if not df.empty else [])
    if inv_to_reverse and st.button("🔄 Reverse Status"):
        c.execute("UPDATE invoices SET status='Reversed' WHERE invoice_number=?", (inv_to_reverse,))
        conn.commit()
        st.success("Invoice status reversed!")

st.sidebar.success(f"👤 {st.session_state.username}")
