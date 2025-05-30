import asyncio

import streamlit as st

from config.config_manager import ConfigManager
from services.service import BackendService

config_manager = ConfigManager("frontend/src/config/config.yml")
config = config_manager.get_config().get('app')

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
        if "ai_model" not in st.session_state:
            st.session_state.ai_model = config.get('default_model')
        if "temperature" not in st.session_state:
            st.session_state.temperature = 1

    def display_sidebar(self):
        with st.sidebar:
            st.title(config.get('settings_title'))

            # Model selection
            available_models = config.get('ai_models')
            default_model_index = 0
            try:
                default_model_index = available_models.index(*config.get('default_model'))
            except ValueError:
                print("no model found that matches the default model, defaulting to 0")

            st.session_state.ai_model = st.selectbox(
                "Select model",
                 available_models,
                 index = default_model_index,
                 format_func= lambda x: x['model']
            )
            st.session_state.temperature = st.slider(label="temperature",min_value=0.0,max_value=2.0,step=0.05)




    def display_chat(self):
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input()
        if prompt:
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            try:
                print({'question': prompt,
                        'model': st.session_state.ai_model['model'],
                        'company': st.session_state.ai_model['company'],
                         'temperature': st.session_state.temperature})
                response_data = asyncio.run(
                    service
                    .post_data('chat', {
                        'question': prompt,
                        'model': st.session_state.ai_model['model'],
                        'company': st.session_state.ai_model['company'],
                        'temperature': st.session_state.temperature
                    })
                )
                response = f"{response_data}"
            except Exception as e:
                response = f"Error: {str(e)}"

            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})


    def run(self):
        st.title("DnD bot")
        self.display_sidebar()
        self.display_chat()


if __name__ == "__main__":
    app = FrontendApp()
    app.run()