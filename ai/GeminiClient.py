from google import genai
from typing import List, Dict, Optional
try:
    from .LLMProvider import LLMProvider
except ImportError:
    from LLMProvider import LLMProvider

class GeminiClient(LLMProvider):
    """
    Advanced Gemini Client implementation.
    Uses the new 'google-genai' SDK (2026 standard).
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        # The new SDK uses a unified Client object
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate_response(self, prompt: str, system_instruction: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """
        Sends a request to Google Gemini and returns the text content.
        """
        try:
            # Note: temperature and max_output_tokens are passed via config
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    'system_instruction': system_instruction,
                    'temperature': temperature,
                    'max_output_tokens': max_tokens,
                }
            )
            
            # The SDK returns a response object where .text is a quick accessor
            if response.text:
                return response.text
            else:
                return "Gemini Error: No text returned (possible safety block)."
                
        except Exception as e:
            return f"Gemini SDK Error: {str(e)}"

    def get_model_info(self) -> str:
        return f"Provider: Google | Model: {self.model}"