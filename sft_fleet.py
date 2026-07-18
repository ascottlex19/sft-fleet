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

# Professional Styling
st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    h1, h2 {color: #1e3a8a;}
    .stButton>button {width: 100%; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ====================== LOGIN PAGE ======================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("logo.png", width=300)  # Your Sunfire Logo
        st.title("SFT SYSTEMS LLC")
        st.subheader("Fleet & Repair Management")
        
        un = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login", type="primary", use_container_width=True):
            # Simple login (expand later)
            if un == "admin" and pw == "admin123":
                st.session_state.logged_in = True
                st.session_state.username = un
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

# ====================== MAIN APP ======================
st.image("logo.png", width=180)  # Logo on main pages
st.title("SFT SYSTEMS LLC")
st.caption("**Professional Fleet Management & Repair Shop System**")

menu = st.sidebar.selectbox("Main Menu", ["Dashboard", "Repair Orders", "Invoices", "Inventory", "Customers", "Settings"])

# Dashboard
if menu == "Dashboard":
    st.header("Business Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Vehicles", "18")
    col2.metric("Open Repair Orders", "4", "🔴")
    col3.metric("Inventory Value", "$2,847")
    col4.metric("Monthly Revenue", "$14,250")

# Repair Orders (polished version from before)
elif menu == "Repair Orders":
    st.header("🔧 Repair Orders")
    # ... (your previous polished repair order code)

# Invoices with PDF
elif menu == "Invoices":
    st.header("SFT SYSTEMS LLC - Invoices")
    st.subheader("9811 West State Rd 2, La Porte, IN 46350 | (219) 785-0042")
    # ... (your invoice code)

st.sidebar.success(f"👤 {st.session_state.username}")
st.sidebar.caption("© Sunfire Transportation • SFT Systems LLC")
