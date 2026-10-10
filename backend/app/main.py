from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.db.session import Base, engine
from app.models import User

app = FastAPI(title='TaxWise AI API', version='0.1.0', description='Intelligent tax planning and recommendation platform')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(api_router, prefix='/api/v1')

@app.on_event('startup')
def create_tables():
    Base.metadata.create_all(bind=engine)

@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'taxwise-api'}
