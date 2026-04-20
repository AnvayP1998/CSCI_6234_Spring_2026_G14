# DataInsight AI

**Multimodal AI-Powered Document Intelligence Platform**

Upload any document, image, audio, or video file — extract text, search semantically, and chat with an AI assistant that reads your content and cites its sources.

---

## What It Does

- **Upload** PDF, image (JPG/PNG), audio (MP3/WAV), or video (MP4) files — from your computer or by pasting a URL
- **Extract** text automatically: OCR for images, Whisper transcription for audio/video, PyMuPDF for PDFs
- **Embed & Index** — chunks the text and stores vector embeddings in Qdrant for semantic search
- **Chat with AI** — ask questions, get summaries, classify documents; answers stream token by token in real time
- **Source citations** — every AI answer links back to the exact chunks it used
- **Chat history** — follow-up questions work ("explain that last point")
- **Semantic search** — find the most relevant sections of any document

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python), Uvicorn |
| Relational DB | PostgreSQL (via SQLAlchemy) |
| Vector DB | Qdrant Cloud |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` |
| LLM | Anthropic Claude (`claude-haiku-4-5`) |
| OCR | Tesseract + Pillow |
| Audio/Video | faster-whisper + ffmpeg |
| PDF | PyMuPDF |
| Deployment | Railway (backend) + Vercel (frontend) + Docker |

---

## Project Structure

```
OOAD_Group14/
├── Projectsrc/
│   ├── backend/             # FastAPI application
│   │   ├── app/
│   │   │   ├── api/         # Route handlers and request schemas
│   │   │   ├── core/        # Config, database session
│   │   │   ├── domain/      # SQLAlchemy ORM models
│   │   │   └── services/    # Business logic (processing, indexing, analysis)
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── frontend/            # Next.js application
│       ├── app/             # Pages (Next.js App Router)
│       └── lib/             # API client
├── sample_files/            # Sample audio files for testing
└── README.md
```

---

## Running Locally

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional, for containerized backend)
- Tesseract OCR installed: https://github.com/tesseract-ocr/tesseract
- ffmpeg installed: https://ffmpeg.org/download.html

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd OOAD_Group14
```

### 2. Backend Setup

```bash
cd Projectsrc/backend
```

Create a `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/datainsight
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=datainsight_assets
QDRANT_API_KEY=                        # leave empty for local Qdrant
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=                        # optional
STORAGE_DIR=./storage
```

Install dependencies and run:

```bash
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 3. Local Qdrant (vector database)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 4. Frontend Setup

```bash
cd Projectsrc/frontend
```

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Install and run:

```bash
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

---

## Running with Docker (Backend only)

```bash
cd Projectsrc/backend
docker build -t datainsight-backend .
docker run -p 8000:8000 --env-file .env datainsight-backend
```

---

## Live Demo

| Service | URL |
|---------|-----|
| Frontend | Deployed on Vercel |
| Backend API | Deployed on Railway |
| Vector DB | Qdrant Cloud |

---

## Sample Test Files

The `sample_files/` folder contains 3 audio files from The Economist (Jan 2024) for testing the audio transcription and AI analysis features:

| File | Topic |
|------|-------|
| `economist_finance_buttonwood.mp3` | Financial markets analysis |
| `economist_finance_international_commerce.mp3` | International trade & finance |
| `economist_business_technology.mp3` | Business & technology |

Upload any of these through the app, click **Prepare for AI**, then ask questions like:
- *"What is the main argument of this audio?"*
- *"Summarize the key points"*
- *"What economic trends are discussed?"*

---

## Database Schema

Five PostgreSQL tables track the full pipeline:

```
data_assets           — every uploaded file
  └── processing_contexts  — pipeline status (UPLOADED → EXTRACTED → INDEXED)
  └── extracted_texts      — raw extracted text content
  └── task_requests        — every AI query made
        └── task_results         — AI-generated answers with confidence score
              └── evidence_refs        — source chunks that backed each answer
```

---

## OOAD Design Patterns Used

- **Singleton** — `QdrantClient` and embedding model loaded once, reused across all requests
- **Strategy** — `ProcessingService` selects the right extractor (PDF / OCR / Whisper) based on file type
- **Repository** — SQLAlchemy ORM abstracts all database access
- **Service Layer** — Business logic separated into `AnalysisService`, `IndexingService`, `ProcessingService`, `SearchService`, `StorageService`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/assets` | List all uploaded assets |
| POST | `/api/assets/upload` | Upload a file |
| POST | `/api/assets/upload-url` | Upload from a URL |
| POST | `/api/assets/{id}/process` | Extract text |
| POST | `/api/assets/{id}/embed` | Chunk, embed, and index |
| POST | `/api/tasks/analyze-stream` | Stream AI analysis (SSE) |
| POST | `/api/query` | Semantic search |
| DELETE | `/api/assets/{id}` | Delete asset and vectors |
