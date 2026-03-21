from typing import Dict
try:
    from .LLMProvider import LLMProvider
    from .ChatGPTClient import ChatGPTClient
    from .ClaudeClient import ClaudeClient
    from .DeepSeekClient import DeepSeekClient
    from .GeminiClient import GeminiClient
except ImportError:
    from LLMProvider import LLMProvider
    from ChatGPTClient import ChatGPTClient
    from ClaudeClient import ClaudeClient
    from DeepSeekClient import DeepSeekClient
    from GeminiClient import GeminiClient

class MultiAIManager:
    """
    Orchestrates multiple LLM providers.
    Allows for structured comparison and parallel execution.
    """
    def __init__(self):
        self.clients: Dict[str, LLMProvider] = {}

    def add_client(self, name: str, client: LLMProvider):
        self.clients[name.lower()] = client

    def ask_all(self, prompt: str) -> Dict[str, str]:
        """Queries all registered clients and returns their responses."""
        results = {}
        for name, client in self.clients.items():
            results[name] = client.generate_response(prompt)
        return results

# --- SETUP & USAGE EXAMPLE ---
if __name__ == "__main__":
    manager = MultiAIManager()
    # Populate with keys if needed
    # manager.add_client("deepseek", DeepSeekClient(api_key="..."))
    # manager.add_client("gpt", ChatGPTClient(api_key="..."))
    # results = manager.ask_all("Hello World")
    # print(results)