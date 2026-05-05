/**
 * TypeScript types for Step Library — Sprint 10.11
 */

export interface StepLibraryModule {
  id: number;
  user_id: number;
  name: string;
  display_name: string;
  description?: string | null;
  steps: string[];
  parameters?: string[] | null;
  tags?: string[] | null;
  created_at: string;
  updated_at: string;
  usage_count?: number;
}

export interface StepLibraryModuleCreate {
  name: string;
  display_name: string;
  description?: string;
  steps: string[];
  parameters?: string[];
  tags?: string[];
}

export interface StepLibraryModuleUpdate {
  name?: string;
  display_name?: string;
  description?: string;
  steps?: string[];
  parameters?: string[];
  tags?: string[];
}
