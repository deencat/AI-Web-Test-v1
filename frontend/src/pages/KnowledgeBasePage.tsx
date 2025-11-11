import React, { useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Upload, Search, FileText, FolderPlus } from 'lucide-react';
import { mockKBDocuments, mockKBCategories, mockKBStats } from '../mock/knowledgeBase';

export const KnowledgeBasePage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const handleUploadDocument = () => {
    alert('Upload Document - This will open a modal to upload a new document');
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

