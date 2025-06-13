import asyncio

import streamlit as st

from services.frontend_service import FrontendService
from managers.session_state_manager import SessionStateManager


class SidebarComponent:

    def __init__(self, config,frontend_service):
        self.config = config
        self.service = frontend_service

    def display(self):
        with st.sidebar:
            st.title(self.config.get('settings_title'))
            self._display_model_selection()
            self._display_temperature_slider()
            self._display_file_upload()
            self._display_file_upload_button()
            self._display_is_streaming_toggle()


    def _display_temperature_slider(self):
        new_temp = st.slider(
            label="Temperature",
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            value=self.config.get('default_temperature'),
            key="temperature"
        )


    def _display_model_selection(self):
        available_models = self.config.get('ai_models')
        default_model_index = self._get_default_model_index(available_models)
        selected_model = st.selectbox(
            "Select model",
            available_models,
            index=default_model_index,
            format_func=lambda x: x['model'],
            key="ai_model"
        )
    def _display_file_upload(self):
        accepted_file_types= self.config.get('accepted_file_types')
        uploaded_file = st.file_uploader(
            "Upload your character sheet",
            type=accepted_file_types,
            key="uploaded_file"
        )

    def _get_default_model_index(self, available_models):
        try:
            default_model = self.config.get('default_model')
            return available_models.index(default_model[0])
        except Exception as error:
            print("no model found that matches the default model, defaulting to 0")
            print(error)
            return 0

    def _display_file_upload_button(self):
        st.button(
            "Send file",
            on_click=(lambda: asyncio.run(
                    self.service
                        .post_file('file', st.session_state.uploaded_file)
                ))
        )

    def _display_is_streaming_toggle(self):
        should_stream = st.toggle("Stream response", value=False, key="is_streaming")



