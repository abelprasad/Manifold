"""
FastAPI Server - Manifold
Handles PDF uploads, processing, and semantic search
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import shutil
from datetime import datetime
import json
import time
import csv
import io

from ocr_processor import PDFProcessor, process_pdf
from search_engine import SemanticSearchEngine


# Sample demo documents for instant demo experience
DEMO_DOCUMENTS = [
    {
        "filename": "Police_Report_2024-CR-1847.pdf",
        "page_count": 12,
        "file_size_mb": 2.4,
        "chunks": [
            {"chunk_id": 0, "page_num": 1, "text": "On March 15, 2024, at approximately 2:47 AM, officers responded to a report of a suspicious vehicle parked behind the Riverside Shopping Center at 1450 Commerce Drive. The reporting party, a security guard on patrol, observed a dark-colored sedan with its engine running and headlights off."},
            {"chunk_id": 1, "page_num": 1, "text": "Upon arrival, Officer Martinez approached the vehicle and made contact with the driver, later identified as JOHN DOE (DOB: 05/12/1985). The subject appeared nervous and was sweating profusely despite the cool temperature. A strong odor of marijuana emanated from the vehicle interior."},
            {"chunk_id": 2, "page_num": 2, "text": "During the subsequent search of the vehicle, officers discovered a black duffel bag in the trunk containing approximately 2.3 kilograms of a white powdery substance, field-tested positive for cocaine. Additionally, a loaded Glock 19 handgun with the serial number filed off was found under the driver's seat."},
            {"chunk_id": 3, "page_num": 3, "text": "The suspect was read his Miranda rights and placed under arrest. During booking, the suspect made spontaneous statements indicating knowledge of a larger distribution network operating out of the warehouse district on Fourth Street."},
            {"chunk_id": 4, "page_num": 4, "text": "Evidence collected includes: (1) One black duffel bag, (2) 2.3 kg white powder substance, (3) One Glock 19 pistol with defaced serial number, (4) $4,750 in cash in various denominations, (5) Three prepaid cellular phones, (6) Vehicle registration documents."},
            {"chunk_id": 5, "page_num": 5, "text": "Forensic analysis of the cellular phones revealed frequent communication with an unknown contact saved as 'SUPPLIER' over the past 60 days. Text messages referenced delivery schedules and payment amounts consistent with drug trafficking operations."},
        ]
    },
    {
        "filename": "Witness_Statement_Martinez.pdf",
        "page_count": 4,
        "file_size_mb": 0.8,
        "chunks": [
            {"chunk_id": 6, "page_num": 1, "text": "WITNESS STATEMENT - Maria Martinez, Security Officer at Riverside Shopping Center. I have been employed as a security guard for 3 years. On the night in question, I was conducting my regular patrol of the parking lot perimeter when I noticed an unfamiliar vehicle."},
            {"chunk_id": 7, "page_num": 1, "text": "The vehicle was a dark blue or black four-door sedan, possibly a Honda Accord or similar model. It was parked in the loading dock area, which is unusual as that area is typically empty after business hours. The engine was running but all lights were off."},
            {"chunk_id": 8, "page_num": 2, "text": "I observed the vehicle for approximately 5 minutes before calling police. During this time, I saw the driver appear to be talking on a cell phone. At one point, another vehicle briefly pulled up alongside, and I witnessed what appeared to be a hand-to-hand exchange through the windows."},
            {"chunk_id": 9, "page_num": 2, "text": "The second vehicle was a white pickup truck with a dent on the rear bumper. It departed heading eastbound on Commerce Drive approximately 2 minutes before police arrived. I did not get the license plate number but the truck had a distinctive red toolbox in the bed."},
        ]
    },
    {
        "filename": "Forensic_Lab_Report_24-0892.pdf",
        "page_count": 8,
        "file_size_mb": 1.6,
        "chunks": [
            {"chunk_id": 10, "page_num": 1, "text": "FORENSIC LABORATORY ANALYSIS REPORT - Case Number: 24-0892. Submitted evidence received on March 16, 2024. Analysis performed by Dr. Sarah Chen, Senior Forensic Chemist. Chain of custody verified and documented."},
            {"chunk_id": 11, "page_num": 2, "text": "SUBSTANCE ANALYSIS: Sample A (white powder from duffel bag) - Gas chromatography-mass spectrometry (GC-MS) confirms presence of cocaine hydrochloride at 87% purity. Total weight: 2,347 grams. Street value estimated at $180,000-$220,000."},
            {"chunk_id": 12, "page_num": 3, "text": "FINGERPRINT ANALYSIS: Latent prints recovered from the firearm match the suspect JOHN DOE with 12-point identification. Additional unidentified prints (designated UNKNOWN SUBJECT #1) were recovered from the ammunition magazine."},
            {"chunk_id": 13, "page_num": 4, "text": "DNA ANALYSIS: Biological material recovered from the duffel bag zipper yielded a partial DNA profile. CODIS search returned no matches. Sample preserved for future comparison."},
            {"chunk_id": 14, "page_num": 5, "text": "FIREARM EXAMINATION: The Glock 19 pistol was test-fired and ballistic comparison conducted. The weapon was found to be in working condition. Serial number restoration attempts using acid etching revealed partial number: 'PKF...47'. ATF trace request submitted."},
        ]
    }
]

# Initialize FastAPI app
app = FastAPI(
    title="Manifold API",
    description="Semantic search for PDF documents",
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
        "message": "Manifold API",
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
    Search across all loaded documents with timing metrics and semantic highlights
    """
    if not uploaded_documents:
        raise HTTPException(status_code=400, detail="No documents uploaded. Upload at least one PDF.")

    try:
        # Calculate total pages for metrics
        total_pages = sum(doc["page_count"] for doc in uploaded_documents.values())
        total_chunks = search_engine.get_chunk_count()

        # Time the search
        start_time = time.time()
        results = search_engine.search(request.query, request.top_k)

        # Add semantic highlights to each result
        for result in results:
            highlights = search_engine.find_semantic_highlights(
                request.query,
                result.get("text", ""),
                top_k=8,
                min_score=0.25
            )
            result["semantic_highlights"] = highlights

        search_time = time.time() - start_time

        # Calculate impact metrics
        # Assume manual review takes ~3 minutes per page
        manual_review_hours = (total_pages * 3) / 60
        time_saved_percentage = 99.9 if search_time < 1 else max(95, 100 - (search_time / (manual_review_hours * 3600)) * 100)

        return {
            "success": True,
            "query": request.query,
            "total_results": len(results),
            "searched_documents": len(uploaded_documents),
            "results": results,
            "metrics": {
                "search_time_seconds": round(search_time, 3),
                "total_pages_searched": total_pages,
                "total_chunks_searched": total_chunks,
                "manual_review_hours": round(manual_review_hours, 1),
                "time_saved_percentage": round(time_saved_percentage, 1)
            }
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


@app.post("/api/demo/load")
async def load_demo():
    """
    Load sample discovery documents for instant demo experience
    """
    global uploaded_documents

    try:
        # Clear existing data first
        uploaded_documents = {}
        search_engine.clear_index()

        # Load demo documents
        all_chunks = []
        for doc in DEMO_DOCUMENTS:
            safe_filename = f"demo_{doc['filename']}"

            # Prepare chunks with metadata
            for chunk in doc["chunks"]:
                chunk_copy = chunk.copy()
                chunk_copy["filename"] = doc["filename"]
                chunk_copy["safe_filename"] = safe_filename
                all_chunks.append(chunk_copy)

            # Store document info
            uploaded_documents[safe_filename] = {
                "filename": doc["filename"],
                "safe_filename": safe_filename,
                "file_path": f"demo/{doc['filename']}",
                "page_count": doc["page_count"],
                "total_chunks": len([c for c in doc["chunks"]]),
                "upload_time": datetime.now().isoformat(),
                "file_size_mb": doc["file_size_mb"],
                "is_demo": True
            }

        # Index all chunks
        search_engine.add_documents(all_chunks)

        total_pages = sum(doc["page_count"] for doc in DEMO_DOCUMENTS)

        return {
            "success": True,
            "message": "Demo documents loaded successfully",
            "documents_loaded": len(DEMO_DOCUMENTS),
            "total_pages": total_pages,
            "total_chunks": len(all_chunks),
            "sample_queries": [
                "What evidence was found in the vehicle?",
                "Who is the suspect and what were they doing?",
                "What did the witness observe?",
                "forensic analysis cocaine",
                "firearm serial number"
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading demo: {str(e)}")


@app.post("/api/export/csv")
async def export_results_csv(request: SearchRequest):
    """
    Export search results as CSV
    """
    if not uploaded_documents:
        raise HTTPException(status_code=400, detail="No documents to search")

    try:
        results = search_engine.search(request.query, request.top_k)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Rank", "Document", "Page", "Match Score", "Text Content"])

        # Data rows
        for i, result in enumerate(results, 1):
            writer.writerow([
                i,
                result.get("filename", "Unknown"),
                result.get("page_num", "N/A"),
                f"{result.get('score_percentage', 0):.1f}%",
                result.get("text", "")[:500]  # Truncate long text
            ])

        output.seek(0)

        # Generate filename
        safe_query = "".join(c if c.isalnum() else "_" for c in request.query[:30])
        filename = f"manifold_search_{safe_query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


@app.post("/api/export/report")
async def export_results_report(request: SearchRequest):
    """
    Export search results as a formatted text report
    """
    if not uploaded_documents:
        raise HTTPException(status_code=400, detail="No documents to search")

    try:
        start_time = time.time()
        results = search_engine.search(request.query, request.top_k)
        search_time = time.time() - start_time

        total_pages = sum(doc["page_count"] for doc in uploaded_documents.values())

        # Build report
        report_lines = [
            "=" * 70,
            "MANIFOLD SEMANTIC SEARCH REPORT",
            "=" * 70,
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Search Query: \"{request.query}\"",
            "",
            "--- SEARCH METRICS ---",
            f"Documents Searched: {len(uploaded_documents)}",
            f"Total Pages Analyzed: {total_pages}",
            f"Search Time: {search_time:.3f} seconds",
            f"Results Found: {len(results)}",
            "",
            "=" * 70,
            "SEARCH RESULTS",
            "=" * 70,
            ""
        ]

        for i, result in enumerate(results, 1):
            report_lines.extend([
                f"--- Result #{i} ---",
                f"Document: {result.get('filename', 'Unknown')}",
                f"Page: {result.get('page_num', 'N/A')}",
                f"Relevance Score: {result.get('score_percentage', 0):.1f}%",
                "",
                "Content:",
                result.get("text", ""),
                "",
                "-" * 40,
                ""
            ])

        report_lines.extend([
            "",
            "=" * 70,
            "END OF REPORT",
            "Generated by Manifold - AI-Powered Document Search",
            "=" * 70
        ])

        report_content = "\n".join(report_lines)

        safe_query = "".join(c if c.isalnum() else "_" for c in request.query[:30])
        filename = f"manifold_report_{safe_query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        return StreamingResponse(
            iter([report_content]),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
