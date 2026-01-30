import { RiskCategory } from '@/types/analysis';
import { Link } from 'react-router-dom';
import { CheckCircle2, AlertTriangle, AlertOctagon, XCircle, ArrowRight, ImageOff } from 'lucide-react';

interface CategoryCardProps {
  category: RiskCategory;
  count: number;
  total: number;
  analysisId: string;
}

const categoryConfig = {
  exact: {
    label: 'Exact Match',
    description: 'Perfect extraction',
    icon: CheckCircle2,
    className: 'risk-exact',
    path: 'exact',
  },
  low: {
    label: 'Low Risk',
    description: 'Minor discrepancy (≤10)',
    icon: AlertTriangle,
    className: 'risk-low',
    path: 'low',
  },
  medium: {
    label: 'Medium Risk',
    description: 'Moderate discrepancy (≤30)',
    icon: AlertTriangle,
    className: 'risk-medium',
    path: 'medium',
  },
  critical: {
    label: 'Critical',
    description: 'Major discrepancy (>30)',
    icon: AlertOctagon,
    className: 'risk-critical',
    path: 'critical',
  },
  error: {
    label: 'Errors',
    description: 'Processing failed',
    icon: XCircle,
    className: 'risk-error',
    path: 'error',
  },
  no_image: {
    label: 'No Image',
    description: 'Missing photo URL',
    icon: ImageOff,
    className: 'risk-error',
    path: 'no_image',
  },
};

export const CategoryCard = ({ category, count, total, analysisId }: CategoryCardProps) => {
  const config = categoryConfig[category];
  const Icon = config.icon;
  const percentage = total > 0 ? (count / total) * 100 : 0;

  return (
    <Link
      to={`/analysis/${analysisId}/${config.path}`}
      className={`
        glass-card p-6 text-left transition-all duration-300 group block
        hover:scale-[1.02] active:scale-[0.98]
        ${config.className}
        hover:ring-2 hover:ring-[hsl(var(--risk-color))]
      `}
    >
      <div className="flex items-start justify-between mb-4">
        <div 
          className="w-12 h-12 rounded-xl flex items-center justify-center"
          style={{ background: 'var(--risk-gradient)' }}
        >
          <Icon className="w-6 h-6 text-background" />
        </div>
        <ArrowRight 
          className="w-5 h-5 text-muted-foreground transition-transform duration-300 group-hover:translate-x-1"
        />
      </div>
      
      <h3 className="text-2xl font-bold text-foreground mb-1">{count}</h3>
      <p className="text-sm font-medium" style={{ color: 'hsl(var(--risk-color))' }}>
        {config.label}
      </p>
      <p className="text-xs text-muted-foreground mt-1">{config.description}</p>
      
      {/* Progress bar */}
      <div className="mt-4 h-1.5 bg-secondary rounded-full overflow-hidden">
        <div 
          className="h-full rounded-full transition-all duration-500"
          style={{ 
            width: `${percentage}%`,
            background: 'var(--risk-gradient)',
          }}
        />
      </div>
      <p className="text-xs text-muted-foreground mt-2 font-mono">
        {percentage.toFixed(1)}% of total
      </p>
    </Link>
  );
};
