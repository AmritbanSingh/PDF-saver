#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for PDF Management System
Tests all CRUD operations for folders and files, including PDF upload/download functionality
"""

import requests
import json
import base64
import os
import tempfile
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Backend URL from environment
BACKEND_URL = "https://66688753-baee-43b6-a49b-f7d910a2636f.preview.emergentagent.com/api"

class PDFTestManager:
    def __init__(self):
        self.session = requests.Session()
        self.created_folders = []
        self.created_files = []
        
    def create_test_pdf(self, filename="test_document.pdf", content="Test PDF Content"):
        """Create a test PDF file in memory"""
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, content)
        p.drawString(100, 730, f"Filename: {filename}")
        p.drawString(100, 710, "This is a test PDF for API testing")
        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    def test_health_check(self):
        """Test if backend is running"""
        print("🔍 Testing health check...")
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                print("✅ Backend health check passed")
                return True
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend health check failed: {str(e)}")
            return False
    
    def test_folder_operations(self):
        """Test all folder CRUD operations"""
        print("\n📁 Testing Folder Operations...")
        
        # Test 1: Create root folder
        print("1. Creating root folder...")
        folder_data = {"name": "Research Papers", "parent_id": None}
        response = self.session.post(f"{BACKEND_URL}/folders", json=folder_data)
        
        if response.status_code != 200:
            print(f"❌ Failed to create root folder: {response.status_code} - {response.text}")
            return False
        
        root_folder = response.json()
        self.created_folders.append(root_folder["id"])
        print(f"✅ Root folder created: {root_folder['name']} (ID: {root_folder['id']})")
        
        # Test 2: Create subfolder
        print("2. Creating subfolder...")
        subfolder_data = {"name": "Machine Learning", "parent_id": root_folder["id"]}
        response = self.session.post(f"{BACKEND_URL}/folders", json=subfolder_data)
        
        if response.status_code != 200:
            print(f"❌ Failed to create subfolder: {response.status_code} - {response.text}")
            return False
        
        subfolder = response.json()
        self.created_folders.append(subfolder["id"])
        print(f"✅ Subfolder created: {subfolder['name']} (ID: {subfolder['id']})")
        
        # Test 3: List all folders
        print("3. Listing all folders...")
        response = self.session.get(f"{BACKEND_URL}/folders")
        
        if response.status_code != 200:
            print(f"❌ Failed to list folders: {response.status_code} - {response.text}")
            return False
        
        folders = response.json()
        print(f"✅ Retrieved {len(folders)} folders")
        
        # Verify our folders are in the list
        folder_ids = [f["id"] for f in folders]
        if root_folder["id"] not in folder_ids or subfolder["id"] not in folder_ids:
            print("❌ Created folders not found in folder list")
            return False
        
        # Test 4: Rename folder
        print("4. Renaming folder...")
        rename_data = {"name": "Deep Learning Research"}
        response = self.session.put(f"{BACKEND_URL}/folders/{subfolder['id']}", json=rename_data)
        
        if response.status_code != 200:
            print(f"❌ Failed to rename folder: {response.status_code} - {response.text}")
            return False
        
        renamed_folder = response.json()
        print(f"✅ Folder renamed to: {renamed_folder['name']}")
        
        # Test 5: Try to rename non-existent folder
        print("5. Testing error handling for non-existent folder...")
        fake_id = "non-existent-folder-id"
        response = self.session.put(f"{BACKEND_URL}/folders/{fake_id}", json={"name": "Should Fail"})
        
        if response.status_code != 404:
            print(f"❌ Expected 404 for non-existent folder, got: {response.status_code}")
            return False
        
        print("✅ Proper error handling for non-existent folder")
        
        return True
    
    def test_file_upload_operations(self):
        """Test PDF file upload with validation"""
        print("\n📄 Testing File Upload Operations...")
        
        # First, create a folder to upload files to
        folder_data = {"name": "Academic Papers", "parent_id": None}
        folder_response = self.session.post(f"{BACKEND_URL}/folders", json=folder_data)
        if folder_response.status_code != 200:
            print("❌ Failed to create folder for file tests")
            return False
        
        test_folder = folder_response.json()
        self.created_folders.append(test_folder["id"])
        
        # Test 1: Upload valid PDF file
        print("1. Uploading valid PDF file...")
        pdf_content = self.create_test_pdf("neural_networks.pdf", "Neural Networks Research Paper")
        
        files = {"file": ("neural_networks.pdf", pdf_content, "application/pdf")}
        data = {"folder_id": test_folder["id"]}
        
        response = self.session.post(f"{BACKEND_URL}/files/upload", files=files, data=data)
        
        if response.status_code != 200:
            print(f"❌ Failed to upload PDF: {response.status_code} - {response.text}")
            return False
        
        uploaded_file = response.json()
        self.created_files.append(uploaded_file["id"])
        print(f"✅ PDF uploaded successfully: {uploaded_file['name']} (Size: {uploaded_file['size']} bytes)")
        
        # Test 2: Upload PDF to root (no folder)
        print("2. Uploading PDF to root directory...")
        pdf_content2 = self.create_test_pdf("computer_vision.pdf", "Computer Vision Research")
        
        files = {"file": ("computer_vision.pdf", pdf_content2, "application/pdf")}
        
        response = self.session.post(f"{BACKEND_URL}/files/upload", files=files)
        
        if response.status_code != 200:
            print(f"❌ Failed to upload PDF to root: {response.status_code} - {response.text}")
            return False
        
        root_file = response.json()
        self.created_files.append(root_file["id"])
        print(f"✅ PDF uploaded to root: {root_file['name']}")
        
        # Test 3: Try to upload non-PDF file (should fail)
        print("3. Testing PDF validation with non-PDF file...")
        text_content = b"This is not a PDF file"
        files = {"file": ("document.txt", text_content, "text/plain")}
        
        response = self.session.post(f"{BACKEND_URL}/files/upload", files=files)
        
        if response.status_code != 400:
            print(f"❌ Expected 400 for non-PDF file, got: {response.status_code}")
            return False
        
        print("✅ Proper validation: non-PDF files rejected")
        
        return True
    
    def test_file_management_operations(self):
        """Test file listing, renaming, moving, and deletion"""
        print("\n🔧 Testing File Management Operations...")
        
        # Test 1: List all files
        print("1. Listing all files...")
        response = self.session.get(f"{BACKEND_URL}/files")
        
        if response.status_code != 200:
            print(f"❌ Failed to list files: {response.status_code} - {response.text}")
            return False
        
        all_files = response.json()
        print(f"✅ Retrieved {len(all_files)} files")
        
        if len(self.created_files) == 0:
            print("❌ No files available for testing file operations")
            return False
        
        test_file_id = self.created_files[0]
        
        # Test 2: Rename file
        print("2. Renaming file...")
        rename_data = {"name": "advanced_neural_networks.pdf"}
        response = self.session.put(f"{BACKEND_URL}/files/{test_file_id}", json=rename_data)
        
        if response.status_code != 200:
            print(f"❌ Failed to rename file: {response.status_code} - {response.text}")
            return False
        
        renamed_file = response.json()
        print(f"✅ File renamed to: {renamed_file['name']}")
        
        # Test 3: Move file to different folder (if we have folders)
        if len(self.created_folders) > 0:
            print("3. Moving file to different folder...")
            move_data = {"folder_id": self.created_folders[0]}
            response = self.session.put(f"{BACKEND_URL}/files/{test_file_id}", json=move_data)
            
            if response.status_code != 200:
                print(f"❌ Failed to move file: {response.status_code} - {response.text}")
                return False
            
            moved_file = response.json()
            print(f"✅ File moved to folder: {moved_file['folder_id']}")
        
        # Test 4: List files in specific folder
        if len(self.created_folders) > 0:
            print("4. Listing files in specific folder...")
            response = self.session.get(f"{BACKEND_URL}/files?folder_id={self.created_folders[0]}")
            
            if response.status_code != 200:
                print(f"❌ Failed to list files in folder: {response.status_code} - {response.text}")
                return False
            
            folder_files = response.json()
            print(f"✅ Retrieved {len(folder_files)} files in folder")
        
        # Test 5: Error handling for non-existent file
        print("5. Testing error handling for non-existent file...")
        fake_file_id = "non-existent-file-id"
        response = self.session.put(f"{BACKEND_URL}/files/{fake_file_id}", json={"name": "should_fail.pdf"})
        
        if response.status_code != 404:
            print(f"❌ Expected 404 for non-existent file, got: {response.status_code}")
            return False
        
        print("✅ Proper error handling for non-existent file")
        
        return True
    
    def test_file_download_operations(self):
        """Test file download functionality"""
        print("\n⬇️ Testing File Download Operations...")
        
        if len(self.created_files) == 0:
            print("❌ No files available for download testing")
            return False
        
        test_file_id = self.created_files[0]
        
        # Test 1: Download existing file
        print("1. Downloading existing file...")
        response = self.session.get(f"{BACKEND_URL}/files/{test_file_id}/download")
        
        if response.status_code != 200:
            print(f"❌ Failed to download file: {response.status_code} - {response.text}")
            return False
        
        # Check content type
        if response.headers.get("content-type") != "application/pdf":
            print(f"❌ Wrong content type: {response.headers.get('content-type')}")
            return False
        
        # Check content disposition header
        if "attachment" not in response.headers.get("content-disposition", ""):
            print("❌ Missing or incorrect Content-Disposition header")
            return False
        
        # Check if content is valid (should be PDF bytes)
        content = response.content
        if len(content) == 0:
            print("❌ Downloaded file is empty")
            return False
        
        # Basic PDF validation (PDF files start with %PDF)
        if not content.startswith(b"%PDF"):
            print("❌ Downloaded content is not a valid PDF")
            return False
        
        print(f"✅ File downloaded successfully ({len(content)} bytes)")
        
        # Test 2: Try to download non-existent file
        print("2. Testing error handling for non-existent file download...")
        fake_file_id = "non-existent-file-id"
        response = self.session.get(f"{BACKEND_URL}/files/{fake_file_id}/download")
        
        if response.status_code != 404:
            print(f"❌ Expected 404 for non-existent file download, got: {response.status_code}")
            return False
        
        print("✅ Proper error handling for non-existent file download")
        
        return True
    
    def test_folder_deletion_cascade(self):
        """Test folder deletion and cascading to files"""
        print("\n🗑️ Testing Folder Deletion with Cascade...")
        
        # Create a test folder with files
        folder_data = {"name": "Temporary Research", "parent_id": None}
        folder_response = self.session.post(f"{BACKEND_URL}/folders", json=folder_data)
        
        if folder_response.status_code != 200:
            print("❌ Failed to create test folder for deletion")
            return False
        
        temp_folder = folder_response.json()
        
        # Upload a file to this folder
        pdf_content = self.create_test_pdf("temp_paper.pdf", "Temporary Research Paper")
        files = {"file": ("temp_paper.pdf", pdf_content, "application/pdf")}
        data = {"folder_id": temp_folder["id"]}
        
        file_response = self.session.post(f"{BACKEND_URL}/files/upload", files=files, data=data)
        
        if file_response.status_code != 200:
            print("❌ Failed to upload file to test folder")
            return False
        
        temp_file = file_response.json()
        
        # Verify file exists in folder
        files_response = self.session.get(f"{BACKEND_URL}/files?folder_id={temp_folder['id']}")
        if files_response.status_code != 200 or len(files_response.json()) == 0:
            print("❌ File not found in folder before deletion")
            return False
        
        print(f"✅ Test setup complete: folder with file created")
        
        # Delete the folder
        print("Deleting folder (should cascade to files)...")
        delete_response = self.session.delete(f"{BACKEND_URL}/folders/{temp_folder['id']}")
        
        if delete_response.status_code != 200:
            print(f"❌ Failed to delete folder: {delete_response.status_code} - {delete_response.text}")
            return False
        
        print("✅ Folder deleted successfully")
        
        # Verify folder is gone
        folders_response = self.session.get(f"{BACKEND_URL}/folders")
        if folders_response.status_code == 200:
            folder_ids = [f["id"] for f in folders_response.json()]
            if temp_folder["id"] in folder_ids:
                print("❌ Folder still exists after deletion")
                return False
        
        # Verify file is also gone (cascade deletion)
        file_check_response = self.session.get(f"{BACKEND_URL}/files/{temp_file['id']}/download")
        if file_check_response.status_code != 404:
            print("❌ File still exists after folder deletion (cascade failed)")
            return False
        
        print("✅ Cascade deletion working: file removed with folder")
        
        return True
    
    def test_file_deletion(self):
        """Test individual file deletion"""
        print("\n🗑️ Testing File Deletion...")
        
        if len(self.created_files) == 0:
            print("❌ No files available for deletion testing")
            return False
        
        # Use the last created file for deletion test
        test_file_id = self.created_files[-1]
        
        # Verify file exists before deletion
        response = self.session.get(f"{BACKEND_URL}/files/{test_file_id}/download")
        if response.status_code != 200:
            print("❌ Test file doesn't exist before deletion test")
            return False
        
        # Delete the file
        print("Deleting file...")
        delete_response = self.session.delete(f"{BACKEND_URL}/files/{test_file_id}")
        
        if delete_response.status_code != 200:
            print(f"❌ Failed to delete file: {delete_response.status_code} - {delete_response.text}")
            return False
        
        print("✅ File deleted successfully")
        
        # Verify file is gone
        verify_response = self.session.get(f"{BACKEND_URL}/files/{test_file_id}/download")
        if verify_response.status_code != 404:
            print("❌ File still exists after deletion")
            return False
        
        print("✅ File properly removed from system")
        
        # Remove from our tracking list
        self.created_files.remove(test_file_id)
        
        return True
    
    def cleanup(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete remaining files
        for file_id in self.created_files[:]:
            try:
                response = self.session.delete(f"{BACKEND_URL}/files/{file_id}")
                if response.status_code == 200:
                    print(f"✅ Cleaned up file: {file_id}")
                    self.created_files.remove(file_id)
            except Exception as e:
                print(f"⚠️ Failed to cleanup file {file_id}: {str(e)}")
        
        # Delete remaining folders
        for folder_id in self.created_folders[:]:
            try:
                response = self.session.delete(f"{BACKEND_URL}/folders/{folder_id}")
                if response.status_code == 200:
                    print(f"✅ Cleaned up folder: {folder_id}")
                    self.created_folders.remove(folder_id)
            except Exception as e:
                print(f"⚠️ Failed to cleanup folder {folder_id}: {str(e)}")
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Comprehensive PDF Management Backend Tests")
        print("=" * 60)
        
        test_results = {}
        
        # Test 1: Health Check
        test_results["health_check"] = self.test_health_check()
        
        if not test_results["health_check"]:
            print("❌ Backend not accessible, stopping tests")
            return test_results
        
        # Test 2: Folder Operations
        test_results["folder_operations"] = self.test_folder_operations()
        
        # Test 3: File Upload Operations
        test_results["file_upload"] = self.test_file_upload_operations()
        
        # Test 4: File Management Operations
        test_results["file_management"] = self.test_file_management_operations()
        
        # Test 5: File Download Operations
        test_results["file_download"] = self.test_file_download_operations()
        
        # Test 6: Folder Deletion Cascade
        test_results["folder_deletion_cascade"] = self.test_folder_deletion_cascade()
        
        # Test 7: File Deletion
        test_results["file_deletion"] = self.test_file_deletion()
        
        # Cleanup
        self.cleanup()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in test_results.values() if result)
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Backend is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the detailed output above.")
        
        return test_results

def main():
    """Main test execution"""
    try:
        # Check if reportlab is available for PDF creation
        import reportlab
        print("✅ ReportLab available for PDF generation")
    except ImportError:
        print("❌ ReportLab not available. Installing...")
        os.system("pip install reportlab")
        try:
            import reportlab
            print("✅ ReportLab installed successfully")
        except ImportError:
            print("❌ Failed to install ReportLab. Using alternative PDF creation method.")
    
    tester = PDFTestManager()
    results = tester.run_all_tests()
    
    return results

if __name__ == "__main__":
    main()