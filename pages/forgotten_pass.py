import streamlit as st
import streamlit_authenticator as stauth
import time
from streamlit_extras.switch_page_button import switch_page
from helper_functions import setup_page, send_email_pass, update_forgotten_pass

# Setup page title and hide pages from the side bar
setup_page()

# Retrieve the variables that we will use from the session state
# If the variables are not available for some reason, return to home immediately
try:
    authenticator = st.session_state["authenticator"]
except:
    switch_page("home")


try:
    # Create a widget for the user to retrieve it's password
    # When they use it correctly, you will get a new random password, the username and the email
    (
        username_forgot_pw,
        email_forgot_password,
        random_password,
    ) = authenticator.forgot_password("Forgot password")
    if username_forgot_pw:
        # Hash the randomly generated password and update the credentials with that
        hashed_pass = stauth.Hasher([random_password]).generate()[0]
        authenticator.credentials["usernames"][username_forgot_pw][
            "password"
        ] = hashed_pass
        # Update the DB with this newly generated password
        update_forgotten_pass(hashed_pass, email_forgot_password, username_forgot_pw)
        # Send the unhashed password to the user
        send_email_pass(random_password, email_forgot_password, username_forgot_pw)
        # Tell the user that his password was sent to his email and return them home after 5 seconds
        with st.spinner("Automatically redirecting..."):
            st.success("New password sent securely")
            time.sleep(5)
        switch_page("home")
    # Tell the user when the username is not found
    elif username_forgot_pw == False:
        st.error("Username not found")

# Show the user the error that happened while trying to retreive the password
except Exception as e:
    st.error(e)
