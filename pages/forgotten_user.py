import streamlit as st
import time
from streamlit_extras.switch_page_button import switch_page
from helper_functions import setup_page, send_email_user

# Setup page title and hide pages from the side bar
setup_page()

# Retrieve the variables that we will use from the session state
# If the variables are not available for some reason, return to home immediately
try:
    authenticator = st.session_state["authenticator"]
except:
    switch_page("home")


try:
    # Create a widget for the user to retrieve it's username
    # When they use it correctly, you will get the forgotten username and the email
    username_forgot_username, email_forgot_username = authenticator.forgot_username(
        "Forgot username"
    )
    if username_forgot_username:
        # Send via email the forgotten username
        send_email_user(username_forgot_username, email_forgot_username)
        # Tell the user was found correctly and return them home after 5 seconds
        with st.spinner("Automatically redirecting..."):
            st.success("Username sent securely")
            time.sleep(5)
        switch_page("home")
    # Tell the user when the email is not found
    else:
        st.error("Email not found")

# Show the user the error that happened while trying to retreive the username
except Exception as e:
    st.error(e)
