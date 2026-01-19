"""
OCR Processor - Extracts text from PDF documents
Handles both text-based PDFs and scanned image PDFs
"""

import pymupdf  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
from typing import List, Dict, Tuple

# Configure Tesseract path from environment variable or use default for Windows
TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
else:
    # If the path doesn't exist, pytesseract will fall back to searching the system's PATH.
    # We can add a log or print statement here if verbose feedback is needed.
    print(f"Warning: Tesseract path '{TESSERACT_PATH}' not found. Falling back to system PATH.")


class PDFProcessor:
    """Process PDF files and extract text content"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = None
        self.text_content = []
        
    def extract_text(self) -> List[Dict[str, any]]:
        """
        Extract text from PDF, using OCR for scanned pages if needed
        Returns: List of dicts with page_num, text, and method (direct/ocr)
        """
        try:
            self.doc = pymupdf.open(self.pdf_path)
            
            for page_num in range(len(self.doc)):
                page = self.doc[page_num]
                
                # Try direct text extraction first
                text = page.get_text()
                
                # If no text found, likely a scanned PDF - use OCR
                if len(text.strip()) < 50:  # Threshold for "empty" page
                    text = self._ocr_page(page)
                    method = "ocr"
                else:
                    method = "direct"
                
                self.text_content.append({
                    "page_num": page_num + 1,  # Human-readable page numbers (1-indexed)
                    "text": text,
                    "method": method,
                    "char_count": len(text)
                })
            
            return self.text_content
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
        
        finally:
            if self.doc:
                self.doc.close()
    
    def _ocr_page(self, page) -> str:
        """
        Perform OCR on a PDF page
        Converts page to image, then uses Tesseract
        """
        try:
            # Render page to image (higher DPI = better OCR accuracy)
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))  # 2x scale for better quality
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Perform OCR
            text = pytesseract.image_to_string(img)
            
            return text
            
        except Exception as e:
            return f"[OCR Error on this page: {str(e)}]"
    
    def get_page_count(self) -> int:
        """Get total number of pages in PDF"""
        try:
            doc = pymupdf.open(self.pdf_path)
            count = len(doc)
            doc.close()
            return count
        except:
            return 0
    
    def chunk_text(self, text_content: List[Dict], chunk_size: int = 500) -> List[Dict]:
        """
        Split text into chunks for semantic search
        
        Args:
            text_content: List of page dicts from extract_text()
            chunk_size: Number of characters per chunk
        
        Returns:
            List of dicts with chunk_id, page_num, text, start_pos, end_pos
        """
        chunks = []
        chunk_id = 0
        
        for page_data in text_content:
            page_num = page_data["page_num"]
            text = page_data["text"]
            
            # Split into chunks, trying to break at sentence boundaries
            start = 0
            while start < len(text):
                end = start + chunk_size
                
                # Try to break at sentence end (period + space)
                if end < len(text):
                    # Look for sentence boundary within next 100 chars
                    boundary = text.find(". ", end, end + 100)
                    if boundary != -1:
                        end = boundary + 1
                
                chunk_text = text[start:end].strip()
                
                if chunk_text:  # Only add non-empty chunks
                    chunks.append({
                        "chunk_id": chunk_id,
                        "page_num": page_num,
                        "text": chunk_text,
                        "start_pos": start,
                        "end_pos": end
                    })
                    chunk_id += 1
                
                start = end
        
        return chunks


# Utility function for quick testing
def process_pdf(pdf_path: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Process a PDF and return both full text and chunks
    
    Returns:
        (text_content, chunks)
    """
    processor = PDFProcessor(pdf_path)
    text_content = processor.extract_text()
    chunks = processor.chunk_text(text_content)
    
    return text_content, chunks


if __name__ == "__main__":
    # Test the processor
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ocr_processor.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    print(f"Processing: {pdf_path}")
    
    processor = PDFProcessor(pdf_path)
    print(f"Total pages: {processor.get_page_count()}")
    
    text_content = processor.extract_text()
    print(f"\nExtracted text from {len(text_content)} pages")
    
    for page in text_content[:3]:  # Show first 3 pages
        print(f"\n--- Page {page['page_num']} ({page['method']}) ---")
        print(f"Characters: {page['char_count']}")
        print(f"Preview: {page['text'][:200]}...")
    
    chunks = processor.chunk_text(text_content)
    print(f"\nCreated {len(chunks)} text chunks for search")