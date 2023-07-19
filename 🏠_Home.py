import streamlit_authenticator as stauth
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from helper_functions import (
    setup_page,
    read_db,
    backup_message_history,
    get_tokens,
    update_tokens,
)
from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.callbacks import get_openai_callback
import os


def main():
    # Setup page title and hide pages from the side bar
    setup_page()

    # At the beginning of the session, read the credentials
    # stored in the user table in the user_data DB
    credentials = read_db()
    # Retrieve the cookie key stored as an environmet variable
    cookie_key = os.environ["app_cookie_key"]

    # Create an authenticator object with all the initial values
    # that we retrieved
    authenticator = stauth.Authenticate(
        credentials, "angel_gallardo", cookie_key, 30, {"emails": None}
    )

    # If the authenticator object is not stored in the session,
    # then save it so that it is available to all the pages
    if "authenticator" not in st.session_state:
        st.session_state["authenticator"] = authenticator

    # Create the login Stramlit object so that any user needs to be
    # logged in to use the Web App
    name, authentication_status, username = authenticator.login("Login", "main")

    # If the user does not authenticate correctly, show the user
    # some additional options
    if authentication_status == False:
        # Tell him that his credentials were not correct
        st.error("Username / password is incorrect")
        register_column, forgotten_user_column, forgotten_pass_column = st.columns(3)

        # Add a register user button, if clicked, it will switch
        # to the register page
        with register_column:
            register = st.button("Not a user yet?", use_container_width=True)
            if register:
                switch_page("register")

        # Add a forgot username? button, if clicked, it will switch
        # to the forgotten_user page
        with forgotten_user_column:
            user = st.button("Forgot your username?", use_container_width=True)
            if user:
                switch_page("forgotten_user")

        # Add a forgotten password? button, if clicked, it will switch
        # to the forgotten_pass page
        with forgotten_pass_column:
            password = st.button("Forgot your password?", use_container_width=True)
            if password:
                switch_page("forgotten_pass")

    # If the user has not inputed anything
    if authentication_status == None:
        # Remind the user that he needs to login to use the WebApp
        st.warning("Please enter your username and password")

        # Add a register user button, if clicked, it will switch
        # to the register page
        register = st.button("Not a user yet? Register for free")
        if register:
            switch_page("register")

    # When the user authenticates correctly
    if authentication_status:
        # Store the variable username in the session
        st.session_state["username"] = username
        # Welcome the username in the sidebar
        st.sidebar.title(f"Welcome back {username}")

        # Fetch the tokens available
        tokens_available = get_tokens(username)
        # Create an empty object so that it is possible to
        # refresh the token value when needed
        token_placeholder = st.sidebar.empty()
        token_placeholder.write(f"Token balance: {tokens_available}")

        # Add a reset password button, if clicked, it will switch
        # to the reset_pass page
        reset_pass = st.sidebar.button("Reset pass", use_container_width=True)
        if reset_pass:
            switch_page("reset_pass")
        st.text("")
        # Add a logout button, if clicked, it will log out the user
        # and reset the web app to the initial state
        authenticator.logout("Logout", "sidebar")

        # For the AI demo, create a template that will describe to your
        # AI LLM what to do witht he prompt that the user had
        # For this case, we want to keep a history of what the user
        # has asked before and so, we tell him he needs to consider that
        # history as well as the prompt

        template = """Assistant is a large language model trained by OpenAI.

        Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

        Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

        Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.

        {history}
        Human: {human_input}
        Assistant:"""

        # Using LangChain we create a Template so that the LLM knows what are the
        # input variables he will receive as well as the prompt template
        prompt = PromptTemplate(
            input_variables=["history", "human_input"], template=template
        )

        # Now, we need to create the chain, which we will save into the session state
        # of Streamlit at the beginning, so that it does not reset every time we ask
        # something new in a session

        if "chatgpt_chain" not in st.session_state:
            # For this chain, we tell LangChain to use the OpenAI model,
            # the prompt template and to use a buffer memory so that the
            # LLM has the history available
            st.session_state["chatgpt_chain"] = LLMChain(
                llm=OpenAI(temperature=0),
                prompt=prompt,
                verbose=True,
                memory=ConversationBufferWindowMemory(k=2),
            )

        # Save all the messages in the session at the beggining
        # Start with a message from the robot to salute the user
        if "messages" not in st.session_state:
            st.session_state["messages"] = [
                {"role": "assistant", "content": "How can I help you?"}
            ]

        # Here we print all the messages in the conversation
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        # When the user has asked something
        if prompt := st.chat_input():
            # We save that message to the messages variable
            st.session_state.messages.append({"role": "user", "content": prompt})
            # Print the question the user asked
            st.chat_message("user").write(prompt)
            # Check if the user has tokens available to complete the operation
            if tokens_available > 0:
                # If he does, with this method we can monitor how many tokens
                # the current request will charge
                with get_openai_callback() as cb:
                    # Here is where we call the LLM to answer the question
                    output = st.session_state["chatgpt_chain"].predict(
                        human_input=prompt
                    )
                    # With the new answer, we update the token table to the current balance
                    update_tokens(username, tokens_available - cb.total_tokens)
                    # Update the current tokens in the sidebar for the user to know
                    tokens_available = get_tokens(username)
                    token_placeholder.empty()
                    token_placeholder.write(f"Token balance: {tokens_available}")
                # Format the response to append to the message session variable
                msg = {"role": "assistant", "content": output}
                st.session_state.messages.append(msg)
                # Print the response for the user to see
                st.chat_message("assistant").write(msg["content"])
                # Sabe the last two piece conversation to the history table in the DB
                backup_message_history(username, f"User:{prompt} AI:{output}")
            # If the user doesn't have enough tokens, remind the user that he should buy more
            else:
                st.chat_message("assistant").write(
                    f"You have run out of tokens 🥲\nPlease consider buying more!"
                )


if __name__ == "__main__":
    main()
