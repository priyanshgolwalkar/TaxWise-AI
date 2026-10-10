from fastapi import APIRouter
from app.api.routers import auth, profile, documents, tax, recommendations, assistant, reports, dashboard
api_router = APIRouter()
for router in (auth.router, profile.router, documents.router, tax.router, recommendations.router, assistant.router, reports.router, dashboard.router):
    api_router.include_router(router)
