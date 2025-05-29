from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

class LLMFactory:
    def __init__(self, config):
        self.config = config

    def get_model(self, model_name: str, temperature: float = 0.5):
        if model_name.startswith("gpt"):
            return ChatOpenAI(
                openai_api_key=self.config.open_ai_key,
                model=model_name,
                temperature=temperature,
            )
        elif model_name.startswith("gemini"):
            return ChatGoogleGenerativeAI(
                google_api_key=self.config.gemini_key,
                model=model_name,
                temperature=temperature,
            )
        else:
            raise ValueError(f"Unknown model: {model_name}")