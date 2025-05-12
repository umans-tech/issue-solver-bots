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
  }>;
  result?: any;
  error?: string;
  processType?: string;
  type?: string;
}

export default function TaskPage() {
  const params = useParams();
  const processId = params?.processId as string;
  const [processData, setProcessData] = useState<ProcessData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isErrorDialogOpen, setIsErrorDialogOpen] = useState(false);

  useEffect(() => {
    async function fetchProcessData() {
      try {
        setLoading(true);
        const response = await fetch(`/api/processes/${processId}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch process data: ${response.statusText}`);
        }
        
        const data = await response.json();
        setProcessData(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching process data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load task data');
      } finally {
        setLoading(false);
      }
    }

    if (processId) {
      fetchProcessData();
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
    
    switch (status.toLowerCase()) {
      case 'completed':
      case 'success':
        return <Badge className="bg-green-500 text-white">Completed</Badge>;
      case 'failed':
      case 'error':
        return <Badge className="bg-red-500 text-white">Failed</Badge>;
      case 'in_progress':
      case 'running':
        return <Badge className="bg-blue-500 text-white">In Progress</Badge>;
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
                    <div>
                      <CardTitle>{getTaskTitle(processData)}</CardTitle>
                      <CardDescription>Process ID: {processData.id}</CardDescription>
                      {processData.processType && (
                        <Badge variant="outline" className="mt-2">
                          {processData.processType}
                        </Badge>
                      )}
                    </div>
                    <div className="flex flex-col items-end">
                      {getStatusBadge(processData.status)}
                      {processData.status?.toLowerCase() === 'completed' && 
                       processData.events?.some(event => 
                         event.type === 'issue_resolution_completed'
                       ) && (
                        <a 
                          href={processData.events.find(e => e.type === 'issue_resolution_completed')?.pr_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-sm text-blue-500 hover:text-blue-700 mt-2 flex items-center"
                        >
                          View PR #{processData.events.find(e => e.type === 'issue_resolution_completed')?.pr_number}
                          <svg 
                            className="ml-1 h-3 w-3" 
                            xmlns="http://www.w3.org/2000/svg" 
                            fill="none" 
                            viewBox="0 0 24 24" 
                            stroke="currentColor"
                          >
                            <path 
                              strokeLinecap="round" 
                              strokeLinejoin="round" 
                              strokeWidth={2} 
                              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" 
                            />
                          </svg>
                        </a>
                      )}
                      {processData.status?.toLowerCase() === 'failed' && 
                       processData.events?.some(event => 
                         event.type === 'issue_resolution_failed'
                       ) && (
                        <a 
                          onClick={() => setIsErrorDialogOpen(true)}
                          className="text-sm text-red-500 hover:text-red-700 mt-2 flex items-center cursor-pointer"
                        >
                          View Error Details
                          <svg 
                            className="ml-1 h-3 w-3" 
                            xmlns="http://www.w3.org/2000/svg" 
                            fill="none" 
                            viewBox="0 0 24 24" 
                            stroke="currentColor"
                          >
                            <path 
                              strokeLinecap="round" 
                              strokeLinejoin="round" 
                              strokeWidth={2} 
                              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" 
                            />
                          </svg>
                        </a>
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
                      <div className="flex items-center gap-2 text-blue-500">
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
                        <span>Task is currently in progress...</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

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