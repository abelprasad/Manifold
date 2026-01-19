"""
FastAPI Server - Public Defender Evidence Search Portal
Handles PDF uploads, processing, and semantic search
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import shutil
from datetime import datetime
import json

from ocr_processor import PDFProcessor, process_pdf
from search_engine import SemanticSearchEngine

# Initialize FastAPI app
app = FastAPI(
    title="PD Evidence Search API",
    description="Semantic search for legal discovery documents",
    version="1.1.0"
)

# CORS - Allow Next.js frontend to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Global search engine (in production, this would be per-user session)
search_engine = SemanticSearchEngine()
# Store uploaded documents metadata: safe_filename -> DocumentInfo
uploaded_documents: Dict[str, dict] = {}


# Pydantic models for request/response
class SearchRequest(BaseModel):
    query: str
    top_k: int = 10


class SearchResult(BaseModel):
    chunk_id: int
    page_num: int
    text: str
    similarity_score: float
    score_percentage: float
    filename: Optional[str] = None


class DocumentInfo(BaseModel):
    filename: str
    safe_filename: str
    page_count: int
    total_chunks: int
    upload_time: str
    file_size_mb: float


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "PD Evidence Search API",
        "status": "running",
        "version": "1.1.0",
        "documents_loaded": len(uploaded_documents)
    }


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF document
    Appends to the current search index
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    try:
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # Process PDF
        print(f"Processing {safe_filename}...")
        processor = PDFProcessor(file_path)
        page_count = processor.get_page_count()
        
        # Extract text
        text_content = processor.extract_text()
        
        # Create chunks for search
        chunks = processor.chunk_text(text_content)
        
        # Inject filename into chunks so we know source
        for chunk in chunks:
            chunk["filename"] = file.filename
            chunk["safe_filename"] = safe_filename
        
        # Add chunks to search index
        search_engine.add_documents(chunks)
        
        # Store document info
        doc_info = {
            "filename": file.filename,
            "safe_filename": safe_filename,
            "file_path": file_path,
            "page_count": page_count,
            "total_chunks": len(chunks),
            "upload_time": datetime.now().isoformat(),
            "file_size_mb": round(file_size_mb, 2),
            "text_content": text_content
        }
        
        uploaded_documents[safe_filename] = doc_info
        
        return {
            "success": True,
            "message": "PDF processed and added to index",
            "document": {
                "filename": file.filename,
                "safe_filename": safe_filename,
                "page_count": page_count,
                "total_chunks": len(chunks),
                "upload_time": doc_info["upload_time"],
                "file_size_mb": doc_info["file_size_mb"]
            },
            "processing_stats": {
                "pages_with_ocr": sum(1 for page in text_content if page["method"] == "ocr"),
                "pages_direct_text": sum(1 for page in text_content if page["method"] == "direct"),
                "total_characters": sum(page["char_count"] for page in text_content)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    finally:
        file.file.close()


@app.get("/api/documents")
async def get_documents():
    """Get list of all uploaded documents"""
    docs_list = []
    for safe_name, doc in uploaded_documents.items():
        docs_list.append({
            "filename": doc["filename"],
            "safe_filename": doc["safe_filename"],
            "page_count": doc["page_count"],
            "total_chunks": doc["total_chunks"],
            "upload_time": doc["upload_time"],
            "file_size_mb": doc["file_size_mb"]
        })
    return {"documents": docs_list}


@app.post("/api/search")
async def search(request: SearchRequest):
    """
    Search across all loaded documents
    """
    if not uploaded_documents:
        raise HTTPException(status_code=400, detail="No documents uploaded. Upload at least one PDF.")
    
    try:
        # Perform semantic search
        results = search_engine.search(request.query, request.top_k)
        
        return {
            "success": True,
            "query": request.query,
            "total_results": len(results),
            "searched_documents": len(uploaded_documents),
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.delete("/api/documents")
async def clear_documents():
    """Clear all documents and reset index"""
    global uploaded_documents
    
    try:
        # Delete files from disk
        for doc in uploaded_documents.values():
            if os.path.exists(doc["file_path"]):
                os.remove(doc["file_path"])
        
        uploaded_documents = {}
        search_engine.clear_index()
        
        return {
            "success": True,
            "message": "All documents cleared and index reset"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """Get search engine statistics"""
    stats = search_engine.get_stats()
    stats["total_documents"] = len(uploaded_documents)
    return stats


# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
