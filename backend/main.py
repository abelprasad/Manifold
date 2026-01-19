"""
FastAPI Server - Public Defender Evidence Search Portal
Handles PDF uploads, processing, and semantic search
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
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
    version="1.0.0"
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
current_document = None  # Tracks currently loaded document


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


class DocumentInfo(BaseModel):
    filename: str
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
        "version": "1.0.0"
    }


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF document
    
    Returns document info and processing stats
    """
    global current_document
    
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
        
        # Index chunks for semantic search
        search_engine.index_documents(chunks)
        
        # Store current document info
        current_document = {
            "filename": file.filename,
            "safe_filename": safe_filename,
            "file_path": file_path,
            "page_count": page_count,
            "total_chunks": len(chunks),
            "upload_time": datetime.now().isoformat(),
            "file_size_mb": round(file_size_mb, 2),
            "text_content": text_content,
            "chunks": chunks
        }
        
        return {
            "success": True,
            "message": "PDF processed successfully",
            "document": {
                "filename": file.filename,
                "page_count": page_count,
                "total_chunks": len(chunks),
                "upload_time": current_document["upload_time"],
                "file_size_mb": current_document["file_size_mb"]
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


@app.post("/api/search")
async def search(request: SearchRequest):
    """
    Search the currently loaded document
    
    Returns ranked list of relevant text chunks
    """
    if current_document is None:
        raise HTTPException(status_code=400, detail="No document uploaded. Upload a PDF first.")
    
    try:
        # Perform semantic search
        results = search_engine.search(request.query, request.top_k)
        
        return {
            "success": True,
            "query": request.query,
            "total_results": len(results),
            "document": current_document["filename"],
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/api/document/info")
async def get_document_info():
    """Get info about currently loaded document"""
    if current_document is None:
        raise HTTPException(status_code=400, detail="No document currently loaded")
    
    return {
        "filename": current_document["filename"],
        "page_count": current_document["page_count"],
        "total_chunks": current_document["total_chunks"],
        "upload_time": current_document["upload_time"],
        "file_size_mb": current_document["file_size_mb"]
    }


@app.get("/api/document/page/{page_num}")
async def get_page_text(page_num: int):
    """Get full text of a specific page"""
    if current_document is None:
        raise HTTPException(status_code=400, detail="No document currently loaded")
    
    # Find page in text_content
    page_data = next(
        (page for page in current_document["text_content"] if page["page_num"] == page_num),
        None
    )
    
    if page_data is None:
        raise HTTPException(status_code=404, detail=f"Page {page_num} not found")
    
    return page_data


@app.delete("/api/document")
async def delete_document():
    """Delete currently loaded document"""
    global current_document
    
    if current_document is None:
        raise HTTPException(status_code=400, detail="No document currently loaded")
    
    try:
        # Delete file from disk
        if os.path.exists(current_document["file_path"]):
            os.remove(current_document["file_path"])
        
        filename = current_document["filename"]
        current_document = None
        
        return {
            "success": True,
            "message": f"Document '{filename}' deleted successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """Get search engine statistics"""
    stats = search_engine.get_stats()
    
    if current_document:
        stats["current_document"] = {
            "filename": current_document["filename"],
            "page_count": current_document["page_count"]
        }
    
    return stats


# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)