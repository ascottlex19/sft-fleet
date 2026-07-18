import streamlit as st
import pandas as pd
from datetime import date
import sqlite3
import hashlib

st.set_page_config(page_title="SFT Fleet Management", layout="wide", page_icon="🚛")

# Login Page
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    st.image("logo.png", width=280)
    st.title("SFT SYSTEMS LLC")
    st.subheader("Fleet & Repair Management")
    
    un = st.text_input("Username", value="admin")
    pw = st.text_input("Password", value="admin123", type="password")
    
    if st.button("Login", type="primary", use_container_width=True):
        if un == "admin" and pw == "admin123":
            st.session_state.logged_in = True
            st.session_state.username = un
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ====================== MAIN APP ======================
st.image("logo.png", width=180)
st.title("SFT SYSTEMS LLC")
st.caption("**Professional Fleet Management System**")

menu = st.sidebar.selectbox("Main Menu", ["Dashboard", "Repair Orders", "Invoices", "Inventory", "Customers"])

if menu == "Dashboard":
    st.header("Welcome Back")
    st.success("System is running smoothly!")

st.sidebar.success(f"Logged in as: {st.session_state.username}")
st.sidebar.caption("Sunfire Transportation • SFT Systems LLC")
