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
    elif settings.llm_provider.lower() in {'gemini', 'groq'}:
        provider_name = settings.llm_provider.lower()
        api_key = getattr(settings, f'{provider_name}_api_key')
        model = getattr(settings, f'{provider_name}_model')
        base_url = getattr(settings, f'{provider_name}_base_url')
        if not api_key:
            raise AIProviderError(
                f'{provider_name.title()} is not configured. Set {provider_name.upper()}_API_KEY.'
            )
        if provider_name == 'groq' and (
            not model.strip() or model.lower().startswith('replace-with-')
        ):
            raise AIProviderError('Groq is not configured. Set GROQ_MODEL to an active Groq model ID.')
        provider_settings = settings.model_copy(update={
            'llm_api_key': api_key,
            'llm_model': model,
            'llm_base_url': base_url,
        })
        provider = HostedLLMProvider(provider_settings)
    elif settings.llm_provider.lower() == 'hosted':
        provider = HostedLLMProvider(settings)
    else:
        raise AIProviderError(f'Unsupported LLM_PROVIDER: {settings.llm_provider}')
    return AIService(provider)
