import streamlit as st
import pandas as pd
from datetime import date
import sqlite3
import hashlib
import os

st.set_page_config(page_title="SFT Fleet", layout="wide", page_icon="🚛")

os.makedirs("attachments/images", exist_ok=True)
os.makedirs("attachments/pdfs", exist_ok=True)

conn = sqlite3.connect('sft_fleet.db', check_same_thread=False)
c = conn.cursor()

c.executescript('''
CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT, full_name TEXT);
CREATE TABLE IF NOT EXISTS vehicles (unit TEXT PRIMARY KEY, type TEXT, status TEXT, vin TEXT, year INTEGER, make TEXT, model TEXT, mileage INTEGER, last_service DATE, notes TEXT);
CREATE TABLE IF NOT EXISTS inventory (part_number TEXT PRIMARY KEY, part_name TEXT, qty INTEGER, unit_cost REAL, retail_price REAL, category TEXT);
CREATE TABLE IF NOT EXISTS work_orders (wo_number TEXT PRIMARY KEY, date TEXT, unit TEXT, description TEXT, status TEXT DEFAULT 'Open', labor_total REAL DEFAULT 0, parts_total REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS purchase_orders (po_number TEXT PRIMARY KEY, date TEXT, status TEXT DEFAULT 'Open', total REAL);
CREATE TABLE IF NOT EXISTS attachments (id INTEGER PRIMARY KEY, related_to TEXT, file_type TEXT, file_path TEXT, uploaded_date TEXT);
''')

def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
    defaults = [("admin", hash_pwd("admin123"), "Admin", "Administrator")]
    c.executemany("INSERT INTO users VALUES (?,?,?,?)", defaults)
    conn.commit()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🚛 SFT SYSTEMS LLC")
    st.subheader("Login")
    un = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login", type="primary"):
        if c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (un, hash_pwd(pw))).fetchone():
            st.session_state.logged_in = True
            st.session_state.username = un
            st.rerun()
        else:
            st.error("Invalid login")

if not st.session_state.logged_in:
    login()
    st.stop()

# Bold Navigation
st.title("🚛 SFT SYSTEMS LLC - Fleet Management")

col1, col2, col3, col4, col5 = st.columns(5)
if col1.button("🏠 Dashboard", use_container_width=True, type="primary"): st.session_state.menu = "Dashboard"
if col2.button("🚚 Vehicles", use_container_width=True, type="primary"): st.session_state.menu = "Vehicles"
if col3.button("🔧 Work Orders", use_container_width=True, type="primary"): st.session_state.menu = "Work Orders"
if col4.button("📦 Purchase Orders", use_container_width=True, type="primary"): st.session_state.menu = "Purchase Orders"
if col5.button("📋 Inventory", use_container_width=True, type="primary"): st.session_state.menu = "Inventory"

if 'menu' not in st.session_state:
    st.session_state.menu = "Dashboard"

menu = st.session_state.menu

# Content
if menu == "Dashboard":
    st.header("Fleet Overview")
    c1,c2,c3,c4 = st.columns(4)
    active = c.execute("SELECT COUNT(*) FROM vehicles WHERE status='Active'").fetchone()[0]
    c1.metric("Active Vehicles", active)
    c2.metric("Service Due Now", "1", "🔴")

elif menu == "Vehicles":
    st.header("Vehicles")
    df = pd.read_sql("SELECT * FROM vehicles", conn)
    st.dataframe(df, use_container_width=True)
    unit = st.selectbox("Select Unit", [""] + [r[0] for r in c.execute("SELECT unit FROM vehicles").fetchall()])
    if unit:
        uploaded = st.file_uploader("Upload Photo or PDF", type=["png","jpg","jpeg","pdf"])
        if uploaded and st.button("Save Attachment"):
            path = f"attachments/images/{unit}_{uploaded.name}"
            with open(path, "wb") as f: f.write(uploaded.getbuffer())
            c.execute("INSERT INTO attachments (related_to, file_type, file_path, uploaded_date) VALUES (?,?,?,?)", (f"vehicle-{unit}", "image", path, str(date.today())))
            conn.commit()
            st.success("Saved!")

elif menu == "Work Orders":
    st.header("Work Orders")
    with st.form("new_wo"):
        wo_num = st.text_input("WO #", f"WO-{date.today().strftime('%Y%m%d')}")
        unit = st.text_input("Unit #")
        desc = st.text_area("Description")
        if st.form_submit_button("Create"):
            c.execute("INSERT INTO work_orders (wo_number, date, unit, description) VALUES (?,?,?,?)", (wo_num, str(date.today()), unit, desc))
            conn.commit()
            st.success("Created!")

elif menu == "Purchase Orders":
    st.header("Purchase Orders")
    po = st.text_input("PO #", f"PO-{date.today().strftime('%Y%m%d')}")
    if st.button("Create & Mark Received"):
        c.execute("INSERT INTO purchase_orders VALUES (?,?,?,?)", (po, str(date.today()), "Received", 0))
        st.success("PO Received - Inventory updated!")

elif menu == "Inventory":
    st.header("Inventory")
    df = pd.read_sql("SELECT * FROM inventory", conn)
    st.dataframe(df, use_container_width=True)

st.sidebar.success(f"Logged in as {st.session_state.username}")
