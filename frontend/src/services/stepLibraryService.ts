/**
 * Step Library Service — Sprint 10.11
 *
 * CRUD operations for the StepLibraryModule resource.
 * All calls require a valid JWT token in localStorage.
 */
import api from './api';
import type {
  StepLibraryModule,
  StepLibraryModuleCreate,
  StepLibraryModuleUpdate,
} from '../types/stepLibrary.types';

const BASE = '/step-library';

class StepLibraryService {
  /** List all modules owned by the current user. */
  async list(): Promise<StepLibraryModule[]> {
    const response = await api.get<StepLibraryModule[]>(BASE);
    return response.data;
  }

  /** Create a new module. */
  async create(body: StepLibraryModuleCreate): Promise<StepLibraryModule> {
    const response = await api.post<StepLibraryModule>(BASE, body);
    return response.data;
  }

  /** Update an existing module by ID. */
  async update(id: number, body: StepLibraryModuleUpdate): Promise<StepLibraryModule> {
    const response = await api.put<StepLibraryModule>(`${BASE}/${id}`, body);
    return response.data;
  }

  /** Delete a module by ID. */
  async delete(id: number): Promise<void> {
    await api.delete(`${BASE}/${id}`);
  }

  /** Get how many test cases reference this module. */
  async getUsage(id: number): Promise<{ module_id: number; usage_count: number }> {
    const response = await api.get(`${BASE}/${id}/usage`);
    return response.data;
  }

  /** Dry-run: return test cases that would be affected by renaming the module's slug. */
  async renamePreview(
    id: number,
    newName: string,
  ): Promise<{ affected_test_cases: { id: number; name: string }[]; count: number }> {
    const response = await api.get(`${BASE}/${id}/rename-preview`, {
      params: { new_name: newName },
    });
    return response.data;
  }
}

const stepLibraryService = new StepLibraryService();
export default stepLibraryService;
