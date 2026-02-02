import { useCallback, useState } from 'react';
import { Upload, FileJson, AlertCircle, Loader2, Receipt, User } from 'lucide-react';

interface CurrentEntry {
  receipt_number: string;
  to_user: string;
  entry_index: number;
  total_entries: number;
  reference_id?: string;
}

interface FileUploadProps {
  onFileLoaded: (file: File) => void;
  isProcessing: boolean;
  progress?: number;
  currentEntry?: CurrentEntry | null;
}

export const FileUpload = ({ onFileLoaded, isProcessing, progress = 0, currentEntry }: FileUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback((file: File) => {
    setError(null);
    
    const isJson = file.name.toLowerCase().endsWith('.json');
    const isCsv = file.name.toLowerCase().endsWith('.csv');
    if (!isJson && !isCsv) {
      setError('Please upload a JSON or CSV file');
      return;
    }

    // Pass the File object directly to the parent for API upload
    onFileLoaded(file);
  }, [onFileLoaded]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  if (isProcessing) {
    return (
      <div className="glass-card p-12 flex flex-col items-center justify-center min-h-[300px]">
        <div className="relative">
          <div className="w-20 h-20 rounded-full border-4 border-muted animate-spin-slow" 
               style={{ borderTopColor: 'hsl(var(--primary))' }} />
          <div className="absolute inset-0 flex items-center justify-center">
            <FileJson className="w-8 h-8 text-primary animate-pulse" />
          </div>
        </div>
        <p className="mt-6 text-lg font-medium text-foreground">Processing your data...</p>
        <p className="mt-2 text-sm text-muted-foreground">Analyzing receipt entries</p>
        
        {/* Live current transaction */}
        {currentEntry && (
          <div className="mt-6 w-full max-w-sm p-4 rounded-xl bg-primary/10 border border-primary/20">
            <div className="flex items-center gap-2 mb-2">
              <Loader2 className="w-4 h-4 text-primary animate-spin shrink-0" />
              <span className="text-sm font-medium text-foreground">Currently processing</span>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <Receipt className="w-4 h-4 text-muted-foreground shrink-0" />
                <span className="font-mono text-foreground">#{currentEntry.receipt_number}</span>
              </div>
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-muted-foreground shrink-0" />
                <span className="text-foreground">{currentEntry.to_user}</span>
              </div>
              {currentEntry.reference_id && (
                <div className="text-xs text-muted-foreground font-mono">
                  Ref: {currentEntry.reference_id}
                </div>
              )}
              <div className="text-xs text-muted-foreground pt-1">
                Entry {currentEntry.entry_index} of {currentEntry.total_entries}
              </div>
            </div>
          </div>
        )}
        
        {progress > 0 && (
          <div className="mt-4 w-full max-w-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">Progress</span>
              <span className="text-xs text-muted-foreground font-mono">{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-secondary rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`
        glass-card p-12 flex flex-col items-center justify-center min-h-[300px] relative
        border-2 border-dashed transition-all duration-300 cursor-pointer
        ${isDragging 
          ? 'border-primary bg-primary/5 scale-[1.02]' 
          : 'border-border hover:border-muted-foreground hover:bg-card/50'
        }
      `}
    >
      <input
        type="file"
        accept=".json,.csv"
        onChange={handleInputChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />
      
      <div className={`
        w-16 h-16 rounded-2xl flex items-center justify-center mb-6 transition-all duration-300
        ${isDragging ? 'bg-primary/20 scale-110' : 'bg-secondary'}
      `}>
        <Upload className={`w-8 h-8 transition-colors ${isDragging ? 'text-primary' : 'text-muted-foreground'}`} />
      </div>
      
      <h3 className="text-xl font-semibold text-foreground mb-2">
        {isDragging ? 'Drop your file here' : 'Upload Analysis Results'}
      </h3>
      <p className="text-muted-foreground text-center max-w-sm">
        Drag and drop your JSON or CSV file here, or click to browse
      </p>
      <p className="text-xs text-muted-foreground mt-4 font-mono">
        .json or .csv
      </p>

      {error && (
        <div className="mt-6 flex items-center gap-2 text-destructive bg-destructive/10 px-4 py-2 rounded-lg">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">{error}</span>
        </div>
      )}
    </div>
  );
};
