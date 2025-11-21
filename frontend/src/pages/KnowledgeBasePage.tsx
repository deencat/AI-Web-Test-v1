import React, { useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Upload, Search, FileText, FolderPlus } from 'lucide-react';
import { mockKBDocuments, mockKBCategories, mockKBStats } from '../mock/knowledgeBase';
import knowledgeBaseService from '../services/knowledgeBaseService';

export const KnowledgeBasePage: React.FC = () => {
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
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleCreateCategory = () => {
    alert('Create Category - This will open a modal to create a new category');
  };

  const handleViewDocument = (docId: string, docName: string) => {
    alert(`View document: ${docName} (ID: ${docId})`);
  };

  // Filter documents based on selected category
  const filteredDocuments = mockKBDocuments.filter((doc) => {
    if (selectedCategory === 'all') return true;
    return doc.category === selectedCategory;
  });

  // Further filter by search query if present
  const displayedDocuments = filteredDocuments.filter((doc) => {
    if (!searchQuery) return true;
    return (
      doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  });

  const getCategoryColor = (category: string) => {
    const cat = mockKBCategories.find((c) => c.name === category);
    return cat?.color || 'gray';
  };

  const colorMap: Record<string, string> = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
    gray: 'bg-gray-500',
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
            <p className="text-gray-600 mt-1">
              {mockKBStats.total_documents} documents • {mockKBStats.total_size}
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
                      {mockKBCategories.map((cat) => (
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
              All Documents ({mockKBDocuments.length})
            </Button>
            {mockKBCategories.map((category) => (
              <Button
                key={category.id}
                variant={selectedCategory === category.name ? 'primary' : 'secondary'}
                onClick={() => setSelectedCategory(category.name)}
              >
                {category.name} ({category.count})
              </Button>
            ))}
          </div>
        </div>

        {/* Category Cards */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Categories</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {mockKBCategories.map((category) => (
              <Card key={category.id} padding={false}>
                <button
                  onClick={() => setSelectedCategory(category.name)}
                  className="w-full p-4 flex items-center gap-3 text-left hover:bg-gray-50 transition-colors rounded-lg"
                >
                  <div
                    className={`w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-xl ${
                      colorMap[category.color || 'blue']
                    }`}
                  >
                    {category.name[0]}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{category.name}</p>
                    <p className="text-sm text-gray-600">{category.count} documents</p>
                  </div>
                </button>
              </Card>
            ))}
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
              Showing {displayedDocuments.length} of {mockKBDocuments.length} documents
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
                        <p className="font-semibold text-gray-900">{doc.name}</p>
                        <span className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded">
                          {doc.id}
                        </span>
                        <span
                          className={`text-xs px-2 py-1 text-white rounded ${
                            colorMap[getCategoryColor(doc.category)]
                          }`}
                        >
                          {doc.category}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{doc.description}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span>{doc.file_size}</span>
                        <span>•</span>
                        <span>Uploaded by {doc.uploaded_by}</span>
                        <span>•</span>
                        <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {doc.tags.map((tag, index) => (
                          <span
                            key={index}
                            className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleViewDocument(doc.id, doc.name)}
                    >
                      View
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </Layout>
  );
};

