# Manifold

AI-powered semantic search for legal document discovery. Find relevant evidence across thousands of pages in seconds, not hours.

![Python](https://img.shields.io/badge/Backend-FastAPI-009688)
![TypeScript](https://img.shields.io/badge/Frontend-Next.js_16-black)
![License](https://img.shields.io/badge/License-MIT-blue)

## The Problem

Legal teams spend **60-80% of discovery time** manually reviewing documents. A 10,000-page case file takes weeks to review thoroughly. Keyword search misses relevant evidence when witnesses use different words ("vehicle" vs "car" vs "sedan").

## The Solution

Manifold uses semantic search to understand *meaning*, not just keywords. Search for "weapon" and find mentions of "knife", "firearm", and "Glock 19" — even if "weapon" never appears in the text.

**Key capabilities:**
- **Semantic search** — Finds conceptually related content using sentence embeddings
- **Semantic highlighting** — Automatically highlights related terms in results
- **OCR support** — Extracts text from scanned PDFs automatically
- **Impact metrics** — Shows time saved vs manual review
- **Export results** — Download findings as CSV or formatted report
- **100% local** — All processing on your machine, no data leaves your network

## Quick Start

### Try the Demo (No Setup)

```bash
# Clone and start backend
cd backend
pip install -r requirements.txt
python main.py

# In another terminal, start frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` and click **"Load Sample Case"** to instantly load demo legal documents (police report, witness statement, forensic lab report).

### Sample Searches to Try
- `"weapon"` → finds knife, firearm, Glock 19
- `"vehicle description"` → finds sedan, car, truck references
- `"suspect behavior"` → finds nervous, sweating, spontaneous statements
- `"forensic evidence"` → finds DNA, fingerprints, lab analysis

## Tech Stack

| Layer | Technology |
|-------|------------|
| Search | Sentence-Transformers (all-MiniLM-L6-v2) |
| Backend | FastAPI, Python 3.9+ |
| Frontend | Next.js 16, TypeScript, Tailwind CSS |
| PDF Processing | PyMuPDF |
| OCR | Tesseract |

## Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- Tesseract OCR ([Windows](https://github.com/UB-Mannheim/tesseract/wiki) | `brew install tesseract` | `apt install tesseract-ocr`)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload and index a PDF |
| POST | `/api/search` | Semantic search with metrics |
| POST | `/api/demo/load` | Load sample case documents |
| POST | `/api/export/csv` | Export results as CSV |
| POST | `/api/export/report` | Export as formatted report |
| GET | `/api/documents` | List indexed documents |
| DELETE | `/api/documents` | Clear all documents |

## Project Structure

```
manifold/
├── backend/
│   ├── main.py              # API endpoints
│   ├── search_engine.py     # Semantic search + highlighting
│   ├── ocr_processor.py     # PDF text extraction + OCR
│   └── requirements.txt
└── frontend/
    └── app/page.tsx         # React UI
```

## How It Works

1. **Upload** — PDF is processed, text extracted (with OCR fallback for scans)
2. **Index** — Text is chunked and converted to vector embeddings
3. **Search** — Query is embedded and compared against all chunks via cosine similarity
4. **Highlight** — Related terms in results are identified semantically and highlighted
5. **Export** — Results can be downloaded for case documentation

## Performance

| Metric | Value |
|--------|-------|
| Search latency | <1 second for 10k+ pages |
| Embedding model | 384 dimensions, ~80MB |
| Chunk size | ~500 characters with overlap |

## License

MIT
