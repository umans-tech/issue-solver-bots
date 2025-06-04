'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Skeleton } from '../../../components/ui/skeleton';
import { TaskHeader } from '../../../components/task-header';
import { ProcessTimelineView } from '../../../components/process-timeline-view';
import { Button } from '../../../components/ui/button';
import { CopyIcon } from '../../../components/icons';
import { toast } from 'sonner';
import { Markdown } from '../../../components/markdown';
import { 
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel
} from '../../../components/ui/alert-dialog';

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
    
    const CheckIcon = () => (
      <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
    );
    
    switch (status.toLowerCase()) {
      case 'completed':
      case 'success':
        return (
          <Badge className="bg-green-500 text-white flex items-center gap-1">
            <CheckIcon />
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
            <CheckIcon />
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
        return (
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        );
      case 'testing':
        return (
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
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

  return (
    <div className="flex flex-col min-w-0 h-dvh bg-background">
      <TaskHeader />

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
                            <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
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
                          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
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
                          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
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
                    
                    {processData.status === 'in_progress' && (
                      <div className="flex items-center gap-2 text-blue-500 mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <svg 
                          className="animate-spin h-4 w-4" 
                          xmlns="http://www.w3.org/2000/svg" 
                          fill="none" 
                          viewBox="0 0 24 24"
                        >
                          <circle 
                            className="opacity-25" 
                            cx="12" 
                            cy="12" 
                            r="10" 
                            stroke="currentColor" 
                            strokeWidth="4"
                          ></circle>
                          <path 
                            className="opacity-75" 
                            fill="currentColor" 
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          ></path>
                        </svg>
                        <span className="font-medium">Task is currently in progress...</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Issue Information Card - Only show for issue resolution tasks */}
              {(processData.type === 'issue_resolution' || processData.processType === 'issue_resolution') && getIssueInfo() && (
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                      Issue Details
                    </CardTitle>
                    <CardDescription>
                      Information about the issue being resolved
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {getIssueInfo()?.title && (
                        <div>
                          <h4 className="font-semibold text-sm text-muted-foreground mb-2">Issue Title</h4>
                          <p className="text-lg font-medium">{getIssueInfo()?.title}</p>
                        </div>
                      )}
                      
                      <div>
                        <h4 className="font-semibold text-sm text-muted-foreground mb-2">Issue Description</h4>
                        <div className="prose prose-sm max-w-none">
                          <Markdown>{getIssueInfo()?.description || 'No description provided'}</Markdown>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Repository Information Card - Show only for repository integration tasks */}
              {isRepositoryTask() && (repoInfo?.connected || getRepoInfoFromEvents()) && (
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
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
                              <CopyIcon size={16} />
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
                                  <CopyIcon size={16} />
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
                      <CopyIcon size={16} />
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