import api from './api';

export interface ProductSummary {
  id: string;
  title: string;
  title_zh?: string | null;
  locale?: string | null;
  pilot?: boolean;
  program_slug?: string | null;
  wiki_profile?: string | null;
}

export interface ProductDetail extends ProductSummary {
  default_urls: Record<string, string>;
  reqiq_project_id: string;
}

export interface ProductWorkspaceStatus {
  source_count: number;
  wiki_ready: boolean;
  wiki_stale: boolean;
  wiki_compiled_at?: string | null;
  requirement_count: number;
  draft_requirement_count: number;
  readiness_score?: number | null;
}

export interface AllowedFormats {
  extensions: string[];
  source_type_hints: Record<string, string>;
}

const ACCEPT_EXT = '.pdf,.doc,.docx,.txt,.md,.ppt,.pptx,.png,.jpg,.jpeg,.gif,.webp,.json,.yaml,.yml,.csv,.xlsx,.xls,.xml,.html,.htm';

export function uploadAcceptAttribute(): string {
  return ACCEPT_EXT;
}

export async function listProducts(): Promise<{ items: ProductSummary[]; total: number }> {
  const { data } = await api.get('/products');
  return data;
}

export async function getProduct(productId: string): Promise<ProductDetail> {
  const { data } = await api.get(`/products/${productId}`);
  return data;
}

export async function getProductStatus(productId: string): Promise<{
  product: ProductDetail;
  status: ProductWorkspaceStatus;
}> {
  const { data } = await api.get(`/products/${productId}/status`);
  return data;
}

export async function getAllowedFormats(): Promise<AllowedFormats> {
  const { data } = await api.get('/products/formats');
  return data;
}

export async function uploadProductDocuments(productId: string, files: File[]): Promise<unknown> {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  const { data } = await api.post(`/products/${productId}/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function compileProductWiki(productId: string): Promise<unknown> {
  const { data } = await api.post(`/products/${productId}/compile-wiki`);
  return data;
}

export async function generateTestsFromWiki(productId: string): Promise<{
  created: number;
  dedupe_dropped: number;
  batch_id?: string;
  message: string;
}> {
  const { data } = await api.post(`/products/${productId}/generate-tests`);
  return data;
}

export async function syncProductProgram(productId: string): Promise<{
  initiatives_synced: number;
  journeys_upserted: number;
  journeys_retired: number;
  tests_retired: number;
}> {
  const { data } = await api.post(`/products/${productId}/sync-program`);
  return data;
}

export async function runOvernight(productId: string): Promise<{
  job_id: string;
  status: string;
  journey_count: number;
}> {
  const { data } = await api.post(`/products/${productId}/run-overnight`);
  return data;
}

export async function getProductWiki(productId: string): Promise<{ markdown?: string; content?: string; wikiStale?: boolean }> {
  const product = await getProduct(productId);
  const { data } = await api.get(`/requirements/projects/${product.reqiq_project_id}/wiki`);
  return data;
}

export async function saveProductWiki(productId: string, markdown: string): Promise<unknown> {
  const product = await getProduct(productId);
  const { data } = await api.patch(`/requirements/projects/${product.reqiq_project_id}/wiki`, {
    markdown,
    indexInRag: false,
  });
  return data;
}

export async function listProductRequirements(productId: string): Promise<unknown[]> {
  const product = await getProduct(productId);
  const { data } = await api.get(`/requirements/${product.reqiq_project_id}/requirements`);
  if (Array.isArray(data)) return data;
  return data.items || data.requirements || [];
}

export async function listProductSources(productId: string): Promise<unknown[]> {
  const product = await getProduct(productId);
  const { data } = await api.get(`/requirements/${product.reqiq_project_id}/sources`);
  if (Array.isArray(data)) return data;
  return data.items || data.sources || [];
}
