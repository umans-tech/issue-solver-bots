'use client';

import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { Button } from './ui/button';
import { CopyIcon, DownloadIcon, MermaidCodeIcon, MermaidDiagramIcon, LoaderIcon, XIcon } from './icons';
import { toast } from 'sonner';
import { CodeBlock } from './code-block';
import { cn } from '@/lib/utils';

interface MermaidDiagramProps {
  code: string;
  className?: string;
}

const viewModes = ['code', 'diagram'] as const;
type ViewMode = (typeof viewModes)[number];

export function MermaidDiagram({ code, className }: MermaidDiagramProps) {
  const diagramRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('diagram');
  const [isLoading, setIsLoading] = useState(true);
  const [isFullPage, setIsFullPage] = useState(false);

  const isCodeView = viewMode === 'code';
  const isDiagramView = viewMode === 'diagram';

  useEffect(() => {
    // Initialize mermaid with dark theme support
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
      themeVariables: {
        darkMode: document.documentElement.classList.contains('dark'),
      },
      flowchart: {
        htmlLabels: true,
        useMaxWidth: true,
      }
    });

    // Render the diagram
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
        
        // First validate the syntax
        await mermaid.parse(code);
        
        // If validation passes, render the diagram
        const { svg } = await mermaid.render(uniqueId, code);
        // Remove any error icons or messages from the SVG
        const cleanedSvg = svg.replace(/<g class="error-icon">.*?<\/g>/g, '');
        setSvg(cleanedSvg);
        setError(null);
      } catch (parseError: any) {
        const errorMessage = parseError?.str || parseError?.message || 'Invalid diagram syntax';
        setError(`Syntax error in diagram: ${errorMessage}`);
      } finally {
        setIsLoading(false);
      }
    };

    if (viewMode === 'diagram') {
      renderDiagram();
    }
  }, [code, viewMode]);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code);
    toast.success('Copied diagram code to clipboard!');
  };

  const handleDownloadPNG = async () => {
    try {
      const svgElement = diagramRef.current?.querySelector('svg');
      if (!svgElement) {
        toast.error('No diagram to download');
        return;
      }

      // Create a new SVG element with proper dimensions
      const clonedSvg = svgElement.cloneNode(true) as SVGElement;
      const bbox = svgElement.getBBox();
      
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
      
      // Create downloadable link
      const link = document.createElement('a');
      link.download = 'diagram.svg';
      link.href = URL.createObjectURL(svgBlob);
      link.click();
      
      // Cleanup
      URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error('Error downloading diagram:', error);
      toast.error('Failed to download diagram');
    }
  };

  const toggleViewMode = () => {
    setViewMode(current => current === 'code' ? 'diagram' : 'code');
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
              isFullPage && "min-w-[800px] w-fit max-w-[95vw] max-h-[95vh] mx-auto"
            )}
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