import { AnalysisSummary } from '@/types/analysis';
import { Activity, CheckCircle, Percent, AlertCircle } from 'lucide-react';

interface SummaryStatsProps {
  summary: AnalysisSummary;
}

export const SummaryStats = ({ summary }: SummaryStatsProps) => {
  const totalProcessed = summary.processed + summary.errors;
  const successRate = totalProcessed > 0 
    ? ((summary.exact_match_count / totalProcessed) * 100).toFixed(1)
    : '0';

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="glass-card p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
            <Activity className="w-5 h-5 text-primary" />
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground font-mono">{summary.total_entries}</p>
            <p className="text-xs text-muted-foreground">Total Entries</p>
          </div>
        </div>
      </div>
      
      <div className="glass-card p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-exact/20 flex items-center justify-center">
            <CheckCircle className="w-5 h-5 text-exact" />
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground font-mono">{summary.processed}</p>
            <p className="text-xs text-muted-foreground">Processed</p>
          </div>
        </div>
      </div>
      
      <div className="glass-card p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-exact/20 flex items-center justify-center">
            <Percent className="w-5 h-5 text-exact" />
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground font-mono">{successRate}%</p>
            <p className="text-xs text-muted-foreground">Exact Match Rate</p>
          </div>
        </div>
      </div>
      
      <div className="glass-card p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-destructive/20 flex items-center justify-center">
            <AlertCircle className="w-5 h-5 text-destructive" />
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground font-mono">{summary.errors}</p>
            <p className="text-xs text-muted-foreground">Errors</p>
          </div>
        </div>
      </div>
    </div>
  );
};
