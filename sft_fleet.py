import streamlit as st
import pandas as pd
from datetime import date
import sqlite3
import hashlib

st.set_page_config(page_title="SFT Fleet Management", layout="wide", page_icon="🚛")

# Login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    st.title("🚛 SFT SYSTEMS LLC")
    st.subheader("Professional Fleet Management")
    un = st.text_input("Username", "admin")
    pw = st.text_input("Password", "admin123", type="password")
    if st.button("Login", type="primary"):
        if un == "admin" and pw == "admin123":
            st.session_state.logged_in = True
            st.session_state.username = un
            st.rerun()
        else:
            st.error("❌ Invalid login")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# Main App
st.title("🚛 SFT SYSTEMS LLC")
st.caption("**Fleet & Repair Management System**")

st.success("✅ System is running!")

menu = st.sidebar.selectbox("Menu", ["Dashboard", "Repair Orders", "Invoices"])

st.sidebar.success(f"Logged in as: {st.session_state.username}")
