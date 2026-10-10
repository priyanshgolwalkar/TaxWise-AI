import asyncio
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


def test_hosted_provider_without_api_key_fails_without_network_request():
    provider = HostedLLMProvider(Settings(llm_api_key=None))
    response = provider.generate('system', {}, [], 'Explain my tax')
    with pytest.raises(AIProviderError, match='LLM_API_KEY'):
        asyncio.run(response)


def test_gemini_provider_defaults_and_service_selection():
    settings = Settings(_env_file=None)
    assert settings.llm_provider == 'gemini'
    assert settings.llm_model == 'gemini-3.8-flash'
    assert settings.llm_base_url == 'https://generativelanguage.googleapis.com/v1beta/openai/'
    with patch('app.services.assistant.service.get_settings', return_value=settings):
        service = get_ai_service()
    assert isinstance(service.provider, HostedLLMProvider)


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
