import os
from datetime import datetime, timedelta

import requests
import streamlit as st

API_URL = f"{os.getenv('API_BASE_URL', 'http://localhost:8000/api').rstrip('/')}/auth"


def save_auth_cookies(cookie_manager, auth_data, email):
    options = {"expires_at": datetime.now() + timedelta(days=30), "same_site": "lax"}
    cookie_manager.set("auth_token", auth_data["access_token"], key="set_token", **options)
    cookie_manager.set("refresh_token", auth_data["refresh_token"], key="set_refresh_token", **options)
    cookie_manager.set("user_email", email, key="set_email", **options)
    cookie_manager.set("user_id", auth_data["user_id"], key="set_id", **options)


def clear_auth_cookies(cookie_manager):
    for name in ("auth_token", "refresh_token", "user_email", "user_id"):
        if name in cookie_manager.cookies:
            cookie_manager.delete(name, key=f"delete_{name}")

def render_auth_ui(cookie_manager):
    st.markdown("<h2 style='text-align: center; margin-bottom: 1rem;'>🔒 Access Control</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a6adc8;'>Log in or register to access the Plagiarism Analysis Platform</p>", unsafe_allow_html=True)
    
    _, login_column, _ = st.columns([1, 2, 1])

    with login_column:
        tab_login, tab_signup = st.tabs(["🔑 Login", "📝 Register"])
        
        # --- LOGIN TAB ---
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email Address", placeholder="student@university.edu")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submit_login = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit_login:
                    if not email or not password:
                        st.error("Please fill in both email and password.")
                    else:
                        try:
                            res = requests.post(
                                f"{API_URL}/login",
                                json={"email": email, "password": password},
                                timeout=5
                            )
                            if res.status_code == 200:
                                data = res.json()
                                token = data["access_token"]
                                user_id = data["user_id"]
                                
                                save_auth_cookies(cookie_manager, data, email)

                                st.session_state["authenticated"] = True
                                st.session_state["auth_restore_checked"] = True
                                st.session_state["user_token"] = token
                                st.session_state["user_id"] = user_id
                                st.session_state["user_email"] = email
                                
                                st.success("Logged in successfully!")
                                st.rerun()
                            else:
                                err_detail = res.json().get("detail", "Invalid credentials")
                                st.error(f"Login Failed: {err_detail}")
                        except Exception as e:
                            st.error(f"Backend offline: {str(e)}")

        # --- SIGNUP TAB ---
        with tab_signup:
            with st.form("signup_form"):
                full_name = st.text_input("Full Name", placeholder="Karan Ahuja")
                signup_email = st.text_input("Email Address", placeholder="karan@university.edu")
                signup_password = st.text_input("Password", type="password", placeholder="At least 6 characters")
                submit_signup = st.form_submit_button("Create Account", use_container_width=True)
                
                if submit_signup:
                    if not signup_email or not signup_password:
                        st.error("Please provide email and password.")
                    elif len(signup_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    else:
                        try:
                            res = requests.post(
                                f"{API_URL}/signup",
                                json={
                                    "email": signup_email,
                                    "password": signup_password,
                                    "full_name": full_name
                                },
                                timeout=5
                            )
                            if res.status_code == 200:
                                st.success("Account created successfully! Please log in now.")
                            else:
                                err_detail = res.json().get("detail", "Signup failed")
                                st.error(f"Registration Error: {err_detail}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")