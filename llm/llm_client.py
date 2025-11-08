import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")

            cls._instance = super().__new__(cls)
            cls._instance.client = genai.Client(api_key=gemini_api_key)
        return cls._instance

gemini_client = GeminiClient()