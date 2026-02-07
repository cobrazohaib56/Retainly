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
  raw_total?: number | null;
  subtotal?: number | null;
  tax?: number | null;
  discount?: number | null;
}

export interface ErrorEntry {
  entry_id: string;
  receipt_number: string;
  to_user: string;
  error: string;
  receipt_photo_url: string;
  dataset_coins: number;
  reference_id?: string;
}

export interface NoImageEntry {
  entry_id: string;
  receipt_number: string;
  to_user: string;
  from_merchant?: string;
  dataset_coins: number;
  reference_id?: string;
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
  no_image_count: number;
}

export interface AnalysisData {
  summary: AnalysisSummary;
  exact_match: AnalysisEntry[];
  low_rank: AnalysisEntry[];
  medium_rank: AnalysisEntry[];
  critical_rank: AnalysisEntry[];
  errors: ErrorEntry[];
  no_image: NoImageEntry[];
}

export type RiskCategory = 'exact' | 'low' | 'medium' | 'critical' | 'error' | 'no_image';
