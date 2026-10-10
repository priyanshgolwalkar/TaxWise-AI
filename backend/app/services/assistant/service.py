from app.core.config import Settings, get_settings
from .context import AssistantContextBuilder
from .providers import AIProviderError, HostedLLMProvider, OllamaProvider
from .prompt import SYSTEM_PROMPT

class AIService:
    def __init__(self, provider, context_builder: AssistantContextBuilder | None = None):
        self.provider = provider
        self.context_builder = context_builder or AssistantContextBuilder()

    async def respond(self, db, user, message: str, history: list[dict]) -> tuple[str, list[dict]]:
        context, sources = self.context_builder.build(db, user, message)
        answer = await self.provider.generate(SYSTEM_PROMPT, context, history, message)
        return answer, sources

def get_ai_service() -> AIService:
    settings: Settings = get_settings()
    if settings.llm_provider.lower() == 'ollama':
        provider = OllamaProvider()
    elif settings.llm_provider.lower() in {'gemini', 'hosted'}:
        provider = HostedLLMProvider(settings)
    else:
        raise AIProviderError(f'Unsupported LLM_PROVIDER: {settings.llm_provider}')
    return AIService(provider)
