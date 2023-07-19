import streamlit as st
import streamlit_authenticator as stauth
import time
from streamlit_extras.switch_page_button import switch_page
from helper_functions import setup_page, update_forgotten_pass

# Setup page title and hide pages from the side bar
setup_page()

# Retrieve the variables that we will use from the session state
# If the variables are not available for some reason, return to home immediately
try:
    authenticator = st.session_state["authenticator"]
    username = st.session_state["username"]
except:
    switch_page("home")


try:
    # Add a reset password widget for the user to reset the password
    if authenticator.reset_password(username, "Reset password"):
        hashed_pass = authenticator.credentials["usernames"][username]["password"]
        email = authenticator.credentials["usernames"][username]["email"]
        # Update the changed password in the user table in the user_data DB
        update_forgotten_pass(hashed_pass, email, username)
        # Tell the user the password was modified and return them home after 5 seconds
        st.success("Password modified successfully")
        with st.spinner("Automatically redirecting..."):
            time.sleep(5)
        switch_page("home")
# Show the user the error that happened while changing passwords
except Exception as e:
    st.error(e)
