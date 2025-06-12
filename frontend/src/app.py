import asyncio

import streamlit as st

from components.chat import ChatComponent
from managers.config_manager import ConfigManager
from services.frontend_service import FrontendService
from components.sidebar import SidebarComponent
from managers.session_state_manager import SessionStateManager


class FrontendApp:

    def __init__(self):
        self._initialize_config_and_service()
        self._initialize_components()


    def _initialize_config_and_service(self):
        config_manager = ConfigManager("frontend/src/config/config.yml")
        self.config = config_manager.get_config().get('app')
        self.service = FrontendService(config_manager)
        st.set_page_config(
            page_title=self.config.get('title'),
            layout=self.config.get('layout')
        )

    def _initialize_components(self):
        self.chat = ChatComponent(self.service)
        self.sidebar = SidebarComponent(self.config,self.service)
   

    def run(self):
        SessionStateManager(self.config).initialize()

        self.sidebar.display()
        self.chat.display()


if __name__ == "__main__":
    app = FrontendApp()
    app.run()
