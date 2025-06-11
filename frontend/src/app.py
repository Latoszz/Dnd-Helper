import asyncio

import streamlit as st

from managers.config_manager import ConfigManager
from services.frontend_service import FrontendService
from components.sidebar import SidebarComponent
from managers.session_state_manager import SessionStateManager

class FrontendApp:

    def __init__(self):
        config_manager = ConfigManager("frontend/src/config/config.yml")
        self.config = config_manager.get_config().get('app')
        self.service = FrontendService(config_manager)
        self.sidebar = SidebarComponent(self.config)
        st.set_page_config(
            page_title=self.config.get('title'),
            layout=self.config.get('layout')
        )

    def display_chat(self):
        messages = SessionStateManager.get_messages()
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input()
        if prompt:
            with st.chat_message("user"):
                st.markdown(prompt)
            SessionStateManager.add_message("user",prompt)
            ai_model = SessionStateManager.get_ai_model()
            temperature = SessionStateManager.get_temperature()
            try:
                request_data = {
                        'question': prompt,
                        'model': ai_model['model'],
                        'provider': ai_model['provider'],
                        'temperature': temperature}
                print(f"POST: {request_data}")
                response_data = asyncio.run(
                    self.service.post_data('chat', request_data)
                )

                response = f"{response_data}"
            except Exception as e:
                response = f"Error: {str(e)}"

            with st.chat_message("assistant"):
                st.markdown(response)
            SessionStateManager.add_message("assistant",response)


    def run(self):
        st.title("DnD bot")

        SessionStateManager(self.config).initialize()
        self.sidebar.display()
        self.display_chat()


if __name__ == "__main__":
    app = FrontendApp()
    app.run()