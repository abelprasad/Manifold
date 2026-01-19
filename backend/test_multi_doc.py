import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Add parent directory to path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, search_engine, uploaded_documents

class TestMultiDocumentSearch(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Reset state
        uploaded_documents.clear()
        search_engine.clear_index()

    @patch('main.PDFProcessor')
    def test_multi_document_workflow(self, MockPDFProcessor):
        print("\n--- Testing Multi-Document Workflow ---")

        # --- Document 1 Setup: "Police Report" ---
        mock_processor_1 = MagicMock()
        mock_processor_1.get_page_count.return_value = 5
        # Simulate text extraction
        mock_processor_1.extract_text.return_value = [
            {"page_num": 1, "text": "The suspect was seen driving a red sedan.", "method": "direct", "char_count": 40},
            {"page_num": 2, "text": "A knife was found at the scene.", "method": "direct", "char_count": 30}
        ]
        # Simulate chunking
        mock_processor_1.chunk_text.return_value = [
            {"chunk_id": 0, "page_num": 1, "text": "The suspect was seen driving a red sedan.", "start_pos": 0, "end_pos": 40},
            {"chunk_id": 1, "page_num": 2, "text": "A knife was found at the scene.", "start_pos": 0, "end_pos": 30}
        ]

        # --- Document 2 Setup: "Witness Statement" ---
        mock_processor_2 = MagicMock()
        mock_processor_2.get_page_count.return_value = 2
        mock_processor_2.extract_text.return_value = [
            {"page_num": 1, "text": "I saw a red car speeding away.", "method": "direct", "char_count": 30}
        ]
        mock_processor_2.chunk_text.return_value = [
            {"chunk_id": 0, "page_num": 1, "text": "I saw a red car speeding away.", "start_pos": 0, "end_pos": 30}
        ]

        # Configure the mock to return different processors based on file path
        def side_effect(file_path):
            if "police_report.pdf" in file_path:
                return mock_processor_1
            else:
                return mock_processor_2
        
        MockPDFProcessor.side_effect = side_effect

        # --- Step 1: Upload Document 1 ---
        print("1. Uploading 'police_report.pdf'...")
        files = {'file': ('police_report.pdf', b'dummy content', 'application/pdf')}
        response = self.client.post("/api/upload", files=files)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['document']['filename'], 'police_report.pdf')
        
        # Verify internal state
        self.assertEqual(len(uploaded_documents), 1)
        
        # --- Step 2: Upload Document 2 ---
        print("2. Uploading 'witness_statement.pdf'...")
        files = {'file': ('witness_statement.pdf', b'dummy content', 'application/pdf')}
        response = self.client.post("/api/upload", files=files)
        self.assertEqual(response.status_code, 200)
        
        # Verify internal state
        self.assertEqual(len(uploaded_documents), 2)

        # --- Step 3: Search (Concept: "Vehicle") ---
        print("3. Searching for 'vehicle' (should match 'sedan' and 'car')...")
        search_payload = {"query": "vehicle", "top_k": 5}
        response = self.client.post("/api/search", json=search_payload)
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']

        print(f"   Found {len(results)} results.")
        
        # We expect matches from BOTH documents
        filenames_found = set(r['filename'] for r in results)
        print(f"   Sources found: {filenames_found}")
        
        self.assertIn('police_report.pdf', filenames_found)
        self.assertIn('witness_statement.pdf', filenames_found)

        # --- Step 4: Search (Specific: "Knife") ---
        print("4. Searching for 'weapon' (should match 'knife')...")
        search_payload = {"query": "weapon", "top_k": 5}
        response = self.client.post("/api/search", json=search_payload)
        results = response.json()['results']
        
        # Should mostly match the police report
        best_match = results[0]
        print(f"   Top result: {best_match['text']} (from {best_match['filename']})")
        self.assertEqual(best_match['filename'], 'police_report.pdf')
        self.assertIn('knife', best_match['text'].lower())

        print("\n✅ SUCCESS: Multi-document search works correctly!")

if __name__ == '__main__':
    unittest.main()
