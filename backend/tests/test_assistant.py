import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.conversation import Conversation, Message
from app.models.planning import TaxCalculationRecord
from app.models.user import User
from app.services.assistant.context import AssistantContextBuilder
from app.core.config import Settings
from app.services.assistant.providers import AIProviderError, HostedLLMProvider
from app.services.assistant.service import get_ai_service
import httpx
import pytest

PAYLOAD = {'assessment_year': '2025-26', 'annual_income': 1200000, 'standard_deduction': 75000, 'deductions_80c': 0, 'deductions_80d': 0, 'home_loan_interest': 0, 'hra_exemption': 0}


def register(client, name):
    email = f'{uuid4().hex}@example.com'
    response = client.post('/api/v1/auth/register', json={'name': name, 'email': email, 'password': 'test-password'})
    assert response.status_code == 201
    return response.json()['access_token'], email


def cleanup(emails):
    with SessionLocal() as db:
        for email in emails:
            user = db.query(User).filter(User.email == email).first()
            if user:
                db.delete(user)
        db.commit()


def test_assistant_requires_auth_and_persists_structured_chat():
    with TestClient(app) as client:
        token, email = register(client, 'Assistant user')
        unauthenticated = client.post('/api/v1/assistant/chat', json={'message': 'Explain my tax'})
        assert unauthenticated.status_code == 401
        with patch('app.api.routers.assistant.get_ai_service') as factory:
            service = factory.return_value
            service.respond = AsyncMock(return_value=('Your saved comparison recommends the new regime.', []))
            response = client.post('/api/v1/assistant/chat', headers={'Authorization': f'Bearer {token}'}, json={'message': 'Which regime is better?'})
        assert response.status_code == 200
        body = response.json()
        assert set(body) == {'answer', 'conversation_id', 'sources'}
        assert body['answer'].startswith('Your saved comparison')
        messages = client.get(f"/api/v1/assistant/conversations/{body['conversation_id']}/messages", headers={'Authorization': f'Bearer {token}'})
        assert [item['role'] for item in messages.json()] == ['user', 'assistant']
    cleanup([email])


def test_conversation_creation_and_cross_user_isolation():
    with TestClient(app) as client:
        first_token, first_email = register(client, 'First assistant')
        second_token, second_email = register(client, 'Second assistant')
        first_headers = {'Authorization': f'Bearer {first_token}'}
        second_headers = {'Authorization': f'Bearer {second_token}'}
        conversation = client.post('/api/v1/assistant/conversations', headers=first_headers)
        conversation_id = conversation.json()['id']
        assert conversation.status_code == 201
        assert len(client.get('/api/v1/assistant/conversations', headers=first_headers).json()) == 1
        assert client.get('/api/v1/assistant/conversations', headers=second_headers).json() == []
        foreign = client.get(f'/api/v1/assistant/conversations/{conversation_id}/messages', headers=second_headers)
        assert foreign.status_code == 404
        with patch('app.api.routers.assistant.get_ai_service') as factory:
            factory.return_value.respond = AsyncMock(return_value=('Mock response', []))
            foreign_chat = client.post('/api/v1/assistant/chat', headers=second_headers, json={'message': 'Hello', 'conversation_id': conversation_id})
        assert foreign_chat.status_code == 404
    cleanup([first_email, second_email])


def test_chat_provider_failure_returns_service_unavailable_and_keeps_user_message():
    with TestClient(app) as client:
        token, email = register(client, 'Failure user')
        with patch('app.api.routers.assistant.get_ai_service') as factory:
            factory.return_value.respond = AsyncMock(side_effect=__import__('app.services.assistant', fromlist=['AIProviderError']).AIProviderError('provider unavailable'))
            response = client.post('/api/v1/assistant/chat', headers={'Authorization': f'Bearer {token}'}, json={'message': 'Help'})
        assert response.status_code == 503
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
            assert db.query(Conversation).filter(Conversation.user_id == user.id).count() == 1
            assert db.query(Message).join(Conversation).filter(Conversation.user_id == user.id, Message.role == 'user').count() == 1
    cleanup([email])


def test_context_builder_uses_only_authenticated_users_saved_tax():
    with TestClient(app) as client:
        first_token, first_email = register(client, 'Context owner')
        second_token, second_email = register(client, 'Context other')
        first_headers = {'Authorization': f'Bearer {first_token}'}
        client.post('/api/v1/tax/compare', headers=first_headers, json=PAYLOAD)
        with SessionLocal() as db:
            owner = db.query(User).filter(User.email == first_email).first()
            other = db.query(User).filter(User.email == second_email).first()
            owner_context, _ = AssistantContextBuilder().build(db, owner, 'tax')
            other_context, _ = AssistantContextBuilder().build(db, other, 'tax')
            assert owner_context['tax_engine_result']['old_regime_tax'] is not None
            assert other_context['tax_engine_result'] is None
    cleanup([first_email, second_email])


def test_context_includes_saved_recommendations_and_document_review_state(monkeypatch):
    with TestClient(app) as client:
        token, email = register(client, 'Context owner')
        headers = {'Authorization': f'Bearer {token}'}
        client.post('/api/v1/tax/compare', headers=headers, json=PAYLOAD)
        recommendation = client.post('/api/v1/recommendations/', headers=headers, json={**PAYLOAD, 'regime': 'old'})
        assert recommendation.status_code == 200
        monkeypatch.setattr('app.api.routers.documents.storage.save', lambda content, filename, content_type: f'documents/{uuid4().hex}.png')
        monkeypatch.setattr('app.api.routers.documents.extract_fields', lambda path: {'document_type': 'financial_document', 'fields': {}, 'raw_text': '', 'missing_fields': ['annual_income'], 'validation_errors': [], 'requires_user_verification': True})
        upload = client.post('/api/v1/documents/upload', headers=headers, files={'file': ('income.png', b'image-bytes', 'image/png')})
        assert upload.status_code == 201

        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
            context, _ = AssistantContextBuilder().build(db, user, 'Explain my planning')

        assert context['financial_inputs']['annual_income'] == PAYLOAD['annual_income']
        assert context['tax_engine_result']['old_regime'] is not None
        assert context['recommendations']['items'] == recommendation.json()['items']
        assert context['documents'][0]['verification_required'] is True
        assert context['documents'][0]['missing_fields'] == ['annual_income']
    cleanup([email])


def test_chat_uses_the_most_recent_twenty_messages_in_order():
    with TestClient(app) as client:
        token, email = register(client, 'History owner')
        headers = {'Authorization': f'Bearer {token}'}
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
            conversation = Conversation(user_id=user.id)
            db.add(conversation)
            db.flush()
            start = datetime(2026, 1, 1)
            for index in range(25):
                db.add(Message(conversation_id=conversation.id, role='user', content=f'message-{index}', created_at=start + timedelta(seconds=index)))
            conversation_id = conversation.id
            db.commit()

        with patch('app.api.routers.assistant.get_ai_service') as factory:
            service = factory.return_value
            service.respond = AsyncMock(return_value=('Saved context response', []))
            response = client.post('/api/v1/assistant/chat', headers=headers, json={'message': 'latest question', 'conversation_id': conversation_id})

        assert response.status_code == 200
        history = service.respond.await_args.args[3]
        assert [item['content'] for item in history] == [f'message-{index}' for index in range(5, 25)]
    cleanup([email])


def test_hosted_provider_without_api_key_fails_without_network_request():
    provider = HostedLLMProvider(Settings(llm_api_key=None))
    response = provider.generate('system', {}, [], 'Explain my tax')
    with pytest.raises(AIProviderError, match='LLM_API_KEY'):
        asyncio.run(response)


def test_gemini_provider_defaults_and_service_selection():
    settings = Settings(_env_file=None, gemini_api_key='test-only-key')
    assert settings.llm_provider == 'gemini'
    assert settings.llm_model == 'gemini-3.8-flash'
    assert settings.llm_base_url == 'https://generativelanguage.googleapis.com/v1beta/openai/'
    with patch('app.services.assistant.service.get_settings', return_value=settings):
        service = get_ai_service()
    assert isinstance(service.provider, HostedLLMProvider)


@pytest.mark.parametrize(
    ('provider_name', 'expected_key', 'expected_model', 'expected_base_url'),
    [
        ('gemini', 'gemini-test-key', 'gemini-test-model', 'https://gemini.test/v1'),
        ('groq', 'groq-test-key', 'groq-test-model', 'https://groq.test/v1'),
    ],
)
def test_hosted_provider_selection_uses_provider_specific_settings(
    provider_name, expected_key, expected_model, expected_base_url
):
    settings = Settings(
        _env_file=None,
        llm_provider=provider_name,
        gemini_api_key='gemini-test-key',
        gemini_model='gemini-test-model',
        gemini_base_url='https://gemini.test/v1',
        groq_api_key='groq-test-key',
        groq_model='groq-test-model',
        groq_base_url='https://groq.test/v1',
    )
    with patch('app.services.assistant.service.get_settings', return_value=settings):
        service = get_ai_service()
    assert isinstance(service.provider, HostedLLMProvider)
    assert service.provider.settings.llm_api_key == expected_key
    assert service.provider.settings.llm_model == expected_model
    assert service.provider.settings.llm_base_url == expected_base_url


def test_hosted_provider_selection_preserves_generic_hosted_settings():
    settings = Settings(
        _env_file=None,
        llm_provider='hosted',
        llm_api_key='generic-test-key',
        llm_model='generic-test-model',
        llm_base_url='https://hosted.test/v1',
    )
    with patch('app.services.assistant.service.get_settings', return_value=settings):
        service = get_ai_service()
    assert isinstance(service.provider, HostedLLMProvider)
    assert service.provider.settings is settings
    assert service.provider.settings.llm_api_key == 'generic-test-key'


@pytest.mark.parametrize(
    ('api_key', 'model', 'error'),
    [
        (None, 'groq-test-model', 'GROQ_API_KEY'),
        ('groq-test-key', '', 'GROQ_MODEL'),
        ('groq-test-key', 'replace-with-an-active-groq-model-id', 'GROQ_MODEL'),
    ],
)
def test_groq_provider_requires_configuration(api_key, model, error):
    settings = Settings(_env_file=None, llm_provider='groq', groq_api_key=api_key, groq_model=model)
    with patch('app.services.assistant.service.get_settings', return_value=settings):
        with pytest.raises(AIProviderError, match=error):
            get_ai_service()


def test_hosted_provider_sends_gemini_openai_compatible_request():
    settings = Settings(
        _env_file=None,
        llm_provider='gemini',
        llm_api_key='test-only-key',
        llm_model='gemini-3.8-flash',
        llm_base_url='https://generativelanguage.googleapis.com/v1beta/openai/',
    )
    response = MagicMock()
    response.json.return_value = {'choices': [{'message': {'content': 'The saved result favors the new regime.'}}]}
    client = MagicMock()
    client.post = AsyncMock(return_value=response)
    async_client = MagicMock()
    async_client.__aenter__ = AsyncMock(return_value=client)
    async_client.__aexit__ = AsyncMock(return_value=False)
    context = {'tax_engine_result': {'old_regime_tax': 123, 'new_regime_tax': 100}}

    with patch('app.services.assistant.providers.httpx.AsyncClient', return_value=async_client):
        answer = asyncio.run(HostedLLMProvider(settings).generate('system instructions', context, [], 'Which regime?'))

    assert answer == 'The saved result favors the new regime.'
    args, kwargs = client.post.await_args
    assert args[0] == 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'
    assert kwargs['headers']['Authorization'] == 'Bearer test-only-key'
    assert kwargs['json']['model'] == 'gemini-3.8-flash'
    context_message = kwargs['json']['messages'][1]['content']
    assert '123' in context_message
    assert '100' in context_message
    assert kwargs['json']['messages'][0]['content'] == 'system instructions'


def test_gemini_http_failure_is_reported_without_leaking_provider_details():
    settings = Settings(_env_file=None, llm_api_key='test-only-key')
    client = MagicMock()
    client.post = AsyncMock(side_effect=httpx.ConnectError('private transport detail'))
    async_client = MagicMock()
    async_client.__aenter__ = AsyncMock(return_value=client)
    async_client.__aexit__ = AsyncMock(return_value=False)
    with patch('app.services.assistant.providers.httpx.AsyncClient', return_value=async_client):
        response = HostedLLMProvider(settings).generate('system', {}, [], 'Question')
        with pytest.raises(AIProviderError, match='temporarily unavailable') as error:
            asyncio.run(response)
    assert 'private transport detail' not in str(error.value)


@pytest.mark.parametrize(
    ('status_code', 'message'),
    [
        (401, 'credentials were rejected'),
        (403, 'credentials were rejected'),
        (429, 'rate limit or quota'),
        (503, 'temporarily unavailable'),
    ],
)
def test_gemini_provider_maps_http_failures_to_safe_messages(status_code, message):
    settings = Settings(_env_file=None, llm_api_key='test-only-key')
    request = httpx.Request('POST', 'https://example.test/chat/completions')
    response = httpx.Response(status_code, json={'error': 'private provider detail'}, request=request)
    client = MagicMock()
    client.post = AsyncMock(return_value=response)
    async_client = MagicMock()
    async_client.__aenter__ = AsyncMock(return_value=client)
    async_client.__aexit__ = AsyncMock(return_value=False)

    with patch('app.services.assistant.providers.httpx.AsyncClient', return_value=async_client):
        with pytest.raises(AIProviderError, match=message) as error:
            asyncio.run(HostedLLMProvider(settings).generate('system', {}, [], 'Question'))

    assert 'private provider detail' not in str(error.value)


def test_gemini_provider_timeout_is_user_friendly_and_does_not_leak_details():
    settings = Settings(_env_file=None, llm_api_key='test-only-key')
    client = MagicMock()
    client.post = AsyncMock(side_effect=httpx.ReadTimeout('private timeout detail'))
    async_client = MagicMock()
    async_client.__aenter__ = AsyncMock(return_value=client)
    async_client.__aexit__ = AsyncMock(return_value=False)

    with patch('app.services.assistant.providers.httpx.AsyncClient', return_value=async_client):
        with pytest.raises(AIProviderError, match='timed out') as error:
            asyncio.run(HostedLLMProvider(settings).generate('system', {}, [], 'Question'))

    assert 'private timeout detail' not in str(error.value)


@pytest.mark.parametrize('payload', [{}, {'choices': []}, {'choices': [{'message': {'content': ['not', 'text']}}]}])
def test_gemini_provider_rejects_malformed_responses(payload):
    settings = Settings(_env_file=None, llm_api_key='test-only-key')
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload
    client = MagicMock()
    client.post = AsyncMock(return_value=response)
    async_client = MagicMock()
    async_client.__aenter__ = AsyncMock(return_value=client)
    async_client.__aexit__ = AsyncMock(return_value=False)

    with patch('app.services.assistant.providers.httpx.AsyncClient', return_value=async_client):
        with pytest.raises(AIProviderError, match='invalid response'):
            asyncio.run(HostedLLMProvider(settings).generate('system', {}, [], 'Question'))
