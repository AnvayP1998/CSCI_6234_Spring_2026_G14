const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export interface Asset {
  asset_id: string;
  filename: string | null;
  modality: string;
  created_at: string;
  processing_status: string;
  chunks_indexed: number;
}

export interface SearchHit {
  asset_id: string;
  chunk_index: number;
  text: string;
  score: number;
}

export interface SearchResult {
  query: string;
  hits: SearchHit[];
}

export interface Evidence {
  evidence_id: string;
  asset_id: string;
  location: string;
  snippet: string;
}

export interface TaskResult {
  request_id: string;
  result_id: string;
  asset_id: string;
  task_type: string;
  query: string | null;
  answer: string;
  confidence: number;
  evidence: Evidence[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T | null> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  listAssets: () => request<Asset[]>("/api/assets"),

  uploadAsset: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<Asset>("/api/assets/upload", { method: "POST", body: fd });
  },

  processAsset: (id: string) =>
    request(`/api/assets/${id}/process`, { method: "POST" }),

  embedAsset: (id: string) =>
    request(`/api/assets/${id}/embed`, { method: "POST" }),

  search: (query: string, assetId?: string) =>
    request<SearchResult>("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: 6, asset_id: assetId ?? null }),
    }),

  analyze: (assetId: string, taskType: string, query?: string) =>
    request<{ request_id: string }>("/api/tasks/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ asset_id: assetId, task_type: taskType, query: query ?? null }),
    }),

  getTaskResult: (requestId: string) =>
    request<TaskResult>(`/api/tasks/${requestId}/result`),

  deleteAsset: (id: string) =>
    request(`/api/assets/${id}`, { method: "DELETE" }),
};
