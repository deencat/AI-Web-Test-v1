import api, { apiHelpers } from './api';
import {
  KBDocument,
  KBCategory,
  CreateCategoryRequest,
  SearchDocumentsRequest,
  PaginatedResponse,
} from '../types/api';
import { mockKBDocuments, mockKBCategories } from '../mock/knowledgeBase';

/**
 * Knowledge Base Service
 * Handles all KB-related API operations
 */

class KnowledgeBaseService {
  /**
   * Get all documents
   */
  async getAllDocuments(params?: {
    category_id?: string;
    document_type?: string;
    page?: number;
    per_page?: number;
  }): Promise<KBDocument[]> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      let filtered = [...mockKBDocuments];

      // Apply filters
      if (params?.category_id) {
        const category = mockKBCategories.find((c) => c.id === params.category_id);
        if (category) {
          filtered = filtered.filter((doc) => doc.category === category.name);
        }
      }
      if (params?.document_type) {
        filtered = filtered.filter((doc) => doc.document_type === params.document_type);
      }

      return filtered;
    }

    // Real API call
    try {
      const response = await api.get<PaginatedResponse<KBDocument>>('/kb/documents', {
        params,
      });
      return response.data.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get document by ID
   */
  async getDocumentById(id: string): Promise<KBDocument> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const doc = mockKBDocuments.find((d) => d.id === id);
      if (!doc) {
        throw new Error('Document not found');
      }
      return doc;
    }

    // Real API call
    try {
      const response = await api.get<KBDocument>(`/kb/documents/${id}`);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Upload document
   */
  async uploadDocument(data: {
    file: File;
    name: string;
    description: string;
    category_id: string;
    document_type: 'system_guide' | 'product' | 'process' | 'reference';
    tags?: string[];
  }): Promise<KBDocument> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const category = mockKBCategories.find((c) => c.id === data.category_id);
      
      const newDoc: KBDocument = {
        id: `KB-${String(mockKBDocuments.length + 1).padStart(3, '0')}`,
        name: data.name,
        description: data.description,
        category: category?.name || 'Uncategorized',
        document_type: data.document_type,
        file_size: `${(data.file.size / (1024 * 1024)).toFixed(1)} MB`,
        uploaded_by: 'Current User',
        uploaded_at: new Date().toISOString(),
        tags: data.tags || [],
        referenced_count: 0,
      };

      mockKBDocuments.push(newDoc);
      
      // Update category count
      if (category) {
        category.count = (category.count || 0) + 1;
      }

      return newDoc;
    }

    // Real API call
    try {
      const formData = new FormData();
      formData.append('file', data.file);
      formData.append('name', data.name);
      formData.append('description', data.description);
      formData.append('category_id', data.category_id);
      formData.append('document_type', data.document_type);
      if (data.tags) {
        formData.append('tags', JSON.stringify(data.tags));
      }

      const response = await api.post<KBDocument>('/kb/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get all categories
   */
  async getAllCategories(): Promise<KBCategory[]> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      return [...mockKBCategories];
    }

    // Real API call
    try {
      const response = await api.get<KBCategory[]>('/kb/categories');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get category by ID
   */
  async getCategoryById(id: string): Promise<KBCategory> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const category = mockKBCategories.find((c) => c.id === id);
      if (!category) {
        throw new Error('Category not found');
      }
      return category;
    }

    // Real API call
    try {
      const response = await api.get<KBCategory>(`/kb/categories/${id}`);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Create category
   */
  async createCategory(data: CreateCategoryRequest): Promise<KBCategory> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const newCategory: KBCategory = {
        id: String(mockKBCategories.length + 1),
        name: data.name,
        count: 0,
        ...(data.color && { color: data.color }),
        ...(data.description && { description: data.description }),
      };

      mockKBCategories.push(newCategory);
      return newCategory;
    }

    // Real API call
    try {
      const response = await api.post<KBCategory>('/kb/categories', data);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Search documents
   */
  async searchDocuments(params: SearchDocumentsRequest): Promise<KBDocument[]> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      let results = [...mockKBDocuments];

      // Search in name and description
      if (params.query) {
        const query = params.query.toLowerCase();
        results = results.filter(
          (doc) =>
            doc.name.toLowerCase().includes(query) ||
            doc.description.toLowerCase().includes(query) ||
            doc.tags.some((tag) => tag.toLowerCase().includes(query))
        );
      }

      // Filter by category
      if (params.category_id) {
        const category = mockKBCategories.find((c) => c.id === params.category_id);
        if (category) {
          results = results.filter((doc) => doc.category === category.name);
        }
      }

      // Filter by document type
      if (params.document_type) {
        results = results.filter((doc) => doc.document_type === params.document_type);
      }

      // Filter by tags
      if (params.tags && params.tags.length > 0) {
        results = results.filter((doc) =>
          params.tags!.some((tag) => doc.tags.includes(tag))
        );
      }

      return results;
    }

    // Real API call
    try {
      const response = await api.get<PaginatedResponse<KBDocument>>('/kb/documents/search', {
        params,
      });
      return response.data.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Delete document
   */
  async deleteDocument(id: string): Promise<void> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const docIndex = mockKBDocuments.findIndex((d) => d.id === id);
      if (docIndex === -1) {
        throw new Error('Document not found');
      }

      const doc = mockKBDocuments[docIndex];
      const category = mockKBCategories.find((c) => c.name === doc.category);
      
      // Remove document
      mockKBDocuments.splice(docIndex, 1);

      // Update category count
      if (category && category.count > 0) {
        category.count -= 1;
      }

      return;
    }

    // Real API call
    try {
      await api.delete(`/kb/documents/${id}`);
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get KB statistics
   */
  async getStats(): Promise<{
    total_documents: number;
    total_size: string;
    categories_count: number;
  }> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      return {
        total_documents: mockKBDocuments.length,
        total_size: '38.8 MB',
        categories_count: mockKBCategories.length,
      };
    }

    // Real API call
    try {
      const response = await api.get('/kb/stats');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }
}

export default new KnowledgeBaseService();

