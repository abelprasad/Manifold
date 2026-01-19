import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Add parent directory to path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, search_engine, uploaded_documents

# --- Test Data Fixtures ---
POLICE_REPORT_FILENAME = "police_report.pdf"
WITNESS_STATEMENT_FILENAME = "witness_statement.pdf"

MOCK_DOC_DATA = {
    POLICE_REPORT_FILENAME: {
        "page_count": 5,
        "text_content": [
            {"page_num": 1, "text": "The suspect was seen driving a red sedan.", "method": "direct", "char_count": 40},
            {"page_num": 2, "text": "A knife was found at the scene.", "method": "direct", "char_count": 30}
        ],
        "chunks": [
            {"chunk_id": 0, "page_num": 1, "text": "The suspect was seen driving a red sedan.", "start_pos": 0, "end_pos": 40},
            {"chunk_id": 1, "page_num": 2, "text": "A knife was found at the scene.", "start_pos": 0, "end_pos": 30}
        ]
    },
    WITNESS_STATEMENT_FILENAME: {
        "page_count": 2,
        "text_content": [
            {"page_num": 1, "text": "I saw a red car speeding away.", "method": "direct", "char_count": 30}
        ],
        "chunks": [
            {"chunk_id": 0, "page_num": 1, "text": "I saw a red car speeding away.", "start_pos": 0, "end_pos": 30}
        ]
    }
}

def create_mock_pdf_processor(filename: str) -> MagicMock:
    """Helper to create a configured MagicMock for PDFProcessor."""
    mock_data = MOCK_DOC_DATA[filename]
    mock_processor = MagicMock()
    mock_processor.get_page_count.return_value = mock_data["page_count"]
    mock_processor.extract_text.return_value = mock_data["text_content"]
    mock_processor.chunk_text.return_value = mock_data["chunks"]
    return mock_processor


class TestMultiDocumentSearch(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Reset state before each test
        uploaded_documents.clear()
        search_engine.clear_index()

    @patch('main.PDFProcessor')
    def test_multi_document_workflow(self, MockPDFProcessor):
        """
        Tests the full workflow:
        1. Upload multiple documents.
        2. Search for a term present in both.
        3. Verify results come from both sources.
        4. Search for a term present in only one.
        5. Verify the top result is from the correct source.
        """
        print("\n--- Testing Multi-Document Workflow ---")

        # Configure the mock to return the correct mock processor based on filename
        MockPDFProcessor.side_effect = lambda path: create_mock_pdf_processor(os.path.basename(path))

        # --- Step 1: Upload Documents ---
        print("1. Uploading documents...")
        for filename in MOCK_DOC_DATA.keys():
            with self.subTest(f"Uploading {filename}"):
                files = {'file': (filename, b'dummy content', 'application/pdf')}
                response = self.client.post("/api/upload", files=files)
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data['document']['filename'], filename)
        
        self.assertEqual(len(uploaded_documents), 2, "Should have two documents registered")
        self.assertEqual(search_engine.get_chunk_count(), 3, "Should have a total of 3 chunks indexed")

        # --- Step 2: Search for a concept ("vehicle") matching both documents ---
        print("2. Searching for a term matching both documents ('vehicle')...")
        search_payload = {"query": "vehicle", "top_k": 5}
        response = self.client.post("/api/search", json=search_payload)
        self.assertEqual(response.status_code, 200)
        
        results = response.json()['results']
        self.assertGreater(len(results), 1, "Should find at least two results")
        
        # Verify that results are from both documents
        filenames_in_results = {result['filename'] for result in results}
        print(f"   Sources found: {filenames_in_results}")
        self.assertIn(POLICE_REPORT_FILENAME, filenames_in_results)
        self.assertIn(WITNESS_STATEMENT_FILENAME, filenames_in_results)

        # --- Step 3: Search for a specific term ("weapon") in one document ---
        print("3. Searching for a term specific to one document ('weapon')...")
        search_payload = {"query": "weapon", "top_k": 3}
        response = self.client.post("/api/search", json=search_payload)
        self.assertEqual(response.status_code, 200)
        
        results = response.json()['results']
        self.assertGreaterEqual(len(results), 1)
        
        # The best match should be from the police report about the "knife"
        top_result = results[0]
        print(f"   Top result: '{top_result['text']}' (from {top_result['filename']})")
        self.assertEqual(top_result['filename'], POLICE_REPORT_FILENAME)
        self.assertIn('knife', top_result['text'].lower())

        print("\n✅ SUCCESS: Multi-document workflow tests passed!")

if __name__ == '__main__':
    unittest.main()