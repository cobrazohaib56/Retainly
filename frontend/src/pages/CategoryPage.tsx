import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getCategoryEntries, AnalysisEntry, ErrorEntry, NoImageEntry } from '@/lib/api';
import { EntryCard } from '@/components/EntryCard';
import { RiskCategory } from '@/types/analysis';
import { ArrowLeft, FileJson, CheckCircle2, AlertTriangle, AlertOctagon, XCircle, ImageOff } from 'lucide-react';

const categoryConfig: Record<string, { 
  key: RiskCategory; 
  label: string; 
  description: string;
  icon: typeof CheckCircle2;
}> = {
  exact: {
    key: 'exact',
    label: 'Exact Match',
    description: 'Entries where receipt total matches expected fiat amount',
    icon: CheckCircle2,
  },
  low: {
    key: 'low',
    label: 'Low Risk',
    description: 'Entries with minor discrepancy (≤10 amount difference)',
    icon: AlertTriangle,
  },
  medium: {
    key: 'medium',
    label: 'Medium Risk',
    description: 'Entries with moderate discrepancy (11-30 amount difference)',
    icon: AlertTriangle,
  },
  critical: {
    key: 'critical',
    label: 'Critical',
    description: 'Entries with major discrepancy (>30 amount difference)',
    icon: AlertOctagon,
  },
  error: {
    key: 'error',
    label: 'Errors',
    description: 'Entries that failed during processing',
    icon: XCircle,
  },
  no_image: {
    key: 'no_image',
    label: 'No Image',
    description: 'Entries missing receipt photo URL',
    icon: ImageOff,
  },
};

const CategoryPage = () => {
  const { id, category } = useParams<{ id: string; category: string }>();
  const [entries, setEntries] = useState<(AnalysisEntry | ErrorEntry | NoImageEntry)[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const config = category ? categoryConfig[category] : null;

  useEffect(() => {
    if (!id || !category || !config) {
      setError('Analysis ID and category are required');
      setLoading(false);
      return;
    }

    const fetchEntries = async () => {
      try {
        const data = await getCategoryEntries(id, category as 'exact' | 'low' | 'medium' | 'critical' | 'error' | 'no_image');
        setEntries(data.entries);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load entries');
      } finally {
        setLoading(false);
      }
    };

    fetchEntries();
  }, [id, category, config]);

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Loading entries...</p>
      </div>
    );
  }

  if (error || !config) {
    return (
      <div className="text-center py-20">
        <FileJson className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-foreground mb-2">Not Found</h2>
        <p className="text-muted-foreground mb-6">{error || 'This analysis or category doesn\'t exist.'}</p>
        <Link
          to={id ? `/analysis/${id}` : '/'}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
        >
          {id ? 'Back to Analysis' : 'Go Home'}
        </Link>
      </div>
    );
  }

  const Icon = config.icon;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link
          to={`/analysis/${id}`}
          className="mt-1 p-2 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-muted-foreground" />
        </Link>
        
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div 
              className={`w-10 h-10 rounded-xl flex items-center justify-center risk-${config.key}`}
              style={{ background: 'var(--risk-gradient)' }}
            >
              <Icon className="w-5 h-5 text-background" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">{config.label}</h1>
              <p className="text-sm text-muted-foreground">{config.description}</p>
            </div>
          </div>
          <p className="text-sm text-muted-foreground font-mono mt-2">
            {entries.length} {entries.length === 1 ? 'entry' : 'entries'}
          </p>
        </div>
      </div>

      {/* Entries */}
      {entries.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <Icon className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No entries in this category</p>
        </div>
      ) : (
        <div className="space-y-4">
          {entries.map((entry, index) => (
            <EntryCard 
              key={entry.entry_id || index} 
              entry={entry} 
              category={config.key}
              index={index}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default CategoryPage;
