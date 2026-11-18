import ssl
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import get_settings

settings = get_settings()

def _create_engine(database_url: str, tidb_ca_path: str | None):
    driver = make_url(database_url).drivername
    if driver.startswith('sqlite'):
        connect_args = {'check_same_thread': False}
    elif driver == 'mysql+pymysql':
        if not tidb_ca_path:
            raise RuntimeError(
                'TIDB_CA_PATH is required for MySQL/PyMySQL connections; '
                'TLS certificate and hostname verification cannot be disabled.'
            )
        try:
            ca_path = Path(tidb_ca_path).expanduser().resolve(strict=True)
            if not ca_path.is_file():
                raise OSError('CA path is not a file')
            ssl.create_default_context(cafile=str(ca_path))
        except (OSError, ssl.SSLError, ValueError) as exc:
            raise RuntimeError(
                'TIDB_CA_PATH must point to a readable, valid CA certificate file.'
            ) from exc
        connect_args = {
            'ssl': {
                'ca': str(ca_path),
                'check_hostname': True,
                'verify_mode': ssl.CERT_REQUIRED,
            }
        }
    else:
        connect_args = {}
    return create_engine(database_url, connect_args=connect_args)


engine = _create_engine(settings.database_url, settings.tidb_ca_path)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
