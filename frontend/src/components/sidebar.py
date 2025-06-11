import streamlit as st

class SidebarComponent:

    def __init__(self, config):
        self.config = config

    def display(self):
        with st.sidebar:
            st.title(self.config.get('settings_title'))
            self._display_model_selection()
            self._display_temperature_slider()


    def _display_temperature_slider(self):
        st.session_state.temperature = st.slider(
            label="temperature",
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            value=st.session_state.temperature
        )


    def _display_model_selection(self):
        available_models = self.config.get('ai_models')
        default_model_index = self._get_default_model_index(available_models)
        st.session_state.ai_model = st.selectbox(
            "Select model",
            available_models,
            index=default_model_index,
            format_func=lambda x: x['model']
        )

    def _get_default_model_index(self, available_models):
        try:
            default_model = self.config.get('default_model')
            return available_models.index(default_model[0])
        except Exception as error:
            print("no model found that matches the default model, defaulting to 0")
            print(error)
            return 0

