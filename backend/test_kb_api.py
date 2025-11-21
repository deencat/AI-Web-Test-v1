"""Test Knowledge Base API endpoints."""
import sys
import io
import requests
import json
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/v1"
TOKEN = None

def print_header(text: str):
    """Print formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print('=' * 70)

def print_test(text: str):
    """Print test name."""
    print(f"\n[TEST] {text}")

def print_result(success: bool, message: str = ""):
    """Print test result."""
    if success:
        print(f"  [OK] {message if message else 'Passed'}")
    else:
        print(f"  [FAIL] {message if message else 'Failed'}")

def login():
    """Login and get access token."""
    global TOKEN
    print_test("Login as admin")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        TOKEN = response.json()["access_token"]
        print_result(True, f"Token: {TOKEN[:30]}...")
        return True
    else:
        print_result(False, f"Status: {response.status_code}")
        return False

def test_list_categories():
    """Test listing KB categories."""
    print_test("List KB categories")
    
    response = requests.get(f"{BASE_URL}/kb/categories")
    
    if response.status_code == 200:
        categories = response.json()
        print_result(True, f"Found {len(categories)} categories")
        
        # Verify predefined categories
        category_names = [c["name"] for c in categories]
        expected = ["System Guide", "Product Info", "Process", "Login Flows"]
        
        for name in expected:
            if name in category_names:
                print(f"    - {name} (OK)")
            else:
                print(f"    - {name} (MISSING!)")
                return False
        
        return True
    else:
        print_result(False, f"Status: {response.status_code}")
        return False

def test_create_category():
    """Test creating a custom category."""
    print_test("Create custom category")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Use timestamp to ensure unique name
    import time
    unique_name = f"Test Category {int(time.time())}"
    
    category_data = {
        "name": unique_name,
        "description": "A test category for automated testing",
        "color": "#FF5733",
        "icon": "test"
    }
    
    response = requests.post(
        f"{BASE_URL}/kb/categories",
        json=category_data,
        headers=headers
    )
    
    if response.status_code == 201:
        category = response.json()
        print_result(True, f"Created category ID: {category['id']}")
        return category["id"]
    else:
        print_result(False, f"Status: {response.status_code}, {response.text}")
        return None

def create_test_file(content: str = "Test document content") -> Path:
    """Create a test TXT file."""
    test_file = Path("test_upload.txt")
    test_file.write_text(content, encoding='utf-8')
    return test_file

def test_upload_document(category_id: int):
    """Test uploading a document."""
    print_test("Upload TXT document")
    
    # Create test file
    test_file = create_test_file("This is a test document for the Knowledge Base system.\nIt contains test content.")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    with open(test_file, 'rb') as f:
        files = {"file": ("test_document.txt", f, "text/plain")}
        data = {
            "title": "Test Document",
            "category_id": category_id,
            "description": "A test document uploaded via API"
        }
        
        response = requests.post(
            f"{BASE_URL}/kb/upload",
            files=files,
            data=data,
            headers=headers
        )
    
    # Clean up test file
    test_file.unlink()
    
    if response.status_code == 201:
        doc = response.json()
        print_result(True, f"Uploaded document ID: {doc['id']}")
        print(f"    Title: {doc['title']}")
        print(f"    File type: {doc['file_type']}")
        print(f"    File size: {doc['file_size']} bytes")
        return doc["id"]
    else:
        print_result(False, f"Status: {response.status_code}, {response.text}")
        return None

def test_list_documents():
    """Test listing documents."""
    print_test("List documents")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{BASE_URL}/kb", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print_result(True, f"Total documents: {result['total']}")
        print(f"    Items returned: {len(result['items'])}")
        
        if result['items']:
            doc = result['items'][0]
            print(f"    First doc: {doc['title']} ({doc['file_type']})")
        
        return True
    else:
        print_result(False, f"Status: {response.status_code}")
        return False

def test_get_document(doc_id: int):
    """Test getting document details."""
    print_test(f"Get document details (ID: {doc_id})")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{BASE_URL}/kb/{doc_id}", headers=headers)
    
    if response.status_code == 200:
        doc = response.json()
        print_result(True, f"Document: {doc['title']}")
        print(f"    Description: {doc['description']}")
        print(f"    Content length: {len(doc['content']) if doc['content'] else 0} chars")
        print(f"    Referenced count: {doc['referenced_count']}")
        print(f"    Category: {doc['category']['name']}")
        return True
    else:
        print_result(False, f"Status: {response.status_code}")
        return False

def test_update_document(doc_id: int):
    """Test updating document metadata."""
    print_test(f"Update document (ID: {doc_id})")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    updates = {
        "title": "Updated Test Document",
        "description": "Updated description via API test"
    }
    
    response = requests.put(
        f"{BASE_URL}/kb/{doc_id}",
        json=updates,
        headers=headers
    )
    
    if response.status_code == 200:
        doc = response.json()
        print_result(True, f"Updated: {doc['title']}")
        return True
    else:
        print_result(False, f"Status: {response.status_code}")
        return False

def test_get_statistics():
    """Test getting KB statistics."""
    print_test("Get KB statistics")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{BASE_URL}/kb/stats", headers=headers)
    
    if response.status_code == 200:
        stats = response.json()
        print_result(True)
        print(f"    Total documents: {stats['total_documents']}")
        print(f"    Total size: {stats['total_size_mb']} MB")
        print(f"    By category: {json.dumps(stats['by_category'], indent=8)}")
        print(f"    By file type: {json.dumps(stats['by_file_type'], indent=8)}")
        return True
    else:
        print_result(False, f"Status: {response.status_code}")
        return False

def test_search_documents():
    """Test document search."""
    print_test("Search documents")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/kb",
        params={"search": "test"},
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print_result(True, f"Found {result['total']} documents matching 'test'")
        return True
    else:
        print_result(False, f"Status: {response.status_code}")
        return False

def test_filter_by_category(category_id: int):
    """Test filtering documents by category."""
    print_test(f"Filter by category (ID: {category_id})")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/kb",
        params={"category_id": category_id},
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print_result(True, f"Found {result['total']} documents in category")
        return True
    else:
        print_result(False, f"Status: {response.status_code}")
        return False

def test_delete_document(doc_id: int):
    """Test deleting a document."""
    print_test(f"Delete document (ID: {doc_id})")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.delete(f"{BASE_URL}/kb/{doc_id}", headers=headers)
    
    if response.status_code == 204:
        print_result(True, "Document deleted")
        return True
    else:
        print_result(False, f"Status: {response.status_code}")
        return False

def main():
    """Run all KB API tests."""
    print_header("Knowledge Base API Tests")
    print("Testing: http://127.0.0.1:8000/api/v1/kb")
    print("Backend must be running!")
    
    # Track results
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Login
    if not login():
        print("\n[FATAL] Login failed. Ensure backend is running.")
        return False
    tests_passed += 1
    
    # Test 2: List categories
    if test_list_categories():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 3: Create category
    category_id = test_create_category()
    if category_id:
        tests_passed += 1
    else:
        tests_failed += 1
        # Use a default category for remaining tests
        category_id = 1  # Assume first category exists
    
    # Test 4: Upload document
    doc_id = test_upload_document(category_id)
    if doc_id:
        tests_passed += 1
    else:
        tests_failed += 1
        print("\n[SKIP] Remaining tests require successful upload")
        return False
    
    # Test 5: List documents
    if test_list_documents():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 6: Get document details
    if test_get_document(doc_id):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 7: Update document
    if test_update_document(doc_id):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 8: Get statistics
    if test_get_statistics():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 9: Search documents
    if test_search_documents():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 10: Filter by category
    if test_filter_by_category(category_id):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 11: Delete document
    if test_delete_document(doc_id):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Summary
    print_header("Test Summary")
    print(f"\nTotal Tests: {tests_passed + tests_failed}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n[SUCCESS] All KB API tests passed!")
        print("\nDay 4 Knowledge Base System: COMPLETE")
        return True
    else:
        print(f"\n[FAILURE] {tests_failed} test(s) failed")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

