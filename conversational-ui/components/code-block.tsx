'use client';

import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { useTheme } from 'next-themes';
import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { Copy } from 'lucide-react';

interface CodeBlockProps {
  node: any;
  inline: boolean;
  className: string;
  children: any;
}

export function CodeBlock({
  node,
  inline,
  className,
  children,
  ...props
}: CodeBlockProps) {
  const { resolvedTheme } = useTheme();
  const [isHovered, setIsHovered] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [currentTheme, setCurrentTheme] = useState<string | undefined>(undefined);
  
  // Effect for client-side mounting and theme detection
  useEffect(() => {
    setMounted(true);
    setCurrentTheme(resolvedTheme);
  }, [resolvedTheme]);
  
  // Effect to update theme when it changes
  useEffect(() => {
    if (mounted) {
      setCurrentTheme(resolvedTheme);
    }
  }, [resolvedTheme, mounted]);
  
  // Check if this is a code block with a language specified
  const match = /language-(\w+)/.exec(className || '');
  const language = match?.[1];
  
  // For inline code or paths
  if (inline || !language) {
    return (
      <code
        className="text-sm bg-muted dark:bg-zinc-800 py-0.5 px-1 rounded-md"
        {...props}
      >
        {children}
      </code>
    );
  }
  
  const handleCopy = () => {
    const content = String(children).replace(/\n$/, '');
    navigator.clipboard.writeText(content);
    toast.success('Copied to clipboard!');
  };
  
  // For actual code blocks (with triple backticks)
  const Highlighter = SyntaxHighlighter as any;
  return (
    <div 
      className="relative w-full overflow-hidden"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {language && (
        <Button
          onClick={handleCopy}
          size="icon"
          variant="ghost"
          className={`absolute top-3 right-1.5 z-10 h-8 w-8 p-0 opacity-0 transition-opacity duration-200 ${
            isHovered ? 'opacity-100' : ''
          }`}
          aria-label="Copy code"
        >
          <Copy size={16} />
        </Button>
      )}
      <Highlighter
        style={currentTheme === 'dark' ? vscDarkPlus : vs}
        language={language}
        PreTag="div"
        className="text-sm rounded-xl"
        customStyle={{
          width: '100%',
          minWidth: '100%',
          overflow: 'auto',
          overflowX: 'auto',
          whiteSpace: 'pre',
          wordBreak: 'normal',
          wordWrap: 'normal'
        }}
        codeTagProps={{
          style: {
            whiteSpace: 'pre',
            wordBreak: 'normal',
            wordWrap: 'normal',
            overflowWrap: 'normal'
          }
        }}
        {...props}
      >
        {String(children).replace(/\n$/, '')}
      </Highlighter>
    </div>
  );
}
