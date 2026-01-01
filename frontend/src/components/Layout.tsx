import { Link, useLocation } from 'react-router-dom';
import { Sparkles, History, Upload, ChevronRight } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
  const location = useLocation();
  
  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Ambient background effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-exact/5 rounded-full blur-[100px]" />
      </div>

      <div className="relative">
        {/* Header */}
        <header className="border-b border-border/50 backdrop-blur-xl bg-background/50 sticky top-0 z-50">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-exact flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-background" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-foreground">Coin Analyzer</h1>
                  <p className="text-xs text-muted-foreground">Receipt Processing Dashboard</p>
                </div>
              </Link>
              
              <nav className="flex items-center gap-2">
                <Link
                  to="/"
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    isActive('/') && location.pathname === '/'
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
                  }`}
                >
                  <Upload className="w-4 h-4" />
                  <span className="hidden sm:inline">Upload</span>
                </Link>
                <Link
                  to="/history"
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    isActive('/history')
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
                  }`}
                >
                  <History className="w-4 h-4" />
                  <span className="hidden sm:inline">History</span>
                </Link>
              </nav>
            </div>
          </div>
        </header>

        {/* Breadcrumb */}
        {location.pathname !== '/' && (
          <div className="border-b border-border/30 bg-background/30 backdrop-blur-sm">
            <div className="container mx-auto px-4 py-2">
              <Breadcrumb />
            </div>
          </div>
        )}

        {/* Main content */}
        <main className="container mx-auto px-4 py-8 md:py-12">
          {children}
        </main>
      </div>
    </div>
  );
};

const Breadcrumb = () => {
  const location = useLocation();
  const paths = location.pathname.split('/').filter(Boolean);
  
  const getBreadcrumbLabel = (segment: string, index: number): string => {
    if (segment === 'history') return 'History';
    if (segment === 'analysis') return 'Analysis';
    if (segment === 'exact') return 'Exact Match';
    if (segment === 'low') return 'Low Risk';
    if (segment === 'medium') return 'Medium Risk';
    if (segment === 'critical') return 'Critical';
    if (segment === 'errors') return 'Errors';
    // If it's an ID (after 'analysis'), show shortened version
    if (index === 1 && paths[0] === 'analysis') {
      return `#${segment.slice(-6)}`;
    }
    return segment;
  };

  return (
    <nav className="flex items-center gap-1 text-sm">
      <Link to="/" className="text-muted-foreground hover:text-foreground transition-colors">
        Home
      </Link>
      {paths.map((segment, index) => {
        const path = '/' + paths.slice(0, index + 1).join('/');
        const isLast = index === paths.length - 1;
        
        return (
          <div key={path} className="flex items-center gap-1">
            <ChevronRight className="w-3 h-3 text-muted-foreground" />
            {isLast ? (
              <span className="text-foreground font-medium">
                {getBreadcrumbLabel(segment, index)}
              </span>
            ) : (
              <Link to={path} className="text-muted-foreground hover:text-foreground transition-colors">
                {getBreadcrumbLabel(segment, index)}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
};
