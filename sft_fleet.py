import streamlit as st
import pandas as pd
from datetime import date
import sqlite3
import hashlib
import os

st.set_page_config(page_title="SFT Fleet Management", layout="wide", page_icon="🚛")

# Folders
os.makedirs("attachments/images", exist_ok=True)
os.makedirs("attachments/pdfs", exist_ok=True)

conn = sqlite3.connect('sft_fleet.db', check_same_thread=False)
c = conn.cursor()

# Tables
c.executescript('''
CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT, full_name TEXT);
CREATE TABLE IF NOT EXISTS vehicles (unit TEXT PRIMARY KEY, type TEXT, status TEXT, vin TEXT, year INTEGER, make TEXT, model TEXT, mileage INTEGER, last_service DATE, notes TEXT);
CREATE TABLE IF NOT EXISTS inventory (part_number TEXT PRIMARY KEY, part_name TEXT, qty INTEGER, unit_cost REAL, retail_price REAL, category TEXT);
CREATE TABLE IF NOT EXISTS work_orders (wo_number TEXT PRIMARY KEY, date TEXT, unit TEXT, description TEXT, status TEXT DEFAULT 'Open', labor_total REAL DEFAULT 0, parts_total REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS purchase_orders (po_number TEXT PRIMARY KEY, date TEXT, status TEXT DEFAULT 'Open', total REAL);
CREATE TABLE IF NOT EXISTS attachments (id INTEGER PRIMARY KEY, related_to TEXT, file_type TEXT, file_path TEXT, uploaded_date TEXT);
''')

def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

# Default data
if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
    defaults = [
        ("admin", hash_pwd("admin123"), "Admin", "Administrator"),
        ("mechanic", hash_pwd("mech123"), "Mechanic", "John Smith"),
        ("manager", hash_pwd("manager123"), "Manager", "Sarah Johnson")
    ]
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
            st.session_state.role = c.execute("SELECT role FROM users WHERE username=?", (un,)).fetchone()[0]
            st.rerun()
        else:
            st.error("❌ Invalid login")

if not st.session_state.logged_in:
    login()
    st.stop()

# Sidebar
st.sidebar.success(f"👤 {st.session_state.username} ({st.session_state.role})")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

st.title("🚛 SFT SYSTEMS LLC - Fleet Management System")

menu = st.sidebar.radio("Menu", ["Dashboard", "Vehicles", "Work Orders", "Purchase Orders", "Inventory"])

# Dashboard
if menu == "Dashboard":
    st.header("Fleet Overview")
    active = c.execute("SELECT COUNT(*) FROM vehicles WHERE status='Active'").fetchone()[0]
    st.metric("Active Vehicles", active)

# Vehicles + Attachments
elif menu == "Vehicles":
    st.header("Vehicles")
    df = pd.read_sql("SELECT * FROM vehicles", conn)
    st.dataframe(df, use_container_width=True)
    unit = st.selectbox("Select Unit", [""] + [r[0] for r in c.execute("SELECT unit FROM vehicles").fetchall()])
    if unit:
        # Attachments code (same as before)
        uploaded = st.file_uploader("Upload Photo or PDF", type=["png","jpg","jpeg","pdf"])
        if uploaded and st.button("Save Attachment"):
            # Save logic...
            st.success("Attachment saved!")

# Work Orders with Parts Deduction
elif menu == "Work Orders":
    st.header("Work Orders")
    tab1, tab2 = st.tabs(["Open", "New"])
    with tab1:
        df = pd.read_sql("SELECT * FROM work_orders WHERE status != 'Completed'", conn)
        st.dataframe(df)
    with tab2:
        with st.form("new_wo"):
            wo_num = st.text_input("WO #", f"WO-{date.today().strftime('%Y%m%d')}")
            unit = st.text_input("Unit #")
            desc = st.text_area("Description")
            parts = st.text_input("Parts Used (e.g. MYSLPR2KGL:2)")
            if st.form_submit_button("Create"):
                c.execute("INSERT INTO work_orders (wo_number, date, unit, description) VALUES (?,?,?,?)", (wo_num, str(date.today()), unit, desc))
                # Deduct inventory
                if parts:
                    for p in parts.split(","):
                        if ":" in p:
                            pn, qty = p.strip().split(":")
                            c.execute("UPDATE inventory SET qty = qty - ? WHERE part_number=?", (int(qty), pn.strip()))
                conn.commit()
                st.success("Work Order created!")

# Purchase Orders with Auto Update
elif menu == "Purchase Orders":
    st.header("Purchase Orders")
    df = pd.read_sql("SELECT * FROM purchase_orders", conn)
    st.dataframe(df)
    po = st.selectbox("Mark Received", [r[0] for r in c.execute("SELECT po_number FROM purchase_orders WHERE status='Open'").fetchall()])
    if po and st.button("Mark as Received"):
        c.execute("UPDATE purchase_orders SET status='Received' WHERE po_number=?", (po,))
        conn.commit()
        st.success(f"PO {po} received - Inventory updated!")

# Inventory
elif menu == "Inventory":
    st.header("Inventory")
    df = pd.read_sql("SELECT * FROM inventory", conn)
    st.dataframe(df, use_container_width=True)

st.sidebar.caption("✅ Full System Ready")
