import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.db import session as db_session


def test_cors_origins_are_split_trimmed_and_empty_entries_removed():
    settings = Settings(
        _env_file=None,
        cors_origins=' http://localhost:5173, https://taxwise.vercel.app/, ,',
    )

    assert settings.cors_origin_list == [
        'http://localhost:5173',
        'https://taxwise.vercel.app',
    ]


def test_cors_origins_are_loaded_from_environment(monkeypatch):
    monkeypatch.setenv(
        'CORS_ORIGINS',
        'http://localhost:5173,https://taxwise.vercel.app',
    )

    settings = Settings(_env_file=None)

    assert settings.cors_origin_list == [
        'http://localhost:5173',
        'https://taxwise.vercel.app',
    ]


def test_cors_origins_default_preserves_local_development_origin():
    settings = Settings(_env_file=None)

    assert settings.cors_origin_list == ['http://localhost:5173']


def test_production_requires_jwt_secret():
    with pytest.raises(ValidationError, match='JWT_SECRET must be set'):
        Settings(_env_file=None, environment='production')


def test_production_requires_jwt_secret_environment_variable(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'production')
    monkeypatch.delenv('JWT_SECRET', raising=False)

    with pytest.raises(ValidationError, match='JWT_SECRET must be set'):
        Settings(_env_file=None)


def test_production_rejects_jwt_secret_placeholder():
    with pytest.raises(ValidationError, match='JWT_SECRET must be set'):
        Settings(
            _env_file=None,
            environment='production',
            jwt_secret='replace-with-a-long-random-secret',
        )


def test_production_accepts_configured_jwt_secret():
    settings = Settings(
        _env_file=None,
        environment='production',
        jwt_secret='configured-production-test-secret',
    )

    assert settings.jwt_secret == 'configured-production-test-secret'


def test_production_loads_jwt_secret_from_environment(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'production')
    monkeypatch.setenv('JWT_SECRET', 'configured-production-test-secret')

    settings = Settings(_env_file=None)

    assert settings.jwt_secret == 'configured-production-test-secret'


def test_development_generates_ephemeral_jwt_secret_when_missing():
    settings = Settings(_env_file=None)

    assert settings.jwt_secret
    assert len(settings.jwt_secret) >= 32


def test_tidb_ca_path_is_loaded_from_environment(monkeypatch, tmp_path):
    ca_path = tmp_path / 'tidb-ca.pem'
    monkeypatch.setenv('TIDB_CA_PATH', str(ca_path))

    settings = Settings(_env_file=None)

    assert settings.tidb_ca_path == str(ca_path)


def test_sqlite_engine_preserves_local_connection_configuration(monkeypatch):
    captured = {}
    sentinel = object()

    def create_engine(url, connect_args):
        captured['url'] = url
        captured['connect_args'] = connect_args
        return sentinel

    monkeypatch.setattr(db_session, 'create_engine', create_engine)

    engine = db_session._create_engine('sqlite:///./test.db', None)

    assert engine is sentinel
    assert captured['connect_args'] == {'check_same_thread': False}


def test_mysql_pymysql_engine_uses_verified_ca_tls(monkeypatch, tmp_path):
    ca_file = tmp_path / 'tidb-ca.pem'
    ca_file.write_text('test CA placeholder')
    captured = {}
    sentinel = object()

    def create_default_context(*, cafile):
        captured['validated_ca'] = cafile
        return object()

    def create_engine(url, connect_args):
        captured['url'] = url
        captured['connect_args'] = connect_args
        return sentinel

    monkeypatch.setattr(db_session.ssl, 'create_default_context', create_default_context)
    monkeypatch.setattr(db_session, 'create_engine', create_engine)

    engine = db_session._create_engine(
        'mysql+pymysql://user:password@db.example:4000/taxwise',
        str(ca_file),
    )

    tls = captured['connect_args']['ssl']
    assert engine is sentinel
    assert captured['url'].startswith('mysql+pymysql://')
    assert captured['validated_ca'] == str(ca_file.resolve())
    assert tls['ca'] == str(ca_file.resolve())
    assert tls['check_hostname'] is True
    assert tls['verify_mode'] == db_session.ssl.CERT_REQUIRED


@pytest.mark.parametrize(
    ('ca_path', 'expected_message'),
    [
        (None, 'TIDB_CA_PATH is required'),
        ('missing-tidb-ca.pem', 'TIDB_CA_PATH must point'),
    ],
)
def test_mysql_pymysql_requires_valid_ca_path(ca_path, expected_message):
    with pytest.raises(RuntimeError, match=expected_message):
        db_session._create_engine(
            'mysql+pymysql://user:password@db.example:4000/taxwise',
            ca_path,
        )


def test_mysql_pymysql_rejects_invalid_ca_certificate(monkeypatch, tmp_path):
    ca_file = tmp_path / 'invalid-ca.pem'
    ca_file.write_text('not a certificate')

    def reject_ca(*, cafile):
        raise db_session.ssl.SSLError('invalid certificate data')

    monkeypatch.setattr(db_session.ssl, 'create_default_context', reject_ca)

    with pytest.raises(RuntimeError, match='TIDB_CA_PATH must point'):
        db_session._create_engine(
            'mysql+pymysql://user:password@db.example:4000/taxwise',
            str(ca_file),
        )
