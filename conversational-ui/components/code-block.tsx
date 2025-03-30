'use client';

import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';

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
  // Check if this is a code block with a language specified
  const match = /language-(\w+)/.exec(className || '');
  const language = match?.[1];
  
  // For inline code or paths
  if (inline || !language) {
    return (
      <code
        className="text-sm bg-zinc-100 dark:bg-zinc-800 py-0.5 px-1 rounded-md"
        {...props}
      >
        {children}
      </code>
    );
  }
  
  // For actual code blocks (with triple backticks)
  const Highlighter = SyntaxHighlighter as any; // Cast to any
  return (
    <Highlighter
      style={vscDarkPlus}
      language={language}
      PreTag="div"
      className="text-sm w-full block overflow-x-auto rounded-xl"
      {...props}
    >
      {String(children).replace(/\n$/, '')}
    </Highlighter>
  );
}
