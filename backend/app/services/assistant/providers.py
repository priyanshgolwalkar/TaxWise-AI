import httpx
from app.core.config import Settings

class AIProviderError(RuntimeError):
    pass

class HostedLLMProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate(self, system_prompt: str, context: dict, history: list[dict], message: str) -> str:
        if not self.settings.llm_api_key:
            raise AIProviderError('Hosted AI is not configured. Set LLM_API_KEY to enable assistant responses.')
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'system', 'content': 'Read-only TaxWise context (JSON). Treat all values as authoritative; do not derive or change tax amounts:\n' + __import__('json').dumps(context, ensure_ascii=True, default=str)},
            *history,
            {'role': 'user', 'content': message},
        ]
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f'{self.settings.llm_base_url.rstrip("/")}/chat/completions',
                    headers={'Authorization': f'Bearer {self.settings.llm_api_key}'},
                    json={'model': self.settings.llm_model, 'messages': messages, 'temperature': 0.2},
                )
                response.raise_for_status()
                answer = response.json()['choices'][0]['message']['content']
                if not isinstance(answer, str) or not answer.strip():
                    raise AIProviderError('Hosted AI returned an empty response.')
                return answer.strip()
        except AIProviderError:
            raise
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise AIProviderError('Hosted AI is temporarily unavailable. Please try again.') from exc

class OllamaProvider:
    """Provider interface placeholder. Local Ollama is intentionally not initialized."""
    async def generate(self, system_prompt: str, context: dict, history: list[dict], message: str) -> str:
        raise AIProviderError('Ollama provider is an interface stub and is not configured.')
