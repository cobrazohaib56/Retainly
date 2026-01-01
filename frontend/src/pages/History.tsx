import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getHistory, deleteAnalysis as deleteAnalysisAPI, AnalysisResponse } from '@/lib/api';
import { History as HistoryIcon, FileJson, Trash2, Clock, CheckCircle2, AlertTriangle, AlertOctagon, XCircle, Calendar, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';

// Group analyses by date
const groupAnalysesByDate = (analyses: AnalysisResponse[]): Record<string, AnalysisResponse[]> => {
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
  }, {} as Record<string, AnalysisResponse[]>);
};

const History = () => {
  const [analyses, setAnalyses] = useState<AnalysisResponse[]>([]);
  const [groupedAnalyses, setGroupedAnalyses] = useState<Record<string, AnalysisResponse[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await getHistory();
        setAnalyses(data.analyses);
        setGroupedAnalyses(groupAnalysesByDate(data.analyses));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load history');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (confirm('Are you sure you want to delete this analysis?')) {
      try {
        await deleteAnalysisAPI(id);
        // Refresh history
        const data = await getHistory();
        setAnalyses(data.analyses);
        setGroupedAnalyses(groupAnalysesByDate(data.analyses));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete analysis');
      }
    }
  };

  const handleClearAll = () => {
    if (confirm('Are you sure you want to delete ALL analysis history? This cannot be undone.')) {
      // Delete all analyses one by one
      Promise.all(analyses.map(a => deleteAnalysisAPI(a.id)))
        .then(() => {
      setAnalyses([]);
      setGroupedAnalyses({});
        })
        .catch((err) => {
          setError(err instanceof Error ? err.message : 'Failed to clear history');
        });
    }
  };

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Loading history...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <HistoryIcon className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-foreground mb-2">Error Loading History</h2>
        <p className="text-muted-foreground mb-6">{error}</p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
        >
          Go Home
        </Link>
      </div>
    );
  }

  if (analyses.length === 0) {
    return (
      <div className="text-center py-20 animate-fade-in">
        <HistoryIcon className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-foreground mb-2">No Analysis History</h2>
        <p className="text-muted-foreground mb-6">
          Your past analyses will appear here after you upload and process files.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
        >
          <FileJson className="w-4 h-4" />
          Upload Your First Analysis
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
            <HistoryIcon className="w-8 h-8 text-primary" />
            Analysis History
          </h1>
          <p className="text-muted-foreground mt-1">
            {analyses.length} {analyses.length === 1 ? 'analysis' : 'analyses'} stored
          </p>
        </div>
        
        <button
          onClick={handleClearAll}
          className="flex items-center gap-2 px-4 py-2 bg-destructive/10 hover:bg-destructive/20 text-destructive rounded-lg transition-all"
        >
          <Trash2 className="w-4 h-4" />
          <span>Clear All</span>
        </button>
      </div>

      {/* Grouped by date */}
      <div className="space-y-8">
        {Object.entries(groupedAnalyses).map(([date, dateAnalyses]) => (
          <div key={date}>
            <div className="flex items-center gap-2 mb-4">
              <Calendar className="w-4 h-4 text-muted-foreground" />
              <h2 className="text-lg font-semibold text-foreground">{date}</h2>
              <span className="text-sm text-muted-foreground">
                ({dateAnalyses.length} {dateAnalyses.length === 1 ? 'analysis' : 'analyses'})
              </span>
            </div>
            
            <div className="space-y-3">
              {dateAnalyses.map((analysis) => (
                <AnalysisCard 
                  key={analysis.id} 
                  analysis={analysis} 
                  onDelete={handleDelete} 
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

interface AnalysisCardProps {
  analysis: AnalysisResponse;
  onDelete: (id: string, e: React.MouseEvent) => void;
}

const AnalysisCard = ({ analysis, onDelete }: AnalysisCardProps) => {
  const { id, timestamp, filename, data } = analysis;
  const { summary } = data;
  
  return (
    <Link
      to={`/analysis/${id}`}
      className="glass-card p-4 sm:p-6 flex flex-col sm:flex-row sm:items-center gap-4 group hover:ring-2 hover:ring-primary/50 transition-all"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-2">
          <FileJson className="w-5 h-5 text-primary shrink-0" />
          <h3 className="font-semibold text-foreground truncate">{filename}</h3>
        </div>
        
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="w-3.5 h-3.5" />
          <span>{format(new Date(timestamp), 'p')}</span>
        </div>
      </div>
      
      {/* Quick stats */}
      <div className="flex items-center gap-3 flex-wrap">
        <StatBadge 
          icon={CheckCircle2} 
          value={summary.exact_match_count} 
          color="exact" 
          label="Exact"
        />
        <StatBadge 
          icon={AlertTriangle} 
          value={summary.low_rank_count + summary.medium_rank_count} 
          color="low" 
          label="Risk"
        />
        <StatBadge 
          icon={AlertOctagon} 
          value={summary.critical_rank_count} 
          color="critical" 
          label="Critical"
        />
        <StatBadge 
          icon={XCircle} 
          value={summary.error_count} 
          color="error" 
          label="Errors"
        />
      </div>
      
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={(e) => onDelete(id, e)}
          className="p-2 rounded-lg bg-secondary hover:bg-destructive/20 hover:text-destructive transition-all"
        >
          <Trash2 className="w-4 h-4" />
        </button>
        <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
      </div>
    </Link>
  );
};

interface StatBadgeProps {
  icon: typeof CheckCircle2;
  value: number;
  color: 'exact' | 'low' | 'critical' | 'error';
  label: string;
}

const StatBadge = ({ icon: Icon, value, color, label }: StatBadgeProps) => {
  const colorClasses = {
    exact: 'text-exact bg-exact/10',
    low: 'text-low bg-low/10',
    critical: 'text-critical bg-critical/10',
    error: 'text-error bg-error/10',
  };
  
  return (
    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-mono ${colorClasses[color]}`}>
      <Icon className="w-3 h-3" />
      <span>{value}</span>
      <span className="hidden sm:inline text-muted-foreground">{label}</span>
    </div>
  );
};

export default History;
