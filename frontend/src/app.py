import os
import streamlit as st
from dotenv import load_dotenv
from config.config_manager import ConfigManager
from services.service import BackendService


config_manager = ConfigManager("config.yml")
config = config_manager.get_config().get('app',{})

service = BackendService(config_manager)

class FrontendApp:

    def __init__(self):
        st.set_page_config(
            page_title=config.get('title'),
            layout=config.get('layout')
        )
        self._initialize_session_state()

    def _initialize_session_state(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []


    def display_sidebar(self):
        with st.sidebar:
            select_model = st.selectbox(config.get('default_model'),(config.get('models')))

    def display_chat(self):
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("What is up?"):
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

        response = f"Echo: {prompt}"
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})


    def run(self):
        #st.title(config.get('echo'))
        st.title("Echo bot")
        #st.sidebar()
        self.display_chat()


if __name__ == "__main__":
    app = FrontendApp()
    app.run()