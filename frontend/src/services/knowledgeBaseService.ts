import api, { apiHelpers } from './api';
import {
  KBDocument,
  KBCategory,
  KBDocumentListResponse,
  KBStatistics,
  CreateCategoryRequest,
  SearchDocumentsRequest,
} from '../types/api';

/**
 * Knowledge Base Service
 * Handles all KB-related API operations
 */

class KnowledgeBaseService {
  /**
   * Get all documents
   */
  async getAllDocuments(params?: {
    category_id?: number;
    file_type?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }): Promise<KBDocument[]> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      // Mock data is outdated, return empty array
      console.warn('Mock data for KB is not implemented with new schema');
      return [];
    }

    // Real API call
    try {
      const response = await api.get<KBDocumentListResponse>('/kb', {
        params: {
          category_id: params?.category_id,
          file_type: params?.file_type,
          search: params?.search,
          skip: params?.skip || 0,
          limit: params?.limit || 100
        },
      });
      return response.data.items;
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
      throw new Error('Mock data not supported for KB - please use real API');
    }

    // Real API call
    try {
      const response = await api.get<KBDocument>(`/kb/${id}`);
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
    // Mock data not supported
    if (apiHelpers.useMockData()) {
      throw new Error('Mock data not supported for KB - please use real API');
    }

    // Real API call
    try {
      const formData = new FormData();
      formData.append('file', data.file);
      formData.append('title', data.name);
      formData.append('description', data.description);
      formData.append('category_id', data.category_id);

      const response = await api.post<KBDocument>('/kb/upload', formData, {
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
    // Mock data not supported
    if (apiHelpers.useMockData()) {
      return [];
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
    // Mock data not supported
    if (apiHelpers.useMockData()) {
      throw new Error('Mock data not supported for KB - please use real API');
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
    // Mock data not supported
    if (apiHelpers.useMockData()) {
      throw new Error('Mock data not supported for KB - please use real API');
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
   * Update category
   */
  async updateCategory(id: number, data: Partial<CreateCategoryRequest>): Promise<KBCategory> {
    // Mock data not supported
    if (apiHelpers.useMockData()) {
      throw new Error('Mock data not supported for KB - please use real API');
    }

    // Real API call
    try {
      const response = await api.put<KBCategory>(`/kb/categories/${id}`, data);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Update document
   */
  async updateDocument(id: number, data: {
    title?: string;
    description?: string;
    category_id?: number;
  }): Promise<KBDocument> {
    // Mock data not supported
    if (apiHelpers.useMockData()) {
      throw new Error('Mock data not supported for KB - please use real API');
    }

    // Real API call
    try {
      const response = await api.put<KBDocument>(`/kb/${id}`, data);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Search documents
   */
  async searchDocuments(params: SearchDocumentsRequest): Promise<KBDocument[]> {
    // Mock data not supported
    if (apiHelpers.useMockData()) {
      return [];
    }

    // Real API call
    try {
      const response = await api.get<KBDocumentListResponse>('/kb', {
        params,
      });
      return response.data.items;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Delete document
   */
  async deleteDocument(id: string): Promise<void> {
    // Mock data not supported
    if (apiHelpers.useMockData()) {
      throw new Error('Mock data not supported for KB - please use real API');
    }

    // Real API call
    try {
      await api.delete(`/kb/${id}`);
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get KB statistics
   */
  async getStats(): Promise<KBStatistics> {
    // Mock data not supported
    if (apiHelpers.useMockData()) {
      return {
        total_documents: 0,
        total_size_bytes: 0,
        total_size_mb: 0,
        by_category: {},
        by_file_type: {},
      };
    }

    // Real API call
    try {
      const response = await api.get<KBStatistics>('/kb/stats');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }
}

export default new KnowledgeBaseService();

