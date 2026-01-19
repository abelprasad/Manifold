# Manifold

A powerful, AI-driven semantic search tool designed to quickly analyze and search through PDF documents. Unlike simple keyword searches, this tool uses natural language processing to understand the *meaning* of your query, helping you find relevant evidence even if the exact words don't match.

![Project Status](https://img.shields.io/badge/Status-Prototype-orange)
![Python](https://img.shields.io/badge/Backend-FastAPI-green)
![TypeScript](https://img.shields.io/badge/Frontend-Next.js-blue)

## 🌟 Key Features

*   **Semantic Search**: Uses `sentence-transformers` (BERT-based models) to find contextually relevant information, not just keyword matches. e.g., searching for "weapon" will find mentions of "gun", "knife", or "firearm".
*   **Intelligent OCR**: Automatically detects scanned PDFs (images) and applies Tesseract OCR to extract text. Handles hybrid documents (text + images) seamlessly.
*   **Relevance Scoring**: Ranks search results by similarity score, showing you the most pertinent evidence first.
*   **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS for a distraction-free reading experience.
*   **Privacy-Focused**: All processing happens locally on your machine. No data is sent to external cloud APIs.

## 🛠️ Tech Stack

### Backend
*   **Language**: Python 3.9+
*   **Framework**: FastAPI
*   **PDF Processing**: PyMuPDF (Fitz)
*   **OCR**: Tesseract OCR & Pytesseract
*   **ML/AI**: Sentence-Transformers, PyTorch, NumPy

### Frontend
*   **Framework**: Next.js 16 (App Router)
*   **Language**: TypeScript
*   **Styling**: Tailwind CSS v4
*   **Icons**: Lucide React

## 📋 Prerequisites

Before setting up, ensure you have the following installed:

1.  **Python 3.9+**
2.  **Node.js 18+** & **npm**
3.  **Tesseract OCR Engine**:
    *   **Windows**: Download and install from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
    *   **macOS**: `brew install tesseract`
    *   **Linux**: `sudo apt-get install tesseract-ocr`

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd manifold
```

### 2. Backend Setup
Set up the Python environment and install dependencies.

```bash
# Navigate to backend
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
..\venv\Scripts\activate
# macOS/Linux:
# source ../venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

> **Note**: The first time you run the backend, it will download the ML model (~80MB), which may take a few moments.

### 3. Frontend Setup
Install the Node.js dependencies.

```bash
# Open a new terminal and navigate to frontend
cd frontend

# Install dependencies
npm install
```

## 🏃‍♂️ Running the Application

You need to run both the backend and frontend servers simultaneously.

### Start the Backend
In your backend terminal (with `venv` activated):

```bash
# From the backend directory
uvicorn main:app --reload --port 8000
```
*The API will run at `http://localhost:8000`*

### Start the Frontend
In your frontend terminal:

```bash
# From the frontend directory
npm run dev
```
*The UI will run at `http://localhost:3000`*

## 📖 Usage Guide

1.  Open your browser to `http://localhost:3000`.
2.  Click **"Upload Discovery Document"** or drag & drop a PDF file.
3.  Wait for the processing to complete (OCR + Indexing).
    *   *Tip*: Processing speed depends on your CPU and the document length.
4.  Once loaded, type a query into the search bar (e.g., *"What did the witness say about the car?"*).
5.  Review the ranked search results below, which show the specific page number and relevant text snippet.

## 📂 Project Structure

```
manifold/
├── backend/
│   ├── main.py              # FastAPI entry point & endpoints
│   ├── ocr_processor.py     # PDF reading & OCR logic
│   ├── search_engine.py     # Semantic search & embedding logic
│   └── uploads/             # Temp storage for uploaded files
│
└── frontend/
    ├── app/
    │   └── page.tsx         # Main UI component (Search & Upload)
    ├── public/
    └── package.json         # Frontend dependencies
```

## 🔧 Troubleshooting

*   **Tesseract Not Found Error**:
    *   This error means the backend couldn't find the Tesseract OCR engine.
    *   **1. Ensure Tesseract is in your system's PATH**: The easiest solution is to add your Tesseract installation directory (e.g., `C:\Program Files\Tesseract-OCR`) to your system's `PATH` environment variable. The application will find it automatically.
    *   **2. Set the `TESSERACT_PATH` Environment Variable**: If you don't want to modify your system `PATH`, you can tell the application exactly where to find the executable.
        *   **Windows (Command Prompt)**: 
            ```cmd
            set TESSERACT_PATH="C:\path\to\your\Tesseract-OCR\tesseract.exe"
            uvicorn main:app --reload
            ```
        *   **Windows (PowerShell)**:
            ```powershell
            $env:TESSERACT_PATH="C:\path\to\your\Tesseract-OCR\tesseract.exe"
            uvicorn main:app --reload
            ```
        *   **macOS/Linux**:
            ```bash
            export TESSERACT_PATH="/path/to/your/tesseract"
            uvicorn main:app --reload
            ```
*   **Upload Fails**:
    *   Check the backend console logs. Ensure the `backend/uploads` directory is writable.
*   **Slow Search**:
    *   The first search might be slightly slower as the model initializes. Subsequent searches should be near-instant.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
