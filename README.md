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

1. Copy `.env.example` to `.env`, replace every `replace-with-*` value with a unique secret, and keep `.env` local. Set `DATABASE_URL` to use the same password as `MYSQL_PASSWORD`. Set `ENVIRONMENT=production`, a strong stable `JWT_SECRET`, and `CORS_ORIGINS` to a comma-separated list containing the deployed frontend origin for production. Local development defaults to `http://localhost:5173`; production startup fails if `JWT_SECRET` is missing or still a placeholder.
2. Backend: `cd backend`, create a virtual environment, install `pip install -r requirements.txt`, then run `uvicorn app.main:app --reload`.
3. Frontend: `cd frontend`, run `npm install`, then `npm run dev`.
4. Open `http://localhost:5173`. API documentation is at `http://localhost:8000/docs`.
5. Run backend tests with `pytest backend/tests` from the repository root.

`DATABASE_URL` defaults to SQLite for quick tests and can be set to the MySQL URL from `.env` for the full stack. Docker Compose requires the database and MinIO credentials in `.env`; no default credentials are committed. Vercel can deploy `frontend/`; Render can deploy `backend/` with the Dockerfile. Before production, connect persistence-backed user authentication, MinIO uploads, Ollama/RAG retrieval, and replace the example tax rules with the project team's approved source of truth.

For TiDB Cloud, set `DATABASE_URL` to a `mysql+pymysql://...` connection URL and `TIDB_CA_PATH` to the downloaded TiDB CA certificate file. MySQL/PyMySQL connections require that CA file and always enable certificate-chain and hostname verification; startup fails with a configuration error if the CA path is missing or invalid. SQLite configuration and behavior are unchanged.

The document endpoints require a bearer token: `POST /api/v1/documents/upload` accepts PDF/PNG/JPEG files up to 10 MB, and `GET /api/v1/documents` returns only the authenticated user's documents. Tax comparison is available at `POST /api/v1/tax/compare` and requires the same token.

The authenticated assistant endpoint is `POST /api/v1/assistant/chat`. Select one hosted provider at a time with `LLM_PROVIDER=gemini` or `LLM_PROVIDER=groq`; provider settings are separate so both credentials can remain configured in the backend `.env`. Gemini uses `GEMINI_API_KEY`, `GEMINI_MODEL` (default `gemini-3.8-flash`), and `GEMINI_BASE_URL` (default `https://generativelanguage.googleapis.com/v1beta/openai/`). Groq uses `GROQ_API_KEY`, `GROQ_MODEL` (set this to a currently available model ID), and `GROQ_BASE_URL` (default `https://api.groq.com/openai/v1`). `LLM_PROVIDER=hosted` continues to use the generic `LLM_API_KEY`, `LLM_MODEL`, and `LLM_BASE_URL` settings. Example placeholders are in `backend/.env.example`. Keep keys backend-only. Without the selected provider's key, the API returns a configuration error and makes no external request. Assistant context contains the user's saved deterministic tax results and document verification status; the LLM is instructed to explain those values, never calculate them. Conversation history is stored per user. Ollama and knowledge retrieval are interfaces only and are not initialized.

OCR requires Tesseract for text extraction and Poppler for PDF rendering. These system tools are not installed by the Python requirements; install them locally and ensure their executables are available on `PATH` before testing OCR.
