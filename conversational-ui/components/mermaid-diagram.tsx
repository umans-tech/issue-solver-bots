'use client';

import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { Button } from './ui/button';
import { CopyIcon, DownloadIcon, MermaidCodeIcon, MermaidDiagramIcon } from './icons';
import { toast } from 'sonner';
import { CodeBlock } from './code-block';

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
    });

    // Render the diagram
    const renderDiagram = async () => {
      try {
        // Check if the code is incomplete or empty
        if (!code || code.trim() === '') {
          setError('Diagram code is empty');
          return;
        }

        // Basic validation of mermaid syntax
        if (!code.includes('graph') && !code.includes('sequenceDiagram') && !code.includes('classDiagram')) {
          setError('Invalid or incomplete diagram code');
          return;
        }

        // Generate a unique ID that's safe for CSS selectors
        const uniqueId = `mermaid-diagram-${Math.random().toString(36).substring(2)}`;
        const { svg } = await mermaid.render(uniqueId, code);
        setSvg(svg);
        setError(null);
      } catch (error) {
        console.error('Error rendering mermaid diagram:', error);
        setError('Failed to render diagram');
        // If rendering fails, switch to code view
        setViewMode('code');
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

  if (error && isDiagramView) {
    return (
      <div className="w-full">
        <div className="flex justify-end mb-2">
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
        <div className="w-full p-4 text-sm text-red-500 bg-red-50 dark:bg-red-950/50 rounded-lg">
          {error}
        </div>
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
        {!isCodeView && (
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
      
      <div className="relative w-full overflow-hidden mb-4" ref={diagramRef}>
        {isCodeView ? (
          <CodeBlock
            node={null}
            inline={false}
            className="language-mermaid"
            children={code}
          />
        ) : (
          <div
            className={`${className} p-4 bg-background rounded-lg`}
            dangerouslySetInnerHTML={{ __html: svg }}
          />
        )}
      </div>
    </div>
  );
} 