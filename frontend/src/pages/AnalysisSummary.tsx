import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getAnalysis, deleteAnalysis as deleteAnalysisAPI } from '@/lib/api';
import { SummaryStats } from '@/components/SummaryStats';
import { CategoryCard } from '@/components/CategoryCard';
import { RiskCategory, AnalysisResponse } from '@/lib/api';
import { FileJson, Trash2, Clock, FileText } from 'lucide-react';
import { format } from 'date-fns';

const AnalysisSummary = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setError('Analysis ID is required');
      setLoading(false);
      return;
    }

    const fetchAnalysis = async () => {
      try {
        const data = await getAnalysis(id);
        setAnalysis(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analysis');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [id]);

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Loading analysis...</p>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="text-center py-20">
        <FileJson className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-foreground mb-2">Analysis Not Found</h2>
        <p className="text-muted-foreground mb-6">{error || 'This analysis may have been deleted or doesn\'t exist.'}</p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
        >
          Upload New Analysis
        </Link>
      </div>
    );
  }

  const { data, timestamp, filename } = analysis;
  const totalProcessed = data.summary.processed + data.summary.errors;

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this analysis?')) {
      try {
        await deleteAnalysisAPI(id!);
      navigate('/history');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete analysis');
      }
    }
  };

  const categories: { key: RiskCategory; count: number }[] = [
    { key: 'exact', count: data.summary.exact_match_count },
    { key: 'low', count: data.summary.low_rank_count },
    { key: 'medium', count: data.summary.medium_rank_count },
    { key: 'critical', count: data.summary.critical_rank_count },
    { key: 'error', count: data.summary.error_count },
    { key: 'no_image', count: data.summary.no_image_count },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
            <FileJson className="w-8 h-8 text-primary" />
            Analysis Results
          </h1>
          <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <FileText className="w-4 h-4" />
              {filename}
            </span>
            <span className="flex items-center gap-1.5">
              <Clock className="w-4 h-4" />
              {format(new Date(timestamp), 'PPpp')}
            </span>
          </div>
        </div>
        
        <button
          onClick={handleDelete}
          className="flex items-center gap-2 px-4 py-2 bg-destructive/10 hover:bg-destructive/20 text-destructive rounded-lg transition-all hover:scale-105 active:scale-95"
        >
          <Trash2 className="w-4 h-4" />
          <span>Delete</span>
        </button>
      </div>

      {/* Summary stats */}
      <SummaryStats summary={data.summary} />

      {/* Category cards - click to navigate to section */}
      <div>
        <h2 className="text-lg font-semibold text-foreground mb-4">Risk Categories</h2>
        <p className="text-sm text-muted-foreground mb-4">Click a category to view detailed entries</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {categories.map(({ key, count }) => (
            <CategoryCard
              key={key}
              category={key}
              count={count}
              total={totalProcessed}
              analysisId={id!}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default AnalysisSummary;
