import os
import streamlit as st
from dotenv import load_dotenv
from config.config_manager import ConfigManager
from services.service import BackendService


config_manager = ConfigManager("config.yml")
config = config_manager.get_config().get('app',{})

service = BackendService()

class FrontendApp:

    def __init__(self):
        st.set_page_config(
            page_title=config.get('title'),
            layout=config.get('layout')
        )

    def run(self):
        st.title(config.get('app_title'))
        #st.sidebar()



if __name__ == "__main__":
    app = FrontendApp()
    app.run()