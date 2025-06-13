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
            print(st.session_state.is_streaming)
            if st.session_state.is_streaming:
                self._process_and_display_ai_response_stream(prompt)
            else:
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
            "question": prompt,
            "model": ai_model["model"],
            "provider": ai_model["provider"],
            "temperature": temperature,
        }

        print(f"Sending request: {request_data}")

        response_data = asyncio.run(self.service.post_data("chat", request_data))

        return str(response_data)

    def _process_and_display_ai_response_stream(self, prompt):
        with st.chat_message("assistant"):
            try:
                # Create a generator for the streaming response
                response_generator = self._get_ai_response_stream(prompt)

                # Use st.write_stream to display the streaming response
                full_response = st.write_stream(response_generator)

                # Store the complete response in session state
                SessionStateManager.add_message("assistant", full_response)

            except Exception as e:
                error_message = f"Error: {str(e)}"
                st.markdown(error_message)
                SessionStateManager.add_message("assistant", error_message)

    def _get_ai_response_stream(self, prompt):
        ai_model = SessionStateManager.get_ai_model()
        temperature = SessionStateManager.get_temperature()

        request_data = {
            "question": prompt,
            "model": ai_model["model"],
            "provider": ai_model["provider"],
            "temperature": temperature,
        }

        print(f"Sending streaming request: {request_data}")

        # Run the async streaming function in sync context
        return self._stream_response(request_data)

    async def _stream_response(self, request_data):
        try:
            async for chunk in self.service.stream_data("chat_stream", request_data):
                yield chunk
        except Exception as e:
            yield f"Error: {str(e)}"
