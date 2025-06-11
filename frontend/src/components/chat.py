import asyncio
import streamlit as st

from services.frontend_service import FrontendService
from managers.session_state_manager import SessionStateManager

class ChatComponent:
    def __init__(self, frontend_service: FrontendService):
        self.service = frontend_service

    def display(self):
        self._display_chat_history()
        self._handle_user_input()

    def _display_chat_history(self):
        messages = SessionStateManager.get_messages()
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    def _handle_user_input(self):
        prompt = st.chat_input()
        if prompt:
            self._display_user_message(prompt)
            self._process_and_display_ai_response(prompt)

    def _display_user_message(self, prompt):
        with st.chat_message("user"):
            st.markdown(prompt)
        SessionStateManager.add_message("user", prompt)

    def _process_and_display_ai_response(self, prompt):
        try:
            response = self._get_ai_response(prompt)
        except Exception as e:
            response = f"Error: {str(e)}"

        with st.chat_message("assistant"):
            st.markdown(response)
        SessionStateManager.add_message("assistant", response)

    def _get_ai_response(self, prompt):
        ai_model = SessionStateManager.get_ai_model()
        temperature = SessionStateManager.get_temperature()

        request_data = {
            'question': prompt,
            'model': ai_model['model'],
            'provider': ai_model['provider'],
            'temperature': temperature
        }

        print(f"Sending request: {request_data}")

        response_data = asyncio.run(
            self.service.post_data('chat', request_data)
        )

        return str(response_data)

