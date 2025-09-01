'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { useProcessMessages } from '../../../hooks/use-process-messages';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Skeleton } from '../../../components/ui/skeleton';
import { SharedHeader } from '../../../components/shared-header';
import { ProcessTimelineView } from '../../../components/process-timeline-view';
import { Button } from '../../../components/ui/button';
import { Copy } from 'lucide-react';
import { toast } from 'sonner';
import { Markdown } from '../../../components/markdown';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../../lib/utils';
import { DiffView } from '../../../components/diffview';
import { TodoDisplay } from '../../../components/todo-display';
import { 
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel
} from '../../../components/ui/alert-dialog';
import { 
  Check, 
  Code, 
  ExternalLink, 
  AlertCircle, 
  Loader2,
  ChevronDown,
  Settings,
  User,
  Bot,
  Wrench,
  Terminal,
  Search,
  Globe,
  FileText,
  Edit3,
  PenTool,
  BookOpen
} from 'lucide-react';

interface ProcessData {
  id: string;
  status: string;
  title?: string;
  description?: string;
  createdAt?: string;
  updatedAt?: string;
  events?: Array<{
    id: string;
    type: string;
    timestamp?: string;
    occurred_at?: string;
    data?: any;
    reason?: string;
    error_message?: string;
    pr_url?: string;
    pr_number?: number;
    // Issue resolution specific fields
    issue?: {
      title?: string;
      description: string;
    };
    // Repository specific fields
    url?: string;
    knowledge_base_id?: string;
    branch?: string;
    commit_sha?: string;
  }>;
  result?: any;
  error?: string;
  processType?: string;
  type?: string;
}

interface RepoInfo {
  connected: boolean;
  url?: string;
  knowledge_base_id?: string;
  branch?: string;
  commit_sha?: string;
  status?: string;
}

export default function TaskPage() {
  const params = useParams();
  const processId = params?.processId as string;
  const [processData, setProcessData] = useState<ProcessData | null>(null);
  const [repoInfo, setRepoInfo] = useState<RepoInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isErrorDialogOpen, setIsErrorDialogOpen] = useState(false);
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(true);
  
  // Use the polling hook for real-time message updates
  const { 
    messages, 
    loading: messagesLoading, 
    error: messagesError 
  } = useProcessMessages(processId, 3000, !!processId);

  // Animation variants for collapsible description
  const descriptionVariants = {
    collapsed: {
      height: 0,
      opacity: 0,
      marginTop: 0,
      marginBottom: 0,
    },
    expanded: {
      height: 'auto',
      opacity: 1,
      marginTop: '1rem',
      marginBottom: '0.5rem',
    },
  };

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        
        // Fetch process data
        const processResponse = await fetch(`/api/processes/${processId}`);
        if (!processResponse.ok) {
          const errorText = await processResponse.text();
          console.error('Process API error:', errorText);
          throw new Error(`Failed to fetch process data: ${processResponse.status} ${processResponse.statusText}`);
        }
        const processData = await processResponse.json();
        setProcessData(processData);
        
        // Fetch repository information for any task that might have repository data
        try {
          const repoResponse = await fetch('/api/repo');
          if (repoResponse.ok) {
            const repoData = await repoResponse.json();
            setRepoInfo(repoData);
          }
        } catch (repoError) {
          console.warn('Could not fetch repository information:', repoError);
          // Don't fail the whole page if repo info can't be fetched
        }

        // Note: Process messages are now handled by the useProcessMessages hook
        
        setError(null);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load task data');
      } finally {
        setLoading(false);
      }
    }

    if (processId) {
      fetchData();
    }
  }, [processId]);

  // Function to format date strings
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  // Function to format task type into a readable title
  const getTaskTitle = (data: ProcessData) => {
    // For issue resolution tasks, use the actual issue title
    if (data.type === 'issue_resolution' || data.processType === 'issue_resolution') {
      const issueInfo = getIssueInfo();
      if (issueInfo?.title) {
        return issueInfo.title;
      }
    }
    
    // Use type field if available
    if (data.type) {
      // Convert snake_case to Title Case
      const formattedType = data.type
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      
      return `${formattedType} Task`;
    }
    
    // Fallback to processType if available
    if (data.processType) {
      const formattedType = data.processType
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      
      return `${formattedType} Task`;
    }
    
    // If title is available, use that
    if (data.title) {
      return data.title;
    }
    
    // Last resort, use Task ID
    return `Task ${data.id}`;
  };

  // Function to determine badge color based on status
  const getStatusBadge = (status?: string) => {
    if (!status) return <Badge variant="outline">Unknown</Badge>;
    
    switch (status.toLowerCase()) {
      case 'completed':
      case 'success':
        return (
          <Badge className="bg-green-500 text-white flex items-center gap-1">
            <Check className="h-3 w-3" />
            Completed
          </Badge>
        );
      case 'failed':
      case 'error':
        return <Badge className="bg-red-500 text-white">Failed</Badge>;
      case 'in_progress':
      case 'running':
        return <Badge className="bg-blue-500 text-white">In Progress</Badge>;
      case 'indexed':
        return (
          <Badge className="bg-green-500 text-white flex items-center gap-1">
            <Check className="h-3 w-3" />
            Indexed
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  // Get failure details from events
  const getFailureDetails = () => {
    if (!processData?.events) return { reason: 'Unknown reason', errorMessage: 'No error details available' };
    
    const failedEvent = processData.events.find(event => event.type === 'issue_resolution_failed');
    
    return {
      reason: failedEvent?.reason || 'Unknown reason',
      errorMessage: failedEvent?.error_message || 'No error details available'
    };
  };

  // Function to get process type icon
  const getProcessTypeIcon = (type?: string) => {
    switch (type) {
      case 'code_review':
        return <Code className="h-4 w-4" />;
      case 'testing':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return null;
    }
  };

  // Get issue information from events
  const getIssueInfo = () => {
    if (!processData?.events) return null;
    
    const issueRequestedEvent = processData.events.find(event => 
      event.type === 'issue_resolution_requested'
    );
    
    return issueRequestedEvent?.issue || null;
  };

  // Get repository information from events
  const getRepoInfoFromEvents = () => {
    if (!processData?.events) return null;
    
    const repoConnectedEvent = processData.events.find(event => 
      event.type === 'repository_connected'
    );
    
    const repoIndexedEvent = processData.events
      .filter(event => event.type === 'repository_indexed')
      .sort((a, b) => new Date(b.occurred_at || '').getTime() - new Date(a.occurred_at || '').getTime())[0];
    
    const indexationRequestedEvent = processData.events
      .filter(event => event.type === 'repository_indexation_requested')
      .sort((a, b) => new Date(b.occurred_at || '').getTime() - new Date(a.occurred_at || '').getTime())[0];
    
    if (!repoConnectedEvent) return null;
    
    return {
      url: repoConnectedEvent.url,
      knowledge_base_id: repoConnectedEvent.knowledge_base_id,
      branch: repoIndexedEvent?.branch,
      commit_sha: repoIndexedEvent?.commit_sha,
      // Timing information
      connected_at: repoConnectedEvent.occurred_at,
      indexation_started_at: indexationRequestedEvent?.occurred_at,
      indexation_completed_at: repoIndexedEvent?.occurred_at
    };
  };

  // Check if this is a repository integration task
  const isRepositoryTask = () => {
    if (!processData?.events) return false;
    
    // Check if any repository-related events exist
    const repoEvents = ['repository_connected', 'repository_indexation_requested', 'repository_indexed', 'repository_integration_failed'];
    return processData.events.some(event => repoEvents.includes(event.type));
  };

  // Get message type icon and color
  const getMessageTypeDetails = (message: any) => {
    const messageType = message.type;
    const role = message.payload?.role;
    const payload = message.payload;
    
    // Handle different message types based on cudu API structure
    if (messageType === 'SystemMessage' || role === 'system') {
      return {
        icon: <Settings className="h-4 w-4" />,
        color: 'text-muted-foreground',
        bgColor: 'bg-muted/10',
        label: 'System'
      };
    }
    
    // Check for tool calls (ToolUseBlock with id, name, input) - these will be grouped with results
    if (Array.isArray(payload?.content) && payload.content.some((block: any) => 
        block?.id && block?.name && block?.input)) {
      return {
        icon: <Wrench className="h-4 w-4" />,
        color: 'text-blue-600',
        bgColor: 'bg-blue-600/10',
        label: 'Tool Call' // This will be bypassed by special rendering logic
      };
    }
    
    // Check for tool results (ToolResultBlock with tool_use_id) - skip these as they'll be grouped with calls
    if (Array.isArray(payload?.content) && payload.content.some((block: any) => 
        block?.tool_use_id)) {
      // Skip rendering separate label for tool results since they'll be shown with their tool calls
      return null;
    }
    
    // Check for result messages (ResultMessage type)
    if (messageType === 'ResultMessage' && payload?.result) {
      return {
        icon: <Wrench className="h-4 w-4" />,
        color: 'text-green-600',
        bgColor: 'bg-green-600/10',
        label: 'Tool Output'
      };
    }
    
    // Check for user messages
    if (messageType === 'UserMessage' || role === 'user') {
      return {
        icon: <User className="h-4 w-4" />,
        color: 'text-blue-500',
        bgColor: 'bg-blue-500/10',
        label: 'User'
      };
    }
    
    // Check for assistant messages (TextBlock with text field)
    if ((messageType === 'AssistantMessage' || role === 'assistant') && 
        (payload?.text || (Array.isArray(payload?.content) && payload.content.some((block: any) => block?.text)))) {
      return {
        icon: <Bot className="h-4 w-4" />,
        color: 'text-primary',
        bgColor: 'bg-primary/10',
        label: 'Assistant'
      };
    }
    
    // Default fallback for unrecognized types
    return {
      icon: <Wrench className="h-4 w-4" />,
      color: 'text-muted-foreground',
      bgColor: 'bg-muted/10',
      label: `Unknown (${messageType || 'No Type'})`
    };
  };

  // Get tool icon based on tool name
  const getToolIcon = (toolName: string) => {
    const lowerTool = toolName.toLowerCase();
    
    if (lowerTool.includes('bash') || lowerTool.includes('terminal')) {
      return <Terminal className="h-3 w-3" />;
    } else if (lowerTool.includes('search') || lowerTool.includes('grep')) {
      return <Search className="h-3 w-3" />;
    } else if (lowerTool.includes('web') || lowerTool.includes('fetch')) {
      return <Globe className="h-3 w-3" />;
    } else if (lowerTool.includes('read') || lowerTool.includes('notebook')) {
      return <BookOpen className="h-3 w-3" />;
    } else if (lowerTool.includes('edit') || lowerTool.includes('write')) {
      return <Edit3 className="h-3 w-3" />;
    } else if (lowerTool.includes('todo')) {
      return <PenTool className="h-3 w-3" />;
    } else if (lowerTool.includes('file') || lowerTool.includes('glob') || lowerTool.includes('ls')) {
      return <FileText className="h-3 w-3" />;
    } else {
      return <Wrench className="h-3 w-3" />;
    }
  };

  // Terminal output component for tool results
  const TerminalOutput = ({ content, isError, toolName }: { content: string; isError: boolean; toolName?: string }) => {
    const handleCopy = () => {
      navigator.clipboard.writeText(content);
      toast.success('Copied to clipboard!');
    };

    return (
      <div className="w-full rounded-lg overflow-hidden border dark:border-zinc-700 border-zinc-200">
        {/* Terminal header */}
        <div className="flex items-center justify-between px-3 py-2 bg-muted border-b dark:border-zinc-700 border-zinc-200">
          <div className="flex items-center gap-2 text-sm">
            <Terminal className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">{toolName || 'Terminal'}</span>
          </div>
          <div className="flex items-center gap-2">
            {isError ? (
              <span className="inline-flex items-center px-2 py-1 bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300 text-xs rounded">
                ❌ Error
              </span>
            ) : (
              <span className="inline-flex items-center px-2 py-1 bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300 text-xs rounded">
                ✅ Success
              </span>
            )}
            <Button
              onClick={handleCopy}
              size="icon"
              variant="ghost"
              className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
              aria-label="Copy output"
            >
              <Copy size={14} />
            </Button>
          </div>
        </div>
        
        {/* Terminal content */}
        <div className="bg-zinc-900 dark:bg-zinc-950 text-zinc-100 p-4 font-mono text-sm max-h-96 overflow-auto">
          <pre className="whitespace-pre-wrap break-words">{content}</pre>
        </div>
      </div>
    );
  };

  // Console command component for tool calls
  const ConsoleCommand = ({ command, description, toolName }: { command: string; description?: string; toolName?: string }) => {
    const handleCopy = () => {
      navigator.clipboard.writeText(command);
      toast.success('Command copied to clipboard!');
    };

    return (
      <div className="w-full rounded-lg overflow-hidden border dark:border-zinc-700 border-zinc-200">
        {/* Console header */}
        <div className="flex items-center justify-between px-3 py-2 bg-muted border-b dark:border-zinc-700 border-zinc-200">
          <div className="flex items-center gap-2 text-sm">
            <Terminal className="h-4 w-4 text-blue-600" />
            <span className="text-muted-foreground">{description || toolName || 'Command'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300 text-xs rounded">
              🔄 Executing
            </span>
            <Button
              onClick={handleCopy}
              size="icon"
              variant="ghost"
              className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
              aria-label="Copy command"
            >
              <Copy size={14} />
            </Button>
          </div>
        </div>
        
        {/* Console content */}
        <div className="bg-zinc-900 dark:bg-zinc-950 text-zinc-100 p-4 font-mono text-sm">
          <div className="flex items-center gap-2">
            <span className="text-green-400">$</span>
            <span className="text-zinc-100">{command}</span>
          </div>
        </div>
      </div>
    );
  };

  // GitHub-style diff display component for edit tool calls
  const DiffDisplay = ({ filePath, oldString, newString, toolName }: { 
    filePath: string; 
    oldString: string; 
    newString: string; 
    toolName?: string; 
  }) => {
    const handleCopyDiff = () => {
      const diffContent = `--- a/${filePath}\n+++ b/${filePath}\n${oldString.split('\n').map(line => `- ${line}`).join('\n')}\n${newString.split('\n').map(line => `+ ${line}`).join('\n')}`;
      navigator.clipboard.writeText(diffContent);
      toast.success('Diff copied to clipboard!');
    };

    return (
      <div className="w-full rounded-lg overflow-hidden border dark:border-zinc-700 border-zinc-200">
        {/* Diff header */}
        <div className="flex items-center justify-between px-3 py-2 bg-muted border-b dark:border-zinc-700 border-zinc-200">
          <div className="flex items-center gap-2 text-sm">
            <Edit3 className="h-4 w-4 text-purple-600" />
            <span className="text-muted-foreground">Editing: {filePath}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-1 bg-purple-100 dark:bg-purple-900/20 text-purple-800 dark:text-purple-300 text-xs rounded">
              ✏️ Modifying
            </span>
            <Button
              onClick={handleCopyDiff}
              size="icon"
              variant="ghost"
              className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
              aria-label="Copy diff"
            >
              <Copy size={14} />
            </Button>
          </div>
        </div>
        
        {/* GitHub-style diff content using existing DiffView component */}
        <div className="max-h-96 overflow-auto p-4 bg-background">
          <DiffView 
            oldContent={oldString || ''} 
            newContent={newString || ''} 
          />
        </div>
      </div>
    );
  };

  // Helper function to find tool result for a given tool call ID across all messages
  const findToolResultForCall = (toolCallId: string, allMessages: any[], currentMessageIndex: number) => {
    // Look in subsequent messages for the tool result
    for (let i = currentMessageIndex + 1; i < allMessages.length; i++) {
      const message = allMessages[i];
      if (Array.isArray(message.payload?.content)) {
        for (const block of message.payload.content) {
          if (block.tool_use_id === toolCallId) {
            return block;
          }
        }
      }
    }
    return null;
  };

  // Render message content with cross-message tool call grouping
  const renderMessageContent = (message: any, messageIndex: number, allMessages: any[]) => {
    const payload = message.payload;
    const messageType = message.type;
    const role = message.payload?.role;
    
    if (!payload) return null;

    // Handle content blocks
    if (Array.isArray(payload.content)) {
      return payload.content.map((block: any, index: number) => {
        const key = `block-${index}`;
        
        // Handle tool calls with potential results in later messages
        if (block.id && block.name && block.input) {
          const toolResult = findToolResultForCall(block.id, allMessages, messageIndex);
          
          // Special handling for TodoWrite - render without wrapper
          if (block.name === 'TodoWrite' && block.input.todos) {
            return (
              <div key={key} className="mb-4">
                <TodoDisplay 
                  todos={block.input.todos}
                  toolName={block.name}
                />
              </div>
            );
          }
          
          if (toolResult) {
            // Render grouped tool call with result
            let resultContent = 'Tool executed successfully';
            let isError = toolResult.is_error || false;
            
            if (toolResult.content) {
              if (typeof toolResult.content === 'string') {
                resultContent = toolResult.content;
              } else {
                resultContent = JSON.stringify(toolResult.content, null, 2);
              }
            }
            
            return (
              <div key={key} className="border rounded-lg mb-4 overflow-hidden">
                {/* Tool Call Header */}
                <div className="bg-gray-50 px-4 py-2 border-b">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-blue-600">🔧 Tool Call</span>
                    <span className="text-sm font-semibold">{block.name}</span>
                  </div>
                </div>
                
                {/* Tool Call Content */}
                <div className="p-4 bg-white">
                  {/* Special handling for Bash/Terminal commands */}
                  {block.name.toLowerCase() === 'bash' && block.input.command ? (
                    <ConsoleCommand 
                      command={block.input.command}
                      description={block.input.description}
                      toolName={block.name}
                    />
                  ) : 
                  /* Special handling for Edit tool calls */
                  block.name.toLowerCase() === 'edit' && block.input.file_path && 
                  (block.input.old_string || block.input.new_string) ? (
                    <DiffDisplay 
                      filePath={block.input.file_path}
                      oldString={block.input.old_string || ''}
                      newString={block.input.new_string || ''}
                      toolName={block.name}
                    />
                  ) :
                  /* Special handling for Todo tool calls */
                  block.name === 'TodoWrite' && block.input.todos ? (
                    <TodoDisplay 
                      todos={block.input.todos}
                      toolName={block.name}
                    />
                  ) : (
                    /* Default handling for other tools */
                    <div className="bg-muted/20 p-2 rounded text-xs">
                      <pre className="whitespace-pre-wrap">{JSON.stringify(block.input, null, 2)}</pre>
                    </div>
                  )}
                </div>
                
                {/* Tool Result */}
                <div className="border-t">
                  <div className="bg-gray-50 px-4 py-2">
                    <span className="text-sm font-medium text-green-600">📤 Tool Output</span>
                  </div>
                  <div className="p-4">
                    <TerminalOutput 
                      content={resultContent} 
                      isError={isError}
                      toolName="Output"
                    />
                  </div>
                </div>
              </div>
            );
          } else {
            // Tool call without result (still pending)
            return (
              <div key={key} className="border rounded-lg mb-4 overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 border-b">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-blue-600">🔧 Tool Call</span>
                    <span className="text-sm font-semibold">{block.name}</span>
                    <span className="text-xs text-orange-500 ml-auto">Pending...</span>
                  </div>
                </div>
                <div className="p-4">
                  {/* Special handling for Bash/Terminal commands */}
                  {block.name.toLowerCase() === 'bash' && block.input.command ? (
                    <ConsoleCommand 
                      command={block.input.command}
                      description={block.input.description}
                      toolName={block.name}
                    />
                  ) : 
                  /* Special handling for Edit tool calls */
                  block.name.toLowerCase() === 'edit' && block.input.file_path && 
                  (block.input.old_string || block.input.new_string) ? (
                    <DiffDisplay 
                      filePath={block.input.file_path}
                      oldString={block.input.old_string || ''}
                      newString={block.input.new_string || ''}
                      toolName={block.name}
                    />
                  ) :
                  /* Special handling for Todo tool calls */
                  block.name === 'TodoWrite' && block.input.todos ? (
                    <TodoDisplay 
                      todos={block.input.todos}
                      toolName={block.name}
                    />
                  ) : (
                    /* Default handling for other tools */
                    <div className="bg-muted/20 p-2 rounded text-xs">
                      <pre className="whitespace-pre-wrap">{JSON.stringify(block.input, null, 2)}</pre>
                    </div>
                  )}
                </div>
              </div>
            );
          }
        }
        
        // Handle text blocks
        if (block.text) {
          return (
            <div key={key}>
              <Markdown>{block.text}</Markdown>
            </div>
          );
        }
        
        // Skip tool results that have already been paired with tool calls
        if (block.tool_use_id) {
          // Check if this result was already rendered with its tool call
          for (let i = 0; i < messageIndex; i++) {
            const prevMessage = allMessages[i];
            if (Array.isArray(prevMessage.payload?.content)) {
              for (const prevBlock of prevMessage.payload.content) {
                if (prevBlock.id === block.tool_use_id) {
                  // This result was already rendered with its tool call
                  return null;
                }
              }
            }
          }
          
          // Orphaned tool result - render it standalone
          let resultContent = 'Tool executed successfully';
          let isError = block.is_error || false;
          
          if (block.content) {
            if (typeof block.content === 'string') {
              resultContent = block.content;
            } else {
              resultContent = JSON.stringify(block.content, null, 2);
            }
          }
          
          return (
            <div key={key} className="border rounded-lg mb-4 overflow-hidden">
              <div className="bg-gray-50 px-4 py-2">
                <span className="text-sm font-medium text-green-600">📤 Tool Output</span>
                <span className="text-xs text-orange-500 ml-2">(No matching call found)</span>
              </div>
              <div className="p-4">
                <TerminalOutput 
                  content={resultContent} 
                  isError={isError}
                  toolName="Output"
                />
              </div>
            </div>
          );
        }
        
        // Fallback for unknown block types
        return (
          <div key={key} className="text-sm text-muted-foreground">
            <pre className="whitespace-pre-wrap text-xs bg-muted/20 p-2 rounded">
              {JSON.stringify(block, null, 2)}
            </pre>
          </div>
        );
      }).filter(Boolean); // Remove null entries
    }

        // Handle ResultMessage with result field
    if (messageType === 'ResultMessage' && payload.result) {
      let resultContent = payload.result;
      if (typeof resultContent !== 'string') {
        resultContent = JSON.stringify(resultContent, null, 2);
      }
      
      return (
        <TerminalOutput 
          content={resultContent} 
          isError={false}
          toolName="Process Result"
        />
      );
    }

    // Handle SystemMessage with tools
    if (messageType === 'SystemMessage' || payload.role === 'system') {
      const tools = payload.tools || [];
      return (
        <div className="text-sm">
          <div className="text-muted-foreground mb-2">Initialisation</div>
          {tools.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {tools.map((tool: string, index: number) => (
                <span key={index} className="inline-flex items-center gap-1 px-2 py-1 bg-muted/30 rounded text-xs">
                  {getToolIcon(tool)}
                  {tool}
                </span>
              ))}
            </div>
          )}
        </div>
      );
    }

    // Handle direct text field (for backwards compatibility)
    if (payload.text) {
      const textContent = typeof payload.text === 'string' ? payload.text : JSON.stringify(payload.text);
      return (
        <div>
          <Markdown>{textContent}</Markdown>
        </div>
      );
    }

    // Handle simple string content
    if (typeof payload.content === 'string') {
      return (
        <div>
          <Markdown>{payload.content}</Markdown>
        </div>
      );
    }

    // Fallback for unhandled message types
    return (
      <div className="text-sm text-muted-foreground">
        <span>Unhandled message type: {messageType}</span>
      </div>
    );
  };

  return (
    <div className="flex flex-col min-w-0 h-dvh bg-background">
      <SharedHeader />

      <div className="flex-1 overflow-auto">
        <div className="container mx-auto py-8 px-4">
          {loading ? (
            <Card>
              <CardHeader>
                <Skeleton className="h-8 w-3/4 mb-2" />
                <Skeleton className="h-4 w-1/2" />
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
              </CardContent>
            </Card>
          ) : error ? (
            <Card className="border-red-200">
              <CardHeader>
                <CardTitle className="text-red-500">Error Loading Task</CardTitle>
                <CardDescription>{error}</CardDescription>
              </CardHeader>
            </Card>
          ) : processData ? (
            <>
              {/* Task Summary Card */}
              <Card className="mb-6">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <CardTitle className="text-2xl">{getTaskTitle(processData)}</CardTitle>
                        {getProcessTypeIcon(processData.processType || processData.type)}
                      </div>
                      <CardDescription className="font-mono text-sm">
                        Process ID: {processData.id}
                      </CardDescription>
                      <div className="flex items-center gap-2 mt-3">
                        {processData.processType && (
                          <Badge variant="outline" className="flex items-center gap-1">
                            {getProcessTypeIcon(processData.processType)}
                            <span className="text-xs">
                              {processData.processType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </span>
                          </Badge>
                        )}
                        {processData.type && processData.type !== processData.processType && (
                          <Badge variant="outline" className="flex items-center gap-1">
                            {getProcessTypeIcon(processData.type)}
                            <span className="text-xs">
                              {processData.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </span>
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-3">
                      <div className="flex items-center gap-2">
                        {getStatusBadge(processData.status)}
                        {processData.status === 'in_progress' && (
                          <div className="flex items-center gap-1 text-blue-500">
                            <Loader2 className="animate-spin h-4 w-4" />
                          </div>
                        )}
                      </div>
                      {processData.status?.toLowerCase() === 'completed' && 
                       processData.events?.some(event => 
                         event.type === 'issue_resolution_completed'
                       ) &&
                        <a 
                          href={processData.events.find(e => e.type === 'issue_resolution_completed')?.pr_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-sm text-blue-500 hover:text-blue-700 flex items-center gap-1 transition-colors"
                        >
                          <ExternalLink className="h-4 w-4" />
                          View PR #{processData.events.find(e => e.type === 'issue_resolution_completed')?.pr_number}
                        </a>
                      }
                      {processData.status?.toLowerCase() === 'failed' && 
                       processData.events?.some(event => 
                         event.type === 'issue_resolution_failed'
                       ) && (
                        <button 
                          onClick={() => setIsErrorDialogOpen(true)}
                          className="text-sm text-red-500 hover:text-red-700 flex items-center gap-1 transition-colors"
                        >
                          <AlertCircle className="h-4 w-4" />
                          View Error Details
                        </button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {processData.description && (
                      <div>
                        <h3 className="font-medium text-sm text-muted-foreground mb-1">Description</h3>
                        <p>{processData.description}</p>
                      </div>
                    )}
                    
                    {/* Timeline view instead of simple timestamps */}
                    {processData.events && processData.events.length > 0 ? (
                      <ProcessTimelineView events={processData.events} />
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h3 className="font-medium text-sm text-muted-foreground mb-1">Created</h3>
                          <p>{formatDate(processData.createdAt)}</p>
                        </div>
                        <div>
                          <h3 className="font-medium text-sm text-muted-foreground mb-1">Last Updated</h3>
                          <p>{formatDate(processData.updatedAt)}</p>
                        </div>
                      </div>
                    )}

                    {/* Issue Description (collapsible) - Only show for issue resolution tasks */}
                    {(processData.type === 'issue_resolution' || processData.processType === 'issue_resolution') && getIssueInfo() && (
                      <div className="space-y-2">
                        {/* Description header with toggle */}
                        <div 
                          className="flex items-center gap-2 cursor-pointer"
                          onClick={() => setIsDescriptionExpanded(!isDescriptionExpanded)}
                        >
                          <h3 className="font-medium text-sm text-muted-foreground">Description</h3>
                          <div className={cn("transition-transform", isDescriptionExpanded ? "rotate-180" : "")}>
                            <ChevronDown size={16} />
                          </div>
                        </div>

                        {/* Description content (collapsible) */}
                        <AnimatePresence initial={false}>
                          {isDescriptionExpanded && (
                            <motion.div
                              key="description-content"
                              initial="collapsed"
                              animate="expanded"
                              exit="collapsed"
                              variants={descriptionVariants}
                              transition={{ duration: 0.2, ease: 'easeInOut' }}
                              style={{ overflow: 'hidden' }}
                            >
                              <div>
                                <Markdown>{getIssueInfo()?.description || 'No description provided'}</Markdown>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    )}
                    
                    {processData.status === 'in_progress' && (
                      <div className="flex items-center gap-2 text-blue-500 mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <Loader2 className="animate-spin h-4 w-4" />
                        <span className="font-medium">Task is currently in progress...</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Agent Progress Card - Show process messages */}
              {messages.length > 0 && (
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Bot className="h-5 w-5" />
                      Agent Progress
                      {messages.length > 0 && !messagesError && (
                        <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-full">
                          Live • {messages.length} messages
                        </span>
                      )}
                    </CardTitle>
                    <CardDescription>
                      Step-by-step progress of the agent working on this task
                      {!messagesError && (
                        <span className="text-xs text-green-600 ml-2">
                          • Updates every 3 seconds
                        </span>
                      )}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {messages.map((message, index) => {
                        const messageDetails = getMessageTypeDetails(message);
                        
                        // Skip messages that return null (e.g., tool results that will be grouped)
                        if (!messageDetails) {
                          return null;
                        }
                        
                        const { icon, color, bgColor, label } = messageDetails;
                        
                        // Special handling for tool calls - render grouped display directly
                        if (Array.isArray(message.payload?.content) && 
                            message.payload.content.some((block: any) => block?.id && block?.name && block?.input)) {
                          return (
                            <div key={message.id || index} className="text-sm">
                              {renderMessageContent(message, index, messages)}
                            </div>
                          );
                        }
                        
                        // Regular message rendering
                        return (
                          <div key={message.id || index} className="flex gap-3">
                            <div className={cn("flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center", bgColor)}>
                              <div className={color}>
                                {icon}
                              </div>
                            </div>
                            <div className="flex-1 min-w-0">
                              {label && (
                                <div className={cn("text-sm font-medium mb-1", color)}>
                                  {label}
                                </div>
                              )}
                              <div className="text-sm">
                                {renderMessageContent(message, index, messages)}
                              </div>
                            </div>
                          </div>
                        );
                      }).filter(Boolean)}
                      
                      {messagesLoading && (
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Loader2 className="animate-spin h-4 w-4" />
                          <span className="text-sm">Loading messages...</span>
                        </div>
                      )}
                      
                      {messagesError && (
                        <div className="flex items-center gap-2 text-red-500 text-sm">
                          <AlertCircle className="h-4 w-4" />
                          <span>Error loading messages: {messagesError}</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Repository Information Card - Show only for repository integration tasks */}
              {isRepositoryTask() && (repoInfo?.connected || getRepoInfoFromEvents()) && (
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Code className="h-5 w-5" />
                      Repository Information
                    </CardTitle>
                    <CardDescription>
                      Connected repository and Git information
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {(repoInfo?.url || getRepoInfoFromEvents()?.url) && (
                        <div>
                          <h4 className="font-semibold text-sm text-muted-foreground mb-2">Repository URL</h4>
                          <div className="flex items-center gap-2">
                            <code className="bg-muted px-2 py-1 rounded text-sm flex-1">
                              {repoInfo?.url || getRepoInfoFromEvents()?.url}
                            </code>
                            <Button
                              onClick={() => {
                                navigator.clipboard.writeText(repoInfo?.url || getRepoInfoFromEvents()?.url || '');
                                toast.success('Repository URL copied to clipboard!');
                              }}
                              size="icon"
                              variant="ghost"
                              className="h-8 w-8 p-0"
                              aria-label="Copy repository URL"
                            >
                              <Copy size={16} />
                            </Button>
                          </div>
                        </div>
                      )}
                      
                      {/* Connection Status and Git Information */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {repoInfo?.status && (
                          <div>
                            <h4 className="font-semibold text-sm text-muted-foreground mb-2">Status</h4>
                            {getStatusBadge(repoInfo.status)}
                          </div>
                        )}
                        
                        {getRepoInfoFromEvents()?.connected_at && (
                          <div>
                            <h4 className="font-semibold text-sm text-muted-foreground mb-2">Connected Since</h4>
                            <span className="text-sm">{formatDate(getRepoInfoFromEvents()?.connected_at)}</span>
                          </div>
                        )}
                      </div>
                      
                      {/* Git Information */}
                      {(repoInfo?.branch || getRepoInfoFromEvents()?.branch) && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h4 className="font-semibold text-sm text-muted-foreground mb-2">Current Branch</h4>
                            <code className="bg-muted px-2 py-1 rounded text-sm block">
                              {repoInfo?.branch || getRepoInfoFromEvents()?.branch}
                            </code>
                          </div>
                          
                          {(repoInfo?.commit_sha || getRepoInfoFromEvents()?.commit_sha) && (
                            <div>
                              <h4 className="font-semibold text-sm text-muted-foreground mb-2">Latest Commit</h4>
                              <div className="flex items-center gap-2">
                                <code className="bg-muted px-2 py-1 rounded text-sm flex-1">
                                  {(repoInfo?.commit_sha || getRepoInfoFromEvents()?.commit_sha)?.substring(0, 8)}...
                                </code>
                                <Button
                                  onClick={() => {
                                    navigator.clipboard.writeText(repoInfo?.commit_sha || getRepoInfoFromEvents()?.commit_sha || '');
                                    toast.success('Commit SHA copied to clipboard!');
                                  }}
                                  size="icon"
                                  variant="ghost"
                                  className="h-8 w-8 p-0"
                                  aria-label="Copy commit SHA"
                                >
                                  <Copy size={16} />
                                </Button>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* Latest Indexation Information */}
                      {(getRepoInfoFromEvents()?.indexation_started_at || getRepoInfoFromEvents()?.indexation_completed_at) && (
                        <div>
                          <h4 className="font-semibold text-sm text-muted-foreground mb-3">Latest Indexation</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {getRepoInfoFromEvents()?.indexation_started_at && (
                              <div>
                                <h5 className="font-medium text-xs text-muted-foreground mb-1">Started</h5>
                                <span className="text-sm">{formatDate(getRepoInfoFromEvents()?.indexation_started_at)}</span>
                              </div>
                            )}
                            
                            {getRepoInfoFromEvents()?.indexation_completed_at && (
                              <div>
                                <h5 className="font-medium text-xs text-muted-foreground mb-1">Completed</h5>
                                <span className="text-sm">{formatDate(getRepoInfoFromEvents()?.indexation_completed_at)}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Error Dialog */}
              <AlertDialog open={isErrorDialogOpen} onOpenChange={setIsErrorDialogOpen}>
                <AlertDialogContent className="max-w-3xl">
                  <AlertDialogHeader>
                    <AlertDialogTitle className="text-red-500">Error Details</AlertDialogTitle>
                    <AlertDialogDescription>
                      The issue resolution task failed with the following details:
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  
                  <div className="mt-4 bg-black rounded-md p-4 text-white font-mono text-sm overflow-auto max-h-96 relative">
                    <Button
                      onClick={() => {
                        const { reason, errorMessage } = getFailureDetails();
                        const textToCopy = `Failure Reason: ${reason}\n\nError Message:\n${errorMessage}`;
                        navigator.clipboard.writeText(textToCopy);
                        toast.success('Error details copied to clipboard!');
                      }}
                      size="icon"
                      variant="ghost"
                      className="absolute top-3 right-3 z-10 h-8 w-8 p-0 text-gray-400 hover:text-white hover:bg-gray-700"
                      aria-label="Copy error details"
                    >
                      <Copy size={16} />
                    </Button>
                    
                    <div className="mb-4">
                      <span className="text-red-400">Failure Reason:</span> 
                      <span className="text-yellow-300 ml-2">{getFailureDetails().reason}</span>
                    </div>
                    
                    <div>
                      <span className="text-red-400">Error Message:</span>
                      <pre className="whitespace-pre-wrap text-green-300 mt-2">
                        {getFailureDetails().errorMessage}
                      </pre>
                    </div>
                  </div>
                  
                  <AlertDialogFooter className="mt-4">
                    <AlertDialogCancel>Close</AlertDialogCancel>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>

              {/* Task Result Section - Will be expanded in the next step */}
              {processData.result && (
                <Card>
                  <CardHeader>
                    <CardTitle>Task Result</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="bg-muted p-4 rounded-md overflow-x-auto">
                      {JSON.stringify(processData.result, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>No Data Available</CardTitle>
                <CardDescription>Could not find information for this task.</CardDescription>
              </CardHeader>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}