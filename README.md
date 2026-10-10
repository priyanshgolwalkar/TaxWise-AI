# TaxWise AI

TaxWise AI is a university PBL project for intelligent, explainable tax planning. It is a modular monolith: React + Vite frontend, FastAPI backend, MySQL persistence, OCR/document processing, deterministic tax calculation, rules-based recommendations, Ollama assistant, FAISS-ready RAG, and MinIO storage.

## Structure

- `frontend/` React, Vite, Tailwind CSS, React Router dashboard
- `backend/app/api/` thin REST routers and Swagger at `/docs`
- `backend/app/services/tax_engine/` versioned rules and deterministic calculator
- `backend/app/services/document_processing/` OpenCV + Tesseract pipeline with review flags
- `backend/app/services/recommendations/` explainable rules engine
- `backend/app/models/` SQLAlchemy models for users, documents, extracted data, calculations, recommendations, and reports
- `docker-compose.yml` local frontend, backend, MySQL, MinIO, and Ollama

## Local development

1. Copy `.env.example` to `.env`, replace every `replace-with-*` value with a unique secret, and keep `.env` local. Set `DATABASE_URL` to use the same password as `MYSQL_PASSWORD`. Without `JWT_SECRET`, the backend generates an ephemeral development key; configure a stable secret for deployments so tokens remain valid across restarts.
2. Backend: `cd backend`, create a virtual environment, install `pip install -r requirements.txt`, then run `uvicorn app.main:app --reload`.
3. Frontend: `cd frontend`, run `npm install`, then `npm run dev`.
4. Open `http://localhost:5173`. API documentation is at `http://localhost:8000/docs`.
5. Run backend tests with `pytest backend/tests` from the repository root.

`DATABASE_URL` defaults to SQLite for quick tests and can be set to the MySQL URL from `.env` for the full stack. Docker Compose requires the database and MinIO credentials in `.env`; no default credentials are committed. Vercel can deploy `frontend/`; Render can deploy `backend/` with the Dockerfile. Before production, connect persistence-backed user authentication, MinIO uploads, Ollama/RAG retrieval, and replace the example tax rules with the project team's approved source of truth.

The document endpoints require a bearer token: `POST /api/v1/documents/upload` accepts PDF/PNG/JPEG files up to 10 MB, and `GET /api/v1/documents` returns only the authenticated user's documents. Tax comparison is available at `POST /api/v1/tax/compare` and requires the same token.

The authenticated assistant endpoint is `POST /api/v1/assistant/chat`. Gemini uses Google's OpenAI-compatible API through the existing hosted provider abstraction. Set `LLM_PROVIDER=gemini`, `LLM_API_KEY`, `LLM_MODEL=gemini-3.8-flash`, and `LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/` in the backend `.env`. Keep the API key backend-only. Without a key, the API returns a configuration error and makes no external request. Assistant context contains the user's saved deterministic tax results and document verification status; the LLM is instructed to explain those values, never calculate them. Conversation history is stored per user. Ollama and knowledge retrieval are interfaces only and are not initialized.

The backend image installs `poppler-utils` for PDF OCR. With Docker Desktop running, use `docker compose up --build` to verify MySQL, MinIO, Ollama, backend, and frontend connectivity. The MinIO data volume is named `minio_data`; stop and restart the stack without `docker compose down -v` to verify uploaded objects persist.
