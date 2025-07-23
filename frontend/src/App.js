import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [folders, setFolders] = useState([]);
  const [files, setFiles] = useState([]);
  const [currentFolder, setCurrentFolder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showNewFolderModal, setShowNewFolderModal] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [contextMenu, setContextMenu] = useState(null);
  const [draggedItem, setDraggedItem] = useState(null);

  useEffect(() => {
    fetchFolders();
    fetchFiles();
  }, []);

  const fetchFolders = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/folders`);
      const data = await response.json();
      setFolders(data);
    } catch (error) {
      console.error('Error fetching folders:', error);
    }
  };

  const fetchFiles = async (folderId = null) => {
    try {
      const url = folderId ? 
        `${API_BASE_URL}/api/files?folder_id=${folderId}` : 
        `${API_BASE_URL}/api/files`;
      const response = await fetch(url);
      const data = await response.json();
      setFiles(data);
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  };

  const createFolder = async () => {
    if (!newFolderName.trim()) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/folders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newFolderName,
          parent_id: currentFolder
        }),
      });
      
      if (response.ok) {
        setNewFolderName('');
        setShowNewFolderModal(false);
        fetchFolders();
      }
    } catch (error) {
      console.error('Error creating folder:', error);
    } finally {
      setLoading(false);
    }
  };

  const uploadFile = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      alert('Please select a PDF file');
      return;
    }

    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('file', file);
      if (currentFolder) {
        formData.append('folder_id', currentFolder);
      }

      const response = await fetch(`${API_BASE_URL}/api/files/upload`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        fetchFiles(currentFolder);
        event.target.value = ''; // Reset file input
      } else {
        const error = await response.json();
        alert(error.detail || 'Upload failed');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const renameItem = async (id, newName, isFolder = false) => {
    try {
      const endpoint = isFolder ? 'folders' : 'files';
      const body = isFolder ? { name: newName } : { name: newName };
      
      const response = await fetch(`${API_BASE_URL}/api/${endpoint}/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        if (isFolder) {
          fetchFolders();
        } else {
          fetchFiles(currentFolder);
        }
      }
    } catch (error) {
      console.error('Error renaming item:', error);
    }
  };

  const deleteItem = async (id, isFolder = false) => {
    if (!window.confirm(`Are you sure you want to delete this ${isFolder ? 'folder' : 'file'}?`)) {
      return;
    }

    try {
      const endpoint = isFolder ? 'folders' : 'files';
      const response = await fetch(`${API_BASE_URL}/api/${endpoint}/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        if (isFolder) {
          fetchFolders();
        } else {
          fetchFiles(currentFolder);
        }
      }
    } catch (error) {
      console.error('Error deleting item:', error);
    }
  };

  const moveFile = async (fileId, targetFolderId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/files/${fileId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          folder_id: targetFolderId
        }),
      });

      if (response.ok) {
        fetchFiles(currentFolder);
      }
    } catch (error) {
      console.error('Error moving file:', error);
    }
  };

  const downloadFile = async (fileId, fileName) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/files/${fileId}/download`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Error downloading file:', error);
    }
  };

  const handleContextMenu = (event, item, isFolder = false) => {
    event.preventDefault();
    setContextMenu({
      x: event.clientX,
      y: event.clientY,
      item,
      isFolder
    });
  };

  const handleDragStart = (event, item, isFolder = false) => {
    setDraggedItem({ ...item, isFolder });
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleDrop = (event, targetFolderId) => {
    event.preventDefault();
    if (draggedItem && !draggedItem.isFolder) {
      moveFile(draggedItem.id, targetFolderId);
    }
    setDraggedItem(null);
  };

  const getCurrentFolderFiles = files.filter(file => file.folder_id === currentFolder);
  const getCurrentFolderSubfolders = folders.filter(folder => folder.parent_id === currentFolder);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">Institute PDF Manager</h1>
            <div className="flex space-x-4">
              <button
                onClick={() => setShowNewFolderModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
              >
                New Folder
              </button>
              <label className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors cursor-pointer">
                Upload PDF
                <input
                  type="file"
                  accept=".pdf"
                  onChange={uploadFile}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb */}
        <nav className="mb-6">
          <button
            onClick={() => {
              setCurrentFolder(null);
              fetchFiles();
            }}
            className="text-blue-600 hover:text-blue-800"
          >
            Root
          </button>
          {currentFolder && (
            <span className="text-gray-500">
              {' / '}
              {folders.find(f => f.id === currentFolder)?.name}
            </span>
          )}
        </nav>

        {/* Loading Indicator */}
        {loading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-4 rounded-lg">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          </div>
        )}

        {/* File/Folder Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
          {/* Folders */}
          {getCurrentFolderSubfolders.map((folder) => (
            <div
              key={folder.id}
              className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow cursor-pointer"
              onDoubleClick={() => {
                setCurrentFolder(folder.id);
                fetchFiles(folder.id);
              }}
              onContextMenu={(e) => handleContextMenu(e, folder, true)}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, folder.id)}
              draggable
              onDragStart={(e) => handleDragStart(e, folder, true)}
            >
              <div className="flex flex-col items-center">
                <svg className="w-12 h-12 text-blue-500 mb-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                </svg>
                <span className="text-sm font-medium text-gray-900 text-center break-words">
                  {folder.name}
                </span>
              </div>
            </div>
          ))}

          {/* Files */}
          {getCurrentFolderFiles.map((file) => (
            <div
              key={file.id}
              className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow cursor-pointer"
              onDoubleClick={() => downloadFile(file.id, file.name)}
              onContextMenu={(e) => handleContextMenu(e, file, false)}
              draggable
              onDragStart={(e) => handleDragStart(e, file, false)}
            >
              <div className="flex flex-col items-center">
                <svg className="w-12 h-12 text-red-500 mb-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                </svg>
                <span className="text-sm font-medium text-gray-900 text-center break-words">
                  {file.name}
                </span>
                <span className="text-xs text-gray-500 mt-1">
                  {(file.size / 1024).toFixed(1)} KB
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {getCurrentFolderSubfolders.length === 0 && getCurrentFolderFiles.length === 0 && (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No files or folders</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a folder or uploading a PDF.</p>
          </div>
        )}
      </div>

      {/* New Folder Modal */}
      {showNewFolderModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-medium mb-4">Create New Folder</h3>
            <input
              type="text"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="Folder name"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyPress={(e) => e.key === 'Enter' && createFolder()}
            />
            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={() => {
                  setShowNewFolderModal(false);
                  setNewFolderName('');
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={createFolder}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Context Menu */}
      {contextMenu && (
        <div
          className="fixed bg-white border border-gray-200 rounded-md shadow-lg py-1 z-50"
          style={{ left: contextMenu.x, top: contextMenu.y }}
        >
          <button
            onClick={() => {
              const newName = prompt('Enter new name:', contextMenu.item.name);
              if (newName) {
                renameItem(contextMenu.item.id, newName, contextMenu.isFolder);
              }
              setContextMenu(null);
            }}
            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
          >
            Rename
          </button>
          {!contextMenu.isFolder && (
            <button
              onClick={() => {
                downloadFile(contextMenu.item.id, contextMenu.item.name);
                setContextMenu(null);
              }}
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
            >
              Download
            </button>
          )}
          <button
            onClick={() => {
              deleteItem(contextMenu.item.id, contextMenu.isFolder);
              setContextMenu(null);
            }}
            className="block px-4 py-2 text-sm text-red-600 hover:bg-gray-100 w-full text-left"
          >
            Delete
          </button>
        </div>
      )}

      {/* Click outside to close context menu */}
      {contextMenu && (
        <div
          className="fixed inset-0"
          onClick={() => setContextMenu(null)}
        ></div>
      )}
    </div>
  );
}

export default App;