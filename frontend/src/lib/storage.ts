import { AnalysisData } from '@/types/analysis';

export interface StoredAnalysis {
  id: string;
  timestamp: string;
  filename: string;
  data: AnalysisData;
}

const STORAGE_KEY = 'coin_analysis_history';

export const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

export const saveAnalysis = (filename: string, data: AnalysisData): StoredAnalysis => {
  const stored = getAnalysisHistory();
  
  const newEntry: StoredAnalysis = {
    id: generateId(),
    timestamp: new Date().toISOString(),
    filename,
    data,
  };
  
  stored.unshift(newEntry);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
  
  return newEntry;
};

export const getAnalysisHistory = (): StoredAnalysis[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
};

export const getAnalysisById = (id: string): StoredAnalysis | null => {
  const history = getAnalysisHistory();
  return history.find(entry => entry.id === id) || null;
};

export const deleteAnalysis = (id: string): void => {
  const history = getAnalysisHistory();
  const filtered = history.filter(entry => entry.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
};

export const clearHistory = (): void => {
  localStorage.removeItem(STORAGE_KEY);
};

// Group analyses by date
export const groupAnalysesByDate = (analyses: StoredAnalysis[]): Record<string, StoredAnalysis[]> => {
  return analyses.reduce((groups, analysis) => {
    const date = new Date(analysis.timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(analysis);
    return groups;
  }, {} as Record<string, StoredAnalysis[]>);
};
