'use client';

import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { Button } from './ui/button';
import { CopyIcon, DownloadIcon, MermaidCodeIcon, MermaidDiagramIcon, LoaderIcon, XIcon } from './icons';
import { toast } from 'sonner';
import { CodeBlock } from './code-block';
import { cn } from '@/lib/utils';
import { ErrorBoundary } from './error-boundary';

interface MermaidDiagramProps {
  code: string;
  className?: string;
}

const viewModes = ['code', 'diagram'] as const;
type ViewMode = (typeof viewModes)[number];

// Mermaid-specific error fallback component
function MermaidErrorFallback() {
  return (
    <div className="w-full p-4 rounded-lg border border-amber-200 dark:border-amber-800 bg-background">
      <p className="text-sm font-medium text-amber-600 dark:text-amber-400">
        Diagram rendering failed
      </p>
      <p className="text-sm text-muted-foreground mt-2">
        There was a problem rendering the diagram. Please check your diagram syntax or try again later.
      </p>
    </div>
  );
}

// Wrapped component with added error handling
function MermaidDiagramContent({ code, className }: MermaidDiagramProps) {
  const diagramRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('diagram');
  const [isLoading, setIsLoading] = useState(true);
  const [isFullPage, setIsFullPage] = useState(false);

  const isCodeView = viewMode === 'code';
  const isDiagramView = viewMode === 'diagram';

  useEffect(() => {
    // Safely initialize mermaid with dark theme support
    try {
      mermaid.initialize({
        startOnLoad: true,
        theme: 'default',
        securityLevel: 'loose',
        suppressErrorRendering: true,
        logLevel: 5, // "error" level - suppresses console warnings
        themeVariables: {
          darkMode: document.documentElement.classList.contains('dark'),
        },
        flowchart: {
          htmlLabels: true,
          useMaxWidth: true,
        }
      });
    } catch (initError) {
      console.error('Error initializing Mermaid (suppressed):', initError);
      // Don't rethrow - we don't want to break the UI if mermaid fails to initialize
    }

    // Render the diagram with improved error handling
    const renderDiagram = async () => {
      if (!code || code.trim() === '') {
        setError('The diagram code is empty. Please provide valid Mermaid syntax.');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        setSvg('');

        // Generate a unique ID that's safe for CSS selectors
        const uniqueId = `mermaid-diagram-${Math.random().toString(36).substring(2)}`;
        
        // Wrap in a try-catch to handle syntax validation errors
        let parseSuccess = false;
        try {
          // First validate the syntax
          await mermaid.parse(code);
          parseSuccess = true;
        } catch (parseError: any) {
          // Suppress the error from reaching the browser
          const errorMessage = parseError?.str || parseError?.message || 'Invalid diagram syntax';
          setError(`Syntax error in diagram: ${errorMessage}`);
          console.error('Mermaid parse error (suppressed):', errorMessage);
          setIsLoading(false);
          return;
        }
        
        // Only try to render if parsing was successful
        if (parseSuccess) {
          try {
            // If validation passes, render the diagram
            const { svg } = await mermaid.render(uniqueId, code);
            // Remove any error icons or messages from the SVG
            const cleanedSvg = svg.replace(/<g class="error-icon">.*?<\/g>/g, '');
            setSvg(cleanedSvg);
            setError(null);
          } catch (renderError: any) {
            // Handle render errors separately
            const errorMessage = renderError?.str || renderError?.message || 'Error rendering diagram';
            setError(`Failed to render diagram: ${errorMessage}`);
            console.error('Mermaid render error (suppressed):', errorMessage);
          }
        }
      } catch (unexpectedError: any) {
        // Catch-all for any other unexpected errors
        const errorMessage = unexpectedError?.message || 'Unexpected error occurred';
        setError(`Diagram error: ${errorMessage}`);
        console.error('Unexpected Mermaid error (suppressed):', unexpectedError);
      } finally {
        setIsLoading(false);
      }
    };

    // Only try to render diagram if in diagram view mode
    if (viewMode === 'diagram') {
      // Wrap the entire operation in a try-catch to prevent any uncaught errors
      try {
        renderDiagram();
      } catch (criticalError) {
        // Last resort error handler to prevent browser notifications
        console.error('Critical Mermaid error (suppressed):', criticalError);
        setError('Failed to process diagram. Please check your syntax.');
        setIsLoading(false);
      }
    }
  }, [code, viewMode]);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code);
    toast.success('Copied diagram code to clipboard!');
  };

  const handleDownloadPNG = async () => {
    try {
      // Defensively check if diagramRef exists before proceeding
      if (!diagramRef || !diagramRef.current) {
        toast.error('No diagram container found');
        return;
      }

      const svgElement = diagramRef.current?.querySelector('svg');
      if (!svgElement) {
        toast.error('No diagram to download');
        return;
      }

      // Wrap all DOM operations in try-catch to prevent uncaught errors
      try {
        // Create a new SVG element with proper dimensions
        const clonedSvg = svgElement.cloneNode(true) as SVGElement;
        
        // Safely get bounding box - getBBox might throw in some edge cases
        let bbox;
        try {
          bbox = svgElement.getBBox();
        } catch (bboxError) {
          console.error('SVG getBBox error (suppressed):', bboxError);
          // Fallback to a default size if getBBox fails
          bbox = { x: 0, y: 0, width: 800, height: 600 };
        }
        
        // Add padding to the SVG
        const padding = 20;
        const width = bbox.width + padding * 2;
        const height = bbox.height + padding * 2;
        
        clonedSvg.setAttribute('width', width.toString());
        clonedSvg.setAttribute('height', height.toString());
        clonedSvg.setAttribute('viewBox', `${bbox.x - padding} ${bbox.y - padding} ${width} ${height}`);
        
        // Convert SVG to a data URL
        const svgData = new XMLSerializer().serializeToString(clonedSvg);
        const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
        
        // Create downloadable link with additional error handling
        try {
          const link = document.createElement('a');
          link.download = 'diagram.svg';
          link.href = URL.createObjectURL(svgBlob);
          link.click();
          
          // Cleanup
          setTimeout(() => {
            try {
              URL.revokeObjectURL(link.href);
            } catch (revokeError) {
              console.error('URL.revokeObjectURL error (suppressed):', revokeError);
            }
          }, 100);
        } catch (downloadError) {
          console.error('Download link creation error (suppressed):', downloadError);
          toast.error('Failed to create download link');
        }
      } catch (svgProcessingError) {
        console.error('SVG processing error (suppressed):', svgProcessingError);
        toast.error('Failed to process diagram for download');
      }
    } catch (error) {
      // Outer catch-all to ensure no errors bubble up
      console.error('Error downloading diagram (suppressed):', error);
      toast.error('Failed to download diagram');
    }
  };

  const toggleViewMode = () => {
    try {
      setViewMode(current => current === 'code' ? 'diagram' : 'code');
    } catch (viewModeError) {
      // Suppress any errors that might occur when toggling view mode
      console.error('View mode toggle error (suppressed):', viewModeError);
      // Try to force a known good state
      setViewMode('code');
    }
  };

  if (error) {
    return (
      <div className="w-full">
        <div className="flex justify-end mb-2 gap-2">
          <Button
            onClick={toggleViewMode}
            variant="ghost"
            size="sm"
            className="gap-2"
          >
            {isCodeView ? (
              <>
                <MermaidDiagramIcon size={16} />
                Try Diagram
              </>
            ) : (
              <>
                <MermaidCodeIcon size={16} />
                Show Code
              </>
            )}
          </Button>
        </div>
        {isDiagramView && (
          <div className="w-full p-4 rounded-lg border border-red-200 dark:border-red-800 bg-background space-y-2">
            <p className="text-sm font-medium text-red-600 dark:text-red-400">
              Failed to render diagram
            </p>
            <p className="text-sm text-muted-foreground">
              {error}
            </p>
          </div>
        )}
        {isCodeView && (
          <CodeBlock
            node={null}
            inline={false}
            className="language-mermaid"
            children={code}
          />
        )}
      </div>
    );
  }

  return (
    <div className="w-full mt-4">
      <div className="flex justify-end mb-4 gap-2">
       {!isCodeView && !error && !isLoading && (
          <Button
            onClick={handleDownloadPNG}
            variant="ghost"
            size="sm"
            className="gap-2"
          >
            <DownloadIcon size={16} />
            Download SVG
          </Button>
        )}
        <Button
          onClick={toggleViewMode}
          variant="ghost"
          size="sm"
          className="gap-2"
        >
          {isCodeView ? (
            <>
              <MermaidDiagramIcon size={16} />
              Show Diagram
            </>
          ) : (
            <>
              <MermaidCodeIcon size={16} />
              Show Code
            </>
          )}
        </Button>
      </div>
      
      <div className={cn(
        "relative w-full overflow-hidden mb-4",
        isFullPage && "fixed inset-0 z-50 bg-background/95 backdrop-blur-sm flex items-start justify-center p-8 overflow-y-auto"
      )} ref={diagramRef} onClick={(e) => {
        if (isFullPage && e.target === e.currentTarget) {
          setIsFullPage(false);
        }
      }}>
        {isCodeView ? (
          <CodeBlock
            node={null}
            inline={false}
            className="language-mermaid"
            children={code}
          />
        ) : isLoading ? (
          <div className="w-full p-8 flex items-center justify-center gap-2 text-muted-foreground bg-muted/30 rounded-lg">
            <div className="animate-spin">
              <LoaderIcon size={16} />
            </div>
            <span>Generating diagram...</span>
          </div>
        ) : error ? (
          <div className="w-full p-4 rounded-lg border border-red-200 dark:border-red-800 bg-background">
            <p className="text-sm text-red-600 dark:text-red-400">
              {error}
            </p>
          </div>
        ) : (
          <div
            className={cn(
              `${className} p-4 bg-background rounded-lg cursor-pointer transition-transform hover:scale-[1.02]`,
              isFullPage && "min-w-[800px] w-auto h-auto mx-auto my-8"
            )}
            style={isFullPage ? { transform: 'scale(1.5)', transformOrigin: 'top center' } : undefined}
            onClick={(e) => {
              e.stopPropagation();
              if (!isCodeView) setIsFullPage(!isFullPage);
            }}
            dangerouslySetInnerHTML={{ __html: svg }}
          />
        )}
        {isFullPage && (
          <Button
            onClick={(e) => {
              e.stopPropagation();
              setIsFullPage(false);
            }}
            variant="ghost"
            size="icon"
            className="fixed top-4 right-4"
          >
            <XIcon size={16} />
          </Button>
        )}
      </div>
    </div>
  );
} 

// Export the error-boundary-wrapped component
export function MermaidDiagram(props: MermaidDiagramProps) {
  // Wrap the component with our error boundary to catch any uncaught errors
  return (
    <ErrorBoundary fallback={<MermaidErrorFallback />}>
      <MermaidDiagramContent {...props} />
    </ErrorBoundary>
  );
}