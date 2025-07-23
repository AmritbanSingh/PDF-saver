from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import base64
from datetime import datetime
import mimetypes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = MongoClient(os.environ.get('MONGO_URL'))
db = client.pdf_management
folders_collection = db.folders
files_collection = db.files

# Pydantic models
class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None

class FolderUpdate(BaseModel):
    name: str

class FileUpdate(BaseModel):
    name: Optional[str] = None
    folder_id: Optional[str] = None

class Folder(BaseModel):
    id: str
    name: str
    parent_id: Optional[str] = None
    created_at: datetime

class FileInfo(BaseModel):
    id: str
    name: str
    folder_id: Optional[str] = None
    size: int
    uploaded_at: datetime

# Folder endpoints
@app.get("/api/folders", response_model=List[Folder])
async def get_folders():
    """Get all folders"""
    folders = []
    for folder in folders_collection.find():
        folders.append(Folder(
            id=folder["_id"],
            name=folder["name"],
            parent_id=folder.get("parent_id"),
            created_at=folder["created_at"]
        ))
    return folders

@app.post("/api/folders", response_model=Folder)
async def create_folder(folder: FolderCreate):
    """Create a new folder"""
    folder_id = str(uuid.uuid4())
    folder_data = {
        "_id": folder_id,
        "name": folder.name,
        "parent_id": folder.parent_id,
        "created_at": datetime.now()
    }
    folders_collection.insert_one(folder_data)
    return Folder(
        id=folder_id,
        name=folder.name,
        parent_id=folder.parent_id,
        created_at=folder_data["created_at"]
    )

@app.put("/api/folders/{folder_id}", response_model=Folder)
async def update_folder(folder_id: str, folder_update: FolderUpdate):
    """Rename a folder"""
    result = folders_collection.update_one(
        {"_id": folder_id},
        {"$set": {"name": folder_update.name}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    folder = folders_collection.find_one({"_id": folder_id})
    return Folder(
        id=folder["_id"],
        name=folder["name"],
        parent_id=folder.get("parent_id"),
        created_at=folder["created_at"]
    )

@app.delete("/api/folders/{folder_id}")
async def delete_folder(folder_id: str):
    """Delete a folder and all its contents"""
    # Delete all files in this folder
    files_collection.delete_many({"folder_id": folder_id})
    
    # Delete all subfolders (simple approach - could be made recursive)
    folders_collection.delete_many({"parent_id": folder_id})
    
    # Delete the folder itself
    result = folders_collection.delete_one({"_id": folder_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    return {"message": "Folder deleted successfully"}

# File endpoints
@app.get("/api/files", response_model=List[FileInfo])
async def get_files(folder_id: Optional[str] = None):
    """Get all files, optionally filtered by folder"""
    query = {}
    if folder_id is not None:
        query["folder_id"] = folder_id
    
    files = []
    for file_doc in files_collection.find(query, {"content": 0}):  # Exclude content for listing
        files.append(FileInfo(
            id=file_doc["_id"],
            name=file_doc["name"],
            folder_id=file_doc.get("folder_id"),
            size=file_doc["size"],
            uploaded_at=file_doc["uploaded_at"]
        ))
    return files

@app.post("/api/files/upload", response_model=FileInfo)
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(None)
):
    """Upload a PDF file"""
    # Check if it's a PDF
    if not file.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Read file content
    content = await file.read()
    
    # Convert to base64
    base64_content = base64.b64encode(content).decode('utf-8')
    
    file_id = str(uuid.uuid4())
    file_data = {
        "_id": file_id,
        "name": file.filename,
        "folder_id": folder_id,
        "content": base64_content,
        "size": len(content),
        "uploaded_at": datetime.now()
    }
    
    files_collection.insert_one(file_data)
    
    return FileInfo(
        id=file_id,
        name=file.filename,
        folder_id=folder_id,
        size=len(content),
        uploaded_at=file_data["uploaded_at"]
    )

@app.put("/api/files/{file_id}", response_model=FileInfo)
async def update_file(file_id: str, file_update: FileUpdate):
    """Update file (rename or move to different folder)"""
    update_data = {}
    if file_update.name:
        update_data["name"] = file_update.name
    if file_update.folder_id is not None:
        update_data["folder_id"] = file_update.folder_id
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    result = files_collection.update_one(
        {"_id": file_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_doc = files_collection.find_one({"_id": file_id}, {"content": 0})
    return FileInfo(
        id=file_doc["_id"],
        name=file_doc["name"],
        folder_id=file_doc.get("folder_id"),
        size=file_doc["size"],
        uploaded_at=file_doc["uploaded_at"]
    )

@app.get("/api/files/{file_id}/download")
async def download_file(file_id: str):
    """Download a PDF file"""
    file_doc = files_collection.find_one({"_id": file_id})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Decode base64 content
    content = base64.b64decode(file_doc["content"])
    
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={file_doc['name']}"}
    )

@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a file"""
    result = files_collection.delete_one({"_id": file_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"message": "File deleted successfully"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)