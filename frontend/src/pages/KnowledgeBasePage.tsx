import React from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Upload, Search } from 'lucide-react';

const mockCategories = [
  { id: 'cat-001', name: 'CRM', color: '#3498db', count: 5 },
  { id: 'cat-002', name: 'Billing', color: '#2ecc71', count: 8 },
  { id: 'cat-003', name: 'Products & Services', color: '#16a085', count: 12 },
  { id: 'cat-004', name: 'Customer Service', color: '#c0392b', count: 6 },
];

const mockDocuments = [
  {
    id: 'doc-001',
    category: 'CRM',
    fileName: 'CRM_User_Guide.pdf',
    size: '2.1 MB',
    uploadedDate: '2025-10-15',
    referencedCount: 47,
  },
  {
    id: 'doc-002',
    category: 'Products & Services',
    fileName: '5G_Product_Catalog.pdf',
    size: '2.4 MB',
    uploadedDate: '2025-10-20',
    referencedCount: 18,
  },
];

export const KnowledgeBasePage: React.FC = () => {
  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
            <p className="text-gray-600 mt-1">Upload and manage documentation</p>
          </div>
          <Button variant="primary">
            <Upload className="w-5 h-5 mr-2" />
            Upload Document
          </Button>
        </div>

        {/* Search Bar */}
        <Card>
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search knowledge base documents..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <Button variant="secondary">Search</Button>
          </div>
        </Card>

        {/* Categories */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Categories</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {mockCategories.map((category) => (
              <Card key={category.id} padding={false}>
                <div className="p-4 flex items-center gap-3">
                  <div
                    className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-xl"
                    style={{ backgroundColor: category.color }}
                  >
                    {category.name[0]}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{category.name}</p>
                    <p className="text-sm text-gray-600">{category.count} documents</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Documents */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Documents</h2>
          <div className="space-y-3">
            {mockDocuments.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="text-4xl">📄</div>
                  <div>
                    <p className="font-medium text-gray-900">{doc.fileName}</p>
                    <p className="text-sm text-gray-600">
                      {doc.category} • {doc.size} • Uploaded {doc.uploadedDate}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Referenced by agents</p>
                    <p className="text-lg font-semibold text-primary">{doc.referencedCount} times</p>
                  </div>
                  <Button variant="secondary" size="sm">View</Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </Layout>
  );
};

