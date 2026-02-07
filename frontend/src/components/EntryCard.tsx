import { AnalysisEntry, ErrorEntry, NoImageEntry, RiskCategory } from '@/types/analysis';
import { Coins, ArrowRight, User, Receipt, ExternalLink, AlertCircle, ImageOff } from 'lucide-react';
import { useState } from 'react';
import { getImageUrl } from '@/lib/api';

interface EntryCardProps {
  entry: AnalysisEntry | ErrorEntry | NoImageEntry;
  category: RiskCategory;
  index: number;
}

const isErrorEntry = (entry: AnalysisEntry | ErrorEntry | NoImageEntry): entry is ErrorEntry => {
  return 'error' in entry;
};

const isNoImageEntry = (entry: AnalysisEntry | ErrorEntry | NoImageEntry): entry is NoImageEntry => {
  return !('error' in entry) && !('extracted_family_coins' in entry);
};

export const EntryCard = ({ entry, category, index }: EntryCardProps) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [useBackendImage, setUseBackendImage] = useState(true);
  const [isErrorExpanded, setIsErrorExpanded] = useState(false);

  const categoryClassName = {
    exact: 'risk-exact',
    low: 'risk-low',
    medium: 'risk-medium',
    critical: 'risk-critical',
    error: 'risk-error',
    no_image: 'risk-error',
  }[category];

  if (isNoImageEntry(entry)) {
    return (
      <div 
        className={`glass-card p-6 ${categoryClassName} animate-fade-in`}
        style={{ animationDelay: `${index * 50}ms` }}
      >
        <div className="flex items-start gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Receipt className="w-4 h-4" />
                <span className="font-mono">#{entry.receipt_number}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <User className="w-4 h-4" />
                <span>{entry.to_user}</span>
              </div>
              {entry.from_merchant && (
                <span className="text-xs px-2 py-1 rounded-full bg-secondary text-muted-foreground">
                  {entry.from_merchant}
                </span>
              )}
            </div>
            {entry.reference_id && (
              <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground font-mono mt-1">
                <span className="uppercase tracking-wide text-[0.65rem]">Ref ID:</span>
                <span className="text-foreground">{entry.reference_id}</span>
              </div>
            )}
            
            <div className="p-4 rounded-lg bg-warning/10 border border-warning/20 mt-3">
              <div className="flex items-start gap-2">
                <ImageOff className="w-4 h-4 text-warning mt-0.5 shrink-0" />
                <div className="flex-1">
                  <p className="text-sm text-warning/90 font-medium">
                    Missing receipt photo URL
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    This entry cannot be processed without an image
                  </p>
                </div>
              </div>
            </div>
            
            <div className="mt-4 flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Expected amount (fiat):</span>
              <span className="font-mono font-semibold text-foreground">{entry.dataset_coins}</span>
            </div>
          </div>
          
          {/* No image placeholder */}
          <div className="relative w-48 h-60 shrink-0">
            <div className="absolute inset-0 bg-secondary rounded-lg flex flex-col items-center justify-center gap-2">
              <ImageOff className="w-12 h-12 text-muted-foreground" />
              <p className="text-xs text-muted-foreground">No Image</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isErrorEntry(entry)) {
    const shouldTruncate = entry.error.length > 200;
    const displayError = shouldTruncate && !isErrorExpanded 
      ? entry.error.slice(0, 200) 
      : entry.error;

    return (
      <div 
        className={`glass-card p-6 ${categoryClassName} animate-fade-in`}
        style={{ animationDelay: `${index * 50}ms` }}
      >
        <div className="flex items-start gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Receipt className="w-4 h-4" />
                <span className="font-mono">#{entry.receipt_number}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <User className="w-4 h-4" />
                <span>{entry.to_user}</span>
              </div>
            </div>
            {entry.reference_id && (
              <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground font-mono mt-1">
                <span className="uppercase tracking-wide text-[0.65rem]">Ref ID:</span>
                <span className="text-foreground">{entry.reference_id}</span>
              </div>
            )}
            
            <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-destructive mt-0.5 shrink-0" />
                <div className="flex-1">
                  <p className="text-sm text-destructive/90 font-mono break-all whitespace-pre-wrap">
                    {displayError}
                    {shouldTruncate && !isErrorExpanded && '...'}
                  </p>
                  {shouldTruncate && (
                    <button
                      onClick={() => setIsErrorExpanded(!isErrorExpanded)}
                      className="mt-2 text-xs text-destructive/80 hover:text-destructive underline"
                    >
                      {isErrorExpanded ? 'Show less' : 'Show full error'}
                    </button>
                  )}
                </div>
              </div>
            </div>
            
            <div className="mt-4 flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Expected amount (fiat):</span>
              <span className="font-mono font-semibold text-foreground">{entry.dataset_coins}</span>
            </div>
          </div>
          
          {/* Receipt image */}
          <div className="relative w-48 h-60 shrink-0">
            {!imageLoaded && !imageError && (
              <div className="absolute inset-0 bg-secondary rounded-lg animate-pulse" />
            )}
            {!imageError ? (
              <img
                src={useBackendImage ? getImageUrl(entry.receipt_number) : entry.receipt_photo_url}
                alt={`Receipt ${entry.receipt_number}`}
                className={`w-full h-full object-cover rounded-lg transition-opacity duration-300 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
                onLoad={() => setImageLoaded(true)}
                onError={() => {
                  if (useBackendImage) {
                    // Fallback to original URL if backend image fails
                    setUseBackendImage(false);
                    setImageLoaded(false);
                  } else {
                    setImageError(true);
                  }
                }}
              />
            ) : (
              <div className="absolute inset-0 bg-secondary rounded-lg flex items-center justify-center">
                <Receipt className="w-8 h-8 text-muted-foreground" />
              </div>
            )}
            <a
              href={useBackendImage && !imageError ? getImageUrl(entry.receipt_number) : entry.receipt_photo_url}
              target="_blank"
              rel="noopener noreferrer"
              className="absolute top-2 right-2 p-1.5 bg-background/80 backdrop-blur-sm rounded-md hover:bg-background transition-colors"
            >
              <ExternalLink className="w-3 h-3 text-muted-foreground" />
            </a>
          </div>
        </div>
      </div>
    );
  }

  const analysisEntry = entry as AnalysisEntry;
  const [analysisImageLoaded, setAnalysisImageLoaded] = useState(false);
  const [analysisImageError, setAnalysisImageError] = useState(false);
  const [useAnalysisBackendImage, setUseAnalysisBackendImage] = useState(true);

  return (
    <div 
      className={`glass-card p-6 ${categoryClassName} animate-fade-in`}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-start gap-6">
        <div className="flex-1">
          {/* Header info */}
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Receipt className="w-4 h-4" />
              <span className="font-mono">#{analysisEntry.receipt_number}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <User className="w-4 h-4" />
              <span>{analysisEntry.to_user}</span>
            </div>
            {analysisEntry.from_merchant && (
              <span className="text-xs px-2 py-1 rounded-full bg-secondary text-muted-foreground">
                {analysisEntry.from_merchant}
              </span>
            )}
          </div>

          {/* Amount comparison: expected fiat vs receipt total */}
          <div className="flex items-center gap-4 p-4 rounded-xl bg-secondary/50">
            <div className="flex-1">
              <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">Expected (fiat)</p>
              <div className="flex items-center gap-2">
                <Coins className="w-5 h-5 text-muted-foreground" />
                <span className="text-2xl font-bold font-mono text-foreground">
                  {analysisEntry.dataset_coins}
                </span>
              </div>
            </div>
            
            <ArrowRight className="w-5 h-5 text-muted-foreground shrink-0" />
            
            <div className="flex-1">
              <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">Invoice total</p>
              <div className="flex items-center gap-2">
                <Coins className="w-5 h-5" style={{ color: 'hsl(var(--risk-color))' }} />
                <span 
                  className="text-2xl font-bold font-mono"
                  style={{ color: 'hsl(var(--risk-color))' }}
                >
                  {analysisEntry.extracted_family_coins ?? 'N/A'}
                </span>
              </div>
              {analysisEntry.discount != null && analysisEntry.discount > 0 && analysisEntry.raw_total != null && (
                <p className="text-xs text-muted-foreground mt-1">
                  ({analysisEntry.raw_total} - {analysisEntry.discount} discount)
                </p>
              )}
            </div>
            
            <div className="flex-1 text-right">
              <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">Difference</p>
              <span 
                className="text-2xl font-bold font-mono"
                style={{ color: 'hsl(var(--risk-color))' }}
              >
                {analysisEntry.difference !== null ? (analysisEntry.difference > 0 ? `+${analysisEntry.difference}` : analysisEntry.difference) : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Receipt image */}
        <div className="relative w-56 h-64 shrink-0">
          {!analysisImageLoaded && !analysisImageError && (
            <div className="absolute inset-0 bg-secondary rounded-lg animate-pulse" />
          )}
          {!analysisImageError ? (
            <img
              src={useAnalysisBackendImage ? getImageUrl(analysisEntry.receipt_number) : analysisEntry.receipt_photo_url}
              alt={`Receipt ${analysisEntry.receipt_number}`}
              className={`w-full h-full object-cover rounded-lg transition-opacity duration-300 ${analysisImageLoaded ? 'opacity-100' : 'opacity-0'}`}
              onLoad={() => setAnalysisImageLoaded(true)}
              onError={() => {
                if (useAnalysisBackendImage) {
                  // Fallback to original URL if backend image fails
                  setUseAnalysisBackendImage(false);
                  setAnalysisImageLoaded(false);
                } else {
                  setAnalysisImageError(true);
                }
              }}
            />
          ) : (
            <div className="absolute inset-0 bg-secondary rounded-lg flex items-center justify-center">
              <Receipt className="w-8 h-8 text-muted-foreground" />
            </div>
          )}
          <a
            href={useAnalysisBackendImage && !analysisImageError ? getImageUrl(analysisEntry.receipt_number) : analysisEntry.receipt_photo_url}
            target="_blank"
            rel="noopener noreferrer"
            className="absolute top-2 right-2 p-1.5 bg-background/80 backdrop-blur-sm rounded-md hover:bg-background transition-colors"
          >
            <ExternalLink className="w-3 h-3 text-muted-foreground" />
          </a>
        </div>
      </div>
    </div>
  );
};
