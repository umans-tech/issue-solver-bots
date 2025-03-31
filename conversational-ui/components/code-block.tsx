'use client';

import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { useTheme } from 'next-themes';

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
  
  // For actual code blocks (with triple backticks)
  const Highlighter = SyntaxHighlighter as any;
  return (
    <div className="relative w-full overflow-hidden">
      <Highlighter
        style={resolvedTheme === 'dark' ? vscDarkPlus : vs}
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
