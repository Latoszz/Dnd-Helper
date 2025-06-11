import streamlit as st

class SessionStateManager:
    def __init__(self, config):
        self.config = config

    def initialize(self):
        self._initialize_messages()

    def _initialize_messages(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []


    @staticmethod
    def get_messages():
        return st.session_state.messages

    @staticmethod
    def add_message(role, content):
        st.session_state.messages.append({"role": role, "content": content})

    @staticmethod
    def get_ai_model():
        return st.session_state.ai_model

    @staticmethod
    def get_ai_model_name():
        return SessionStateManager.get_ai_model()['model']

    @staticmethod
    def get_ai_model_provider():
        return SessionStateManager.get_ai_model()['provider']

    @staticmethod
    def get_temperature():
        return st.session_state.temperature
