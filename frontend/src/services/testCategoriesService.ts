import api, { apiHelpers } from './api';
import {
  CreateTestCategoryRequest,
  TestCategory,
  TestCategoryListResponse,
  UpdateTestCategoryRequest,
} from '../types/api';

class TestCategoriesService {
  async getAll(): Promise<TestCategory[]> {
    try {
      const response = await api.get<TestCategoryListResponse>('/test-categories');
      return response.data.items || [];
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  async create(data: CreateTestCategoryRequest): Promise<TestCategory> {
    try {
      const response = await api.post<TestCategory>('/test-categories', data);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  async update(id: number, data: UpdateTestCategoryRequest): Promise<TestCategory> {
    try {
      const response = await api.put<TestCategory>(`/test-categories/${id}`, data);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  async delete(id: number): Promise<void> {
    try {
      await api.delete(`/test-categories/${id}`);
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }
}

export default new TestCategoriesService();
