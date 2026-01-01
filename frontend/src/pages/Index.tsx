import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileUpload } from '@/components/FileUpload';
import { uploadFile, pollStatus } from '@/lib/api';

const Index = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleFileLoaded = useCallback(async (file: File) => {
    setIsProcessing(true);
    setProgress(0);
    setError(null);
    
    try {
      // Upload file to backend
      const analysis = await uploadFile(file);
      
      // Poll for status until completion
      await pollStatus(
        analysis.id,
        (progressValue) => {
          setProgress(progressValue || 0);
        },
        2000
      );
      
      // Navigate to analysis page
      setIsProcessing(false);
      navigate(`/analysis/${analysis.id}`);
    } catch (err) {
      setIsProcessing(false);
      const errorMessage = err instanceof Error ? err.message : 'Failed to process file';
      setError(errorMessage);
    }
  }, [navigate]);

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-4xl font-bold text-foreground mb-3">
          Analyze Your Results
        </h2>
        <p className="text-muted-foreground text-lg">
          Upload your family coins analysis JSON to visualize the extraction results
        </p>
      </div>
      
      <FileUpload 
        onFileLoaded={handleFileLoaded} 
        isProcessing={isProcessing} 
        progress={progress}
      />

      {error && (
        <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
          {error}
        </div>
      )}

      <div className="mt-8 text-center">
        <p className="text-sm text-muted-foreground">
          Upload your JSON dataset to process receipt images and extract family coins
        </p>
      </div>
    </div>
  );
};

export default Index;
