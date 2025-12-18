import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Upload, Search, FileText, FolderPlus } from 'lucide-react';
import knowledgeBaseService from '../services/knowledgeBaseService';
import type { KBDocument, KBCategory, KBStatistics } from '../types/api';

export const KnowledgeBasePage: React.FC = () => {
  // Data state
  const [documents, setDocuments] = useState<KBDocument[]>([]);
  const [categories, setCategories] = useState<KBCategory[]>([]);
  const [stats, setStats] = useState<KBStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // UI state
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadData, setUploadData] = useState({
    file: null as File | null,
    name: '',
    description: '',
    category_id: '',
    document_type: 'system_guide' as 'system_guide' | 'product' | 'process' | 'reference',
    tags: '',
  });
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  
  // Document viewer state
  const [viewingDocument, setViewingDocument] = useState<KBDocument | null>(null);
  
  // Edit document modal state
  const [editingDocument, setEditingDocument] = useState<KBDocument | null>(null);
  const [editDocumentData, setEditDocumentData] = useState({
    title: '',
    description: '',
    category_id: 0
  });
  const [updatingDocument, setUpdatingDocument] = useState(false);
  
  // Create category modal state
  const [showCreateCategoryModal, setShowCreateCategoryModal] = useState(false);
  const [newCategoryData, setNewCategoryData] = useState({
    name: '',
    description: '',
    color: '#3B82F6',
    icon: 'folder'
  });
  const [creatingCategory, setCreatingCategory] = useState(false);
  
  // Edit category modal state
  const [editingCategory, setEditingCategory] = useState<KBCategory | null>(null);
  const [editCategoryData, setEditCategoryData] = useState({
    name: '',
    description: '',
    color: '#3B82F6',
    icon: 'folder'
  });
  const [updatingCategory, setUpdatingCategory] = useState(false);

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [docsData, catsData, statsData] = await Promise.all([
        knowledgeBaseService.getAllDocuments(),
        knowledgeBaseService.getAllCategories(),
        knowledgeBaseService.getStats(),
      ]);
      
      setDocuments(docsData);
      setCategories(catsData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load knowledge base');
      console.error('Failed to load KB data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadDocument = () => {
    setShowUploadModal(true);
    setUploadData({
      file: null,
      name: '',
      description: '',
      category_id: '',
      document_type: 'system_guide',
      tags: '',
    });
    setUploadError(null);
  };

  const handleFileSelect = (file: File) => {
    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File size must be less than 10MB');
      return;
    }

    // Check file type
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
    ];
    if (!allowedTypes.includes(file.type)) {
      setUploadError('Only PDF, DOCX, and TXT files are allowed');
      return;
    }

    setUploadData({ ...uploadData, file, name: uploadData.name || file.name });
    setUploadError(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleSubmitUpload = async () => {
    if (!uploadData.file || !uploadData.name || !uploadData.category_id) {
      setUploadError('Please fill in all required fields');
      return;
    }

    setUploading(true);
    setUploadError(null);

    try {
      await knowledgeBaseService.uploadDocument({
        file: uploadData.file,
        name: uploadData.name,
        description: uploadData.description,
        category_id: uploadData.category_id,
        document_type: uploadData.document_type,
        tags: uploadData.tags ? uploadData.tags.split(',').map((t) => t.trim()) : [],
      });

      setShowUploadModal(false);
      alert('Document uploaded successfully!');
      
      // Reload data to show new document
      await loadData();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleCreateCategory = () => {
    setShowCreateCategoryModal(true);
  };

  const handleSaveCategory = async () => {
    if (!newCategoryData.name.trim()) {
      alert('Category name is required');
      return;
    }

    try {
      setCreatingCategory(true);
      await knowledgeBaseService.createCategory({
        name: newCategoryData.name,
        description: newCategoryData.description || undefined,
        color: newCategoryData.color
      });
      
      // Reload categories
      const catsData = await knowledgeBaseService.getAllCategories();
      setCategories(catsData);
      
      // Reset and close modal
      setNewCategoryData({ name: '', description: '', color: '#3B82F6', icon: 'folder' });
      setShowCreateCategoryModal(false);
      alert('Category created successfully!');
    } catch (err) {
      alert(`Failed to create category: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setCreatingCategory(false);
    }
  };

  const handleCloseCategoryModal = () => {
    setShowCreateCategoryModal(false);
    setNewCategoryData({ name: '', description: '', color: '#3B82F6', icon: 'folder' });
  };

  const handleEditCategory = (category: KBCategory) => {
    setEditingCategory(category);
    setEditCategoryData({
      name: category.name,
      description: category.description || '',
      color: category.color || '#3B82F6',
      icon: category.icon || 'folder'
    });
  };

  const handleUpdateCategory = async () => {
    if (!editingCategory) return;
    
    if (!editCategoryData.name.trim()) {
      alert('Category name is required');
      return;
    }

    try {
      setUpdatingCategory(true);
      await knowledgeBaseService.updateCategory(editingCategory.id, {
        name: editCategoryData.name,
        description: editCategoryData.description || undefined,
        color: editCategoryData.color
      });
      
      // Reload categories
      const catsData = await knowledgeBaseService.getAllCategories();
      setCategories(catsData);
      
      // Reset and close modal
      setEditingCategory(null);
      setEditCategoryData({ name: '', description: '', color: '#3B82F6', icon: 'folder' });
      alert('Category updated successfully!');
    } catch (err) {
      alert(`Failed to update category: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setUpdatingCategory(false);
    }
  };

  const handleCloseEditCategoryModal = () => {
    setEditingCategory(null);
    setEditCategoryData({ name: '', description: '', color: '#3B82F6', icon: 'folder' });
  };

  const handleEditDocument = (doc: KBDocument) => {
    setEditingDocument(doc);
    setEditDocumentData({
      title: doc.title,
      description: doc.description || '',
      category_id: doc.category.id
    });
  };

  const handleUpdateDocument = async () => {
    if (!editingDocument) return;
    
    if (!editDocumentData.title.trim()) {
      alert('Document title is required');
      return;
    }

    try {
      setUpdatingDocument(true);
      await knowledgeBaseService.updateDocument(editingDocument.id, {
        title: editDocumentData.title,
        description: editDocumentData.description || undefined,
        category_id: editDocumentData.category_id
      });
      
      // Reload documents
      const docsData = await knowledgeBaseService.getAllDocuments();
      setDocuments(docsData);
      
      // Reset and close modal
      setEditingDocument(null);
      setEditDocumentData({ title: '', description: '', category_id: 0 });
      alert('Document updated successfully!');
    } catch (err) {
      alert(`Failed to update document: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setUpdatingDocument(false);
    }
  };

  const handleCloseEditDocumentModal = () => {
    setEditingDocument(null);
    setEditDocumentData({ title: '', description: '', category_id: 0 });
  };

  const handleViewDocument = async (docId: number) => {
    try {
      const doc = await knowledgeBaseService.getDocumentById(docId.toString());
      setViewingDocument(doc);
    } catch (err) {
      alert(`Failed to load document: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleCloseViewer = () => {
    setViewingDocument(null);
  };

  const handleDownload = async (doc: KBDocument) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
      const token = localStorage.getItem('token'); // Changed from 'access_token' to 'token'
      
      if (!token) {
        alert('Please log in to download documents');
        return;
      }
      
      // Fetch the file from the backend
      const response = await fetch(`${apiUrl}/kb/${doc.id}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Download error:', errorText);
        throw new Error(`Download failed: ${response.status} ${response.statusText}`);
      }
      
      // Get the blob from response
      const blob = await response.blob();
      
      // Create temporary download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.filename;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);
      
    } catch (err) {
      console.error('Download error:', err);
      alert(`Failed to download document: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // Filter documents based on selected category
  const filteredDocuments = documents.filter((doc) => {
    if (selectedCategory === 'all') return true;
    return doc.category.id.toString() === selectedCategory;
  });

  // Further filter by search query if present
  const displayedDocuments = filteredDocuments.filter((doc) => {
    if (!searchQuery) return true;
    return (
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (doc.description && doc.description.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  });

  const getCategoryColor = (category: KBCategory) => {
    // Use the category's color field if available
    return category.color || '#3B82F6'; // Default to blue if no color
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="text-gray-600">Loading knowledge base...</div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Content */}
        {!loading && !error && (
          <>
            {/* Header */}
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
                <p className="text-gray-600 mt-1">
                  {stats?.total_documents || 0} documents • {stats?.total_size_mb?.toFixed(1) || '0'} MB
                </p>
              </div>
              <div className="flex gap-3">
                <Button variant="secondary" onClick={handleCreateCategory}>
                  <FolderPlus className="w-5 h-5 mr-2" />
                  Create Category
                </Button>
                <Button variant="primary" onClick={handleUploadDocument}>
                  <Upload className="w-5 h-5 mr-2" />
                  Upload Document
                </Button>
              </div>
            </div>

        {/* Upload Modal */}
        {showUploadModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-gray-900">Upload Document</h2>
                  <button
                    onClick={() => setShowUploadModal(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>

                {/* Drag & Drop Zone */}
                <div
                  onDrop={handleDrop}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  className={`border-2 border-dashed rounded-lg p-8 text-center ${
                    dragActive
                      ? 'border-primary bg-blue-50'
                      : 'border-gray-300 bg-gray-50'
                  }`}
                >
                  {uploadData.file ? (
                    <div className="space-y-2">
                      <FileText className="w-12 h-12 mx-auto text-green-600" />
                      <p className="font-semibold text-gray-900">{uploadData.file.name}</p>
                      <p className="text-sm text-gray-600">
                        {(uploadData.file.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setUploadData({ ...uploadData, file: null })}
                      >
                        Remove File
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Upload className="w-12 h-12 mx-auto text-gray-400" />
                      <p className="text-gray-700">
                        Drag and drop a file here, or click to select
                      </p>
                      <p className="text-xs text-gray-500">
                        Supported formats: PDF, DOCX, TXT (Max 10MB)
                      </p>
                      <input
                        type="file"
                        accept=".pdf,.docx,.txt"
                        onChange={(e) =>
                          e.target.files && handleFileSelect(e.target.files[0])
                        }
                        className="hidden"
                        id="file-upload"
                      />
                      <label htmlFor="file-upload" className="inline-block">
                        <span className="inline-flex items-center px-4 py-2 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 cursor-pointer transition-colors">
                          Select File
                        </span>
                      </label>
                    </div>
                  )}
                </div>

                {/* Form Fields */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Document Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={uploadData.name}
                      onChange={(e) =>
                        setUploadData({ ...uploadData, name: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                      placeholder="Enter document name"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Description
                    </label>
                    <textarea
                      value={uploadData.description}
                      onChange={(e) =>
                        setUploadData({ ...uploadData, description: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary min-h-[80px]"
                      placeholder="Brief description of the document"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Category <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={uploadData.category_id}
                      onChange={(e) =>
                        setUploadData({ ...uploadData, category_id: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option value="">Select a category</option>
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Document Type
                    </label>
                    <select
                      value={uploadData.document_type}
                      onChange={(e) =>
                        setUploadData({
                          ...uploadData,
                          document_type: e.target.value as any,
                        })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option value="system_guide">System Guide</option>
                      <option value="product">Product</option>
                      <option value="process">Process</option>
                      <option value="reference">Reference</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Tags (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={uploadData.tags}
                      onChange={(e) =>
                        setUploadData({ ...uploadData, tags: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                      placeholder="e.g. billing, user-guide, api"
                    />
                  </div>
                </div>

                {uploadError && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                    {uploadError}
                  </div>
                )}

                <div className="flex gap-3">
                  <Button
                    variant="primary"
                    onClick={handleSubmitUpload}
                    disabled={uploading || !uploadData.file}
                    className="flex-1"
                  >
                    {uploading ? 'Uploading...' : 'Upload Document'}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => setShowUploadModal(false)}
                    disabled={uploading}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Search Bar */}
        <Card>
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search knowledge base documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
        </Card>

        {/* Category Filters */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Filter by Category</h2>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={selectedCategory === 'all' ? 'primary' : 'secondary'}
              onClick={() => setSelectedCategory('all')}
            >
              All Documents ({documents.length})
            </Button>
            {categories.map((category) => {
              const count = documents.filter(d => d.category.id === category.id).length;
              return (
                <Button
                  key={category.id}
                  variant={selectedCategory === category.id.toString() ? 'primary' : 'secondary'}
                  onClick={() => setSelectedCategory(category.id.toString())}
                >
                  {category.name} ({count})
                </Button>
              );
            })}
          </div>
        </div>

        {/* Category Cards */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Categories</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {categories.map((category) => {
              const count = documents.filter(d => d.category.id === category.id).length;
              const color = getCategoryColor(category);
              return (
                <Card key={category.id} padding={false}>
                  <div className="p-4">
                    <button
                      onClick={() => setSelectedCategory(category.id.toString())}
                      className="w-full flex items-center gap-3 text-left hover:bg-gray-50 transition-colors rounded-lg p-2"
                    >
                      <div
                        className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-xl"
                        style={{ backgroundColor: color }}
                      >
                        {category.name[0]}
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900">{category.name}</p>
                        <p className="text-sm text-gray-600">{count} documents</p>
                      </div>
                    </button>
                    <button
                      onClick={() => handleEditCategory(category)}
                      className="mt-2 w-full px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors"
                    >
                      Edit Category
                    </button>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Documents List */}
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              {selectedCategory === 'all'
                ? 'All Documents'
                : `${selectedCategory} Documents`}
            </h2>
            <p className="text-sm text-gray-600">
              Showing {displayedDocuments.length} of {documents.length} documents
            </p>
          </div>
          <div className="space-y-3">
            {displayedDocuments.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                <p>No documents found</p>
                {searchQuery && <p className="text-sm">Try a different search term</p>}
              </div>
            ) : (
              displayedDocuments.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="text-4xl">📄</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-gray-900">{doc.title}</p>
                        <span className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded">
                          #{doc.id}
                        </span>
                        {doc.category && (
                          <span
                            className="text-xs px-2 py-1 text-white rounded"
                            style={{ backgroundColor: getCategoryColor(doc.category) }}
                          >
                            {doc.category.name}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{doc.description || 'No description'}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span>{(doc.file_size / (1024 * 1024)).toFixed(2)} MB</span>
                        <span>•</span>
                        <span>{doc.file_type.toUpperCase()}</span>
                        <span>•</span>
                        <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                        <span>•</span>
                        <span>Referenced {doc.referenced_count} times</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleViewDocument(doc.id)}
                    >
                      View
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleEditDocument(doc)}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleDownload(doc)}
                    >
                      Download
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
          </>
        )}
      </div>

      {/* Document Viewer Modal */}
      {viewingDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    {viewingDocument.title}
                  </h2>
                  <div className="flex items-center gap-3 text-sm text-gray-600">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                      {viewingDocument.category.name}
                    </span>
                    <span>{viewingDocument.filename}</span>
                    <span>•</span>
                    <span>{(viewingDocument.file_size / 1024).toFixed(2)} KB</span>
                    <span>•</span>
                    <span>{new Date(viewingDocument.created_at).toLocaleDateString()}</span>
                  </div>
                  {viewingDocument.description && (
                    <p className="mt-2 text-gray-600">{viewingDocument.description}</p>
                  )}
                </div>
                <button
                  onClick={handleCloseViewer}
                  className="ml-4 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-6">
              <div className="prose max-w-none">
                {viewingDocument.content ? (
                  <pre className="whitespace-pre-wrap font-sans text-gray-700">
                    {viewingDocument.content}
                  </pre>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                    <p>Document content preview not available</p>
                    <p className="text-sm mt-2">The full document is stored at: {viewingDocument.file_path}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-gray-200 bg-gray-50">
              <div className="flex justify-end gap-3">
                <Button variant="secondary" onClick={handleCloseViewer}>
                  Close
                </Button>
                <Button variant="primary" onClick={() => handleDownload(viewingDocument)}>
                  Download
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Category Modal */}
      {showCreateCategoryModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Create New Category</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category Name *
                </label>
                <input
                  type="text"
                  value={newCategoryData.name}
                  onChange={(e) => setNewCategoryData({ ...newCategoryData, name: e.target.value })}
                  placeholder="e.g., Product Documentation"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={newCategoryData.description}
                  onChange={(e) => setNewCategoryData({ ...newCategoryData, description: e.target.value })}
                  placeholder="Brief description of this category"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Color
                </label>
                <div className="flex gap-2 items-center">
                  <input
                    type="color"
                    value={newCategoryData.color}
                    onChange={(e) => setNewCategoryData({ ...newCategoryData, color: e.target.value })}
                    className="h-10 w-20 border border-gray-300 rounded cursor-pointer"
                  />
                  <span className="text-sm text-gray-600">{newCategoryData.color}</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <Button variant="secondary" onClick={handleCloseCategoryModal} disabled={creatingCategory}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSaveCategory} disabled={creatingCategory}>
                {creatingCategory ? 'Creating...' : 'Create Category'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Category Modal */}
      {editingCategory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Edit Category</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category Name *
                </label>
                <input
                  type="text"
                  value={editCategoryData.name}
                  onChange={(e) => setEditCategoryData({ ...editCategoryData, name: e.target.value })}
                  placeholder="e.g., Product Documentation"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={editCategoryData.description}
                  onChange={(e) => setEditCategoryData({ ...editCategoryData, description: e.target.value })}
                  placeholder="Brief description of this category"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Color
                </label>
                <div className="flex gap-2 items-center">
                  <input
                    type="color"
                    value={editCategoryData.color}
                    onChange={(e) => setEditCategoryData({ ...editCategoryData, color: e.target.value })}
                    className="h-10 w-20 border border-gray-300 rounded cursor-pointer"
                  />
                  <span className="text-sm text-gray-600">{editCategoryData.color}</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <Button variant="secondary" onClick={handleCloseEditCategoryModal} disabled={updatingCategory}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleUpdateCategory} disabled={updatingCategory}>
                {updatingCategory ? 'Updating...' : 'Update Category'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Document Modal */}
      {editingDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Edit Document</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  value={editDocumentData.title}
                  onChange={(e) => setEditDocumentData({ ...editDocumentData, title: e.target.value })}
                  placeholder="Document title"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={editDocumentData.description}
                  onChange={(e) => setEditDocumentData({ ...editDocumentData, description: e.target.value })}
                  placeholder="Brief description"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category *
                </label>
                <select
                  value={editDocumentData.category_id}
                  onChange={(e) => setEditDocumentData({ ...editDocumentData, category_id: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="p-3 bg-gray-100 rounded-md">
                <p className="text-sm text-gray-600">
                  <strong>File:</strong> {editingDocument.filename}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Type:</strong> {editingDocument.file_type.toUpperCase()}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Size:</strong> {(editingDocument.file_size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <Button variant="secondary" onClick={handleCloseEditDocumentModal} disabled={updatingDocument}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleUpdateDocument} disabled={updatingDocument}>
                {updatingDocument ? 'Updating...' : 'Update Document'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};