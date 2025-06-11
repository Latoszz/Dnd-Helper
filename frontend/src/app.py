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

        self.session = SessionStateManager(self.config)
        st.set_page_config(
            page_title=self.config.get('title'),
            layout=self.config.get('layout')
        )

    def display_chat(self):
        for message in self.session.get_messages():
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input()
        if prompt:
            with st.chat_message("user"):
                st.markdown(prompt)
            self.session.add_message("user",prompt)

            try:
                print({'question': prompt,
                        'model': self.session.get_ai_model_name(),
                        'provider': self.session.get_ai_model_provider(),
                         'temperature': self.session.get_temperature()})
                response_data = asyncio.run(
                    self.service
                    .post_data('chat', {
                        'question': prompt,
                        'model': self.session.get_ai_model_name(),
                        'provider': self.session.get_ai_model_provider(),
                         'temperature': self.session.get_temperature()})
                )
                response = f"{response_data}"
            except Exception as e:
                response = f"Error: {str(e)}"

            with st.chat_message("assistant"):
                st.markdown(response)
            self.session.add_message("assistant",response)


    def run(self):
        st.title("DnD bot")

        self.session.initialize()
        self.sidebar.display()
        self.display_chat()


if __name__ == "__main__":
    app = FrontendApp()
    app.run()