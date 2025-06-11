import streamlit as st

from managers.session_state_manager import SessionStateManager


class SidebarComponent:

    def __init__(self, config):
        self.config = config

    def display(self):
        with st.sidebar:
            st.title(self.config.get('settings_title'))
            self._display_model_selection()
            self._display_temperature_slider()


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

    def _get_default_model_index(self, available_models):
        try:
            default_model = self.config.get('default_model')
            return available_models.index(default_model[0])
        except Exception as error:
            print("no model found that matches the default model, defaulting to 0")
            print(error)
            return 0

