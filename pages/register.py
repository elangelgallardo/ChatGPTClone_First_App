import streamlit as st
import time
from streamlit_extras.switch_page_button import switch_page
from st_pages import hide_pages
from helper_functions import setup_page, insert_user

# Setup page title and hide pages from the side bar
setup_page()

# Retrieve the variables that we will use from the session state
# If the variables are not available for some reason, return to home immediately
try:
    authenticator = st.session_state["authenticator"]
except:
    switch_page("home")

try:
    # Create a register widget for the user to register
    if authenticator.register_user("Register user", preauthorization=False):
        latest_user = list(authenticator.credentials["usernames"].keys())[-1]
        # Update the user table in the user_data DB to keep the credentials to date
        insert_user(latest_user, authenticator.credentials["usernames"][latest_user])
        # Tell the user was registered correctly and return them home after 5 seconds
        st.success("User registered successfully")
        with st.spinner("Automatically redirecting..."):
            time.sleep(5)
        switch_page("home")
# Show the user the error that happened while registering
except Exception as e:
    st.error(e)
