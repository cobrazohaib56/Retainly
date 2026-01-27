// const API_BASE_URL = 'http://localhost:8000/api/v1';
const API_BASE_URL = 'http://74.162.89.220:8000/api/v1';


// Types matching backend schemas
export interface AnalysisEntry {
  entry_id: string;
  receipt_number: string;
  to_user: string;
  from_merchant?: string;
  dataset_coins: number;
  extracted_family_coins: number | null;
  difference: number | null;
  category: string;
  receipt_photo_url: string;
  image_path?: string;
  gemini_raw_response?: string;
}

export interface ErrorEntry {
  entry_id: string;
  receipt_number: string;
  to_user: string;
  error: string;
  receipt_photo_url: string;
  dataset_coins: number;
}

export interface AnalysisSummary {
  total_entries: number;
  processed: number;
  errors: number;
  exact_match_count: number;
  low_rank_count: number;
  medium_rank_count: number;
  critical_rank_count: number;
  error_count: number;
}

export interface AnalysisData {
  summary: AnalysisSummary;
  exact_match: AnalysisEntry[];
  low_rank: AnalysisEntry[];
  medium_rank: AnalysisEntry[];
  critical_rank: AnalysisEntry[];
  errors: ErrorEntry[];
}

export interface AnalysisResponse {
  id: string;
  filename: string;
  timestamp: string;
  data: AnalysisData;
  status: 'processing' | 'completed' | 'failed';
  progress?: number;
}

export interface HistoryResponse {
  analyses: AnalysisResponse[];
  total: number;
}

export interface CategoryResponse {
  analysis_id: string;
  category: string;
  entries: (AnalysisEntry | ErrorEntry)[];
  count: number;
}

/**
 * Check if backend is healthy
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Upload a JSON file to start processing
 */
export async function uploadFile(file: File): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to upload file' }));
    throw new Error(error.detail || 'Failed to upload file');
  }

  return await response.json();
}

/**
 * Get processing status of an analysis
 */
export async function getStatus(analysisId: string): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/upload/status/${analysisId}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get status' }));
    throw new Error(error.detail || 'Failed to get status');
  }

  return await response.json();
}

/**
 * Poll for processing status until completion
 */
export async function pollStatus(
  analysisId: string,
  onProgress?: (progress: number) => void,
  interval: number = 2000
): Promise<AnalysisResponse> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await getStatus(analysisId);

        if (onProgress && status.progress !== undefined) {
          onProgress(status.progress);
        }

        if (status.status === 'completed') {
          resolve(status);
          return;
        }

        if (status.status === 'failed') {
          reject(new Error('Processing failed'));
          return;
        }

        // Continue polling
        setTimeout(poll, interval);
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
}

/**
 * Get analysis by ID
 */
export async function getAnalysis(analysisId: string): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Analysis not found' }));
    throw new Error(error.detail || 'Analysis not found');
  }

  return await response.json();
}

/**
 * Get category entries
 */
export async function getCategoryEntries(
  analysisId: string,
  category: 'exact' | 'low' | 'medium' | 'critical' | 'error'
): Promise<CategoryResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}/category/${category}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get category entries' }));
    throw new Error(error.detail || 'Failed to get category entries');
  }

  return await response.json();
}

/**
 * Get analysis history
 */
export async function getHistory(skip: number = 0, limit: number = 100): Promise<HistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/history?skip=${skip}&limit=${limit}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get history' }));
    throw new Error(error.detail || 'Failed to get history');
  }

  return await response.json();
}

/**
 * Delete an analysis
 */
export async function deleteAnalysis(analysisId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to delete analysis' }));
    throw new Error(error.detail || 'Failed to delete analysis');
  }
}

/**
 * Get image URL for a receipt
 */
export function getImageUrl(receiptNumber: string): string {
  return `${API_BASE_URL}/images/${receiptNumber}`;
}
