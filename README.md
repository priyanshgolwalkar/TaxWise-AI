# TaxWise AI

### Intelligent and Explainable Tax Planning Platform

TaxWise AI is a university Project-Based Learning (PBL) project that simplifies income tax planning through deterministic tax calculations, document processing, explainable recommendations and an AI-powered tax assistant.

Built using a modular monolith architecture, the application combines a React frontend with a FastAPI backend, database persistence, OCR-based financial document extraction and hosted LLM integration.

## Key Features

- **User Authentication:** JWT-based registration, login and user-specific data access.
- **Financial Document Processing:** Upload PDF and image documents with OCR-based financial data extraction using OpenCV and Tesseract.
- **Tax Calculation Engine:** Deterministic comparison of the Old and New Tax Regimes using configured tax rules.
- **Explainable Recommendations:** Rule-based tax-saving recommendations based on available financial information.
- **AI Tax Assistant:** Conversational tax assistance using hosted LLM providers, with saved tax calculations and recommendations as context.
- **Conversation History:** Persistent, user-specific assistant conversations.
- **Tax Records and Reports:** Store and access calculations, documents, recommendations and reports.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Router |
| Backend | Python, FastAPI |
| Database | SQLite for local development, MySQL-compatible database support |
| ORM | SQLAlchemy |
| Authentication | JWT |
| Document Processing | OpenCV, Tesseract, pdf2image |
| AI Integration | Groq, Gemini |
| API Architecture | REST APIs |
| Testing | Pytest, TypeScript validation |
| Version Control | Git, GitHub |

## Project Structure

```text
TaxWise-AI/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── lib/
│   ├── package.json
│   └── .env.example
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   │       ├── tax_engine/
│   │       ├── document_processing/
│   │       ├── recommendations/
│   │       └── assistant/
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── .env.example
└── README.md
```

## System Architecture

TaxWise AI follows a modular monolith architecture. The frontend communicates with the FastAPI backend through REST APIs. The backend manages authentication, tax calculations, document processing, recommendations, database operations and AI assistant requests.

The tax calculation engine remains deterministic. The AI assistant explains saved calculation results and recommendations rather than independently calculating tax liabilities.

## Local Development Setup

### Prerequisites

- Python 3.10+
- Node.js and npm
- Git
- Tesseract OCR
- Poppler for PDF rendering

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd TaxWise-AI
```

### 2. Backend Setup

```bash
cd backend

python -m venv venv
```

Activate the virtual environment.

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` file using `backend/.env.example` as a reference.

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend URL:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
```

Create the frontend `.env` file using `frontend/.env.example` as a reference.

Configure the backend API URL:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

Start the frontend:

```bash
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

## Environment Configuration

Configure the environment variables in the backend `.env` file.

| Variable | Description |
|---|---|
| `ENVIRONMENT` | Application environment |
| `DATABASE_URL` | Database connection URL |
| `JWT_SECRET` | Secret used for JWT signing |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |
| `LLM_PROVIDER` | Selected AI provider: `groq`, `gemini` or `hosted` |
| `GROQ_API_KEY` | Groq API key |
| `GROQ_MODEL` | Groq model identifier |
| `GROQ_BASE_URL` | Groq API endpoint |
| `GEMINI_API_KEY` | Gemini API key |
| `GEMINI_MODEL` | Gemini model identifier |
| `GEMINI_BASE_URL` | Gemini API endpoint |
| `TIDB_CA_PATH` | TiDB CA certificate path when using TiDB Cloud |

Provider-specific configuration is maintained separately. Only the selected provider is used for assistant requests.

### Database Configuration

The application defaults to SQLite for local development and testing.

For MySQL-compatible databases, configure `DATABASE_URL` using the SQLAlchemy PyMySQL connection format.

For TiDB Cloud:

- Use a `mysql+pymysql://` connection URL.
- Configure `TIDB_CA_PATH` with the downloaded TiDB CA certificate path.
- TLS certificate-chain and hostname verification are enabled.
- MySQL connections fail with a configuration error if the required CA certificate is missing or invalid.
- SQLite configuration and behavior remain unchanged.

### Security

- Never commit `.env` files or database credentials.
- Keep API keys exclusively on the backend.
- Use a strong, stable `JWT_SECRET` in production.
- Configure CORS for trusted frontend origins.
- Never disable TLS certificate verification for hosted database connections.

## API Endpoints

### Authentication and Tax Management

The backend exposes REST APIs for authentication, document management, tax calculations, recommendations and reports.

Important endpoints include:

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/documents/upload` | Upload a financial document |
| GET | `/api/v1/documents` | Retrieve authenticated user's documents |
| POST | `/api/v1/tax/compare` | Compare Old and New Tax Regimes |
| POST | `/api/v1/assistant/chat` | Send a message to the AI assistant |
| POST | `/api/v1/assistant/conversations` | Create an assistant conversation |
| GET | `/api/v1/assistant/conversations` | Retrieve conversation history |
| GET | `/api/v1/assistant/conversations/{conversation_id}/messages` | Retrieve conversation messages |

Protected endpoints require a valid JWT bearer token.

Document uploads support PDF, PNG and JPEG files up to 10 MB.

## AI Assistant

TaxWise AI supports hosted LLM integration through Groq and Gemini.

Configure the selected provider using:

```env
LLM_PROVIDER=groq
```

**Groq Configuration**

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_available_model_id
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

**Gemini Configuration**

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_gemini_model_id
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

The assistant uses the user's saved deterministic tax results, recommendations and document verification status as context.

The language model is instructed to explain existing tax results rather than independently calculate tax liabilities.

Conversation history is persisted per user.

## Document Processing and OCR

The document processing module uses:

- OpenCV for image preprocessing.
- Tesseract OCR for text extraction.
- pdf2image for PDF-to-image conversion.

**System dependencies:**

Tesseract and Poppler must be installed separately. They are not installed automatically through Python requirements.

Ensure both executables are available on your system `PATH` before testing OCR functionality.

Extracted financial information should be reviewed before using it for tax calculations.

## Testing

### Backend Tests

Run from the repository root:

```bash
python -m pytest backend/tests
```

### Frontend TypeScript Validation

```bash
cd frontend
npx tsc --noEmit
```

### Frontend Production Build

```bash
npm run build
```

## Current Scope and Limitations

- Tax calculations depend on the rules configured in the application.
- The currently configured tax rules cover Assessment Year 2025–26.
- OCR extraction may require manual verification.
- AI responses depend on the availability and configuration of the selected hosted provider.
- Ollama and knowledge retrieval components are not currently initialized as active application features.
- TiDB Cloud connectivity requires valid credentials, network access and TLS configuration.

## Future Enhancements

- Extend tax rule coverage to additional assessment years.
- Improve OCR accuracy and document verification.
- Expand financial document support.
- Enhance personalized tax-saving recommendations.
- Introduce retrieval-based knowledge assistance.
- Complete hosted cloud deployment and production database integration.

## Disclaimer

TaxWise AI is an academic prototype developed for educational and demonstration purposes.

It does not provide legally binding tax advice, guarantee tax savings or submit income tax returns. Always verify tax calculations against applicable government regulations or consult a qualified tax professional.

---

**Developed as a Semester 7 Project-Based Learning project at MIT ADT University.**
