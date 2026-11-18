import json

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
            {'role': 'system', 'content': 'Read-only TaxWise context (JSON). Treat all values as authoritative; do not derive or change tax amounts:\n' + json.dumps(context, ensure_ascii=True, default=str)},
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
                if response.status_code in {401, 403}:
                    raise AIProviderError('Hosted AI credentials were rejected. Check LLM_API_KEY.')
                if response.status_code == 429:
                    raise AIProviderError('Hosted AI rate limit or quota reached. Please try again later.')
                response.raise_for_status()
                try:
                    answer = response.json()['choices'][0]['message']['content']
                except (KeyError, IndexError, TypeError, ValueError) as exc:
                    raise AIProviderError('Hosted AI returned an invalid response. Please try again.') from exc
                if not isinstance(answer, str):
                    raise AIProviderError('Hosted AI returned an invalid response. Please try again.')
                if not answer.strip():
                    raise AIProviderError('Hosted AI returned an empty response.')
                return answer.strip()
        except AIProviderError:
            raise
        except httpx.TimeoutException as exc:
            raise AIProviderError('Hosted AI timed out. Please try again.') from exc
        except httpx.HTTPError as exc:
            raise AIProviderError('Hosted AI is temporarily unavailable. Please try again.') from exc

class OllamaProvider:
    """Provider interface placeholder. Local Ollama is intentionally not initialized."""
    async def generate(self, system_prompt: str, context: dict, history: list[dict], message: str) -> str:
        raise AIProviderError('Ollama provider is an interface stub and is not configured.')
