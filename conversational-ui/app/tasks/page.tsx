'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Skeleton } from '../../components/ui/skeleton';
import { TaskHeader } from '../../components/task-header';
import { 
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  GitBranch,
  Database,
  Zap,
  Activity,
  ExternalLink
} from 'lucide-react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useSession } from 'next-auth/react';

interface ProcessData {
  id: string;
  status: string;
  title?: string;
  description?: string;
  createdAt?: string;
  updatedAt?: string;
  processType?: string;
  type?: string;
  events?: Array<{
    id: string;
    type: string;
    occurred_at?: string;
    data?: any;
    // Issue resolution specific fields
    issue?: {
      title?: string;
      description: string;
    };
    pr_url?: string;
    pr_number?: string;
  }>;
}

export default function TasksPage() {
  const { data: session } = useSession();
  const [processes, setProcesses] = useState<ProcessData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  useEffect(() => {
    async function fetchProcesses() {
      try {
        setLoading(true);
        
        // Build query parameters including knowledge_base_id if available
        const queryParams = new URLSearchParams();
        if (session?.user?.selectedSpace?.knowledgeBaseId) {
          queryParams.set('knowledge_base_id', session.user.selectedSpace.knowledgeBaseId);
        }
        
        const response = await fetch(`/api/processes?${queryParams.toString()}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch processes: ${response.statusText}`);
        }
        
        const data = await response.json();
        setProcesses(data.processes || []);
        setError(null);
      } catch (err) {
        console.error('Error fetching processes:', err);
        setError(err instanceof Error ? err.message : 'Failed to load tasks');
      } finally {
        setLoading(false);
      }
    }

    // Only fetch if we have session data and a knowledge base ID
    if (session && session?.user?.selectedSpace?.knowledgeBaseId) {
      fetchProcesses();
    } else if (session && !session?.user?.selectedSpace?.knowledgeBaseId) {
      // If we have a session but no knowledge base ID, set empty processes and stop loading
      setProcesses([]);
      setLoading(false);
    }
  }, [session?.user?.selectedSpace?.knowledgeBaseId]);

  // Function to format task type into a readable title
  const getTaskTitle = (data: ProcessData) => {
    // For issue resolution tasks, try to get the actual issue title from events
    if ((data.type === 'issue_resolution' || data.processType === 'issue_resolution') && data.events) {
      const issueRequestedEvent = data.events.find(event => 
        event.type === 'issue_resolution_requested' || event.type === 'IssueResolutionRequested'
      );
      
      if (issueRequestedEvent?.data?.issue?.title) {
        return issueRequestedEvent.data.issue.title;
      }
      
      // Also check the direct issue field structure
      if (issueRequestedEvent?.issue?.title) {
        return issueRequestedEvent.issue.title;
      }
    }
    
    if (data.type) {
      const formattedType = data.type
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      return `${formattedType} Task`;
    }
    
    if (data.processType) {
      const formattedType = data.processType
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      return `${formattedType} Task`;
    }
    
    if (data.title) {
      return data.title;
    }
    
    return `Task ${data.id.slice(0, 8)}...`;
  };

  // Filter processes based on search and filters
  const filteredProcesses = processes.filter(process => {
    const computedTitle = getTaskTitle(process);
    const matchesSearch = !searchTerm || 
      process.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (process.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (process.description || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      computedTitle.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || process.status === statusFilter;
    
    const matchesType = typeFilter === 'all' || 
      process.processType === typeFilter || 
      process.type === typeFilter;

    return matchesSearch && matchesStatus && matchesType;
  });

  // Group processes by type
  const groupedProcesses = filteredProcesses.reduce((groups, process) => {
    const processType = process.processType || process.type || 'unknown';
    if (!groups[processType]) {
      groups[processType] = [];
    }
    groups[processType].push(process);
    return groups;
  }, {} as Record<string, ProcessData[]>);

  // Get unique process types for filter
  const processTypes = Array.from(new Set(
    processes.map(p => p.processType || p.type).filter(Boolean)
  )) as string[];

  // Function to get process type with icon
  const getProcessTypeWithIcon = (processType?: string, type?: string) => {
    const processTypeValue = processType || type || 'unknown';
    
    switch (processTypeValue.toLowerCase()) {
      case 'issue_resolution':
      case 'issue_resolution_requested':
        return {
          icon: <Zap className="h-4 w-4" />,
          label: 'Issue Resolution',
          color: 'bg-purple-500/10 text-purple-600 border-purple-500/20'
        };
      case 'code_repository_connected':
      case 'repository':
        return {
          icon: <GitBranch className="h-4 w-4" />,
          label: 'Repository',
          color: 'bg-blue-500/10 text-blue-600 border-blue-500/20'
        };
      case 'code_repository_indexed':
      case 'indexing':
        return {
          icon: <Database className="h-4 w-4" />,
          label: 'Indexing',
          color: 'bg-green-500/10 text-green-600 border-green-500/20'
        };
      default:
        return {
          icon: <Activity className="h-4 w-4" />,
          label: processTypeValue.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          color: 'bg-gray-500/10 text-gray-600 border-gray-500/20'
        };
    }
  };

  // Function to get group header info
  const getGroupHeaderInfo = (groupType: string) => {
    const { icon, label, color } = getProcessTypeWithIcon(groupType);
    return { icon, label, color };
  };

  // Function to determine status badge with icon
  const getStatusBadgeWithIcon = (status?: string) => {
    if (!status) return {
      badge: <Badge variant="outline" className="flex items-center gap-1">
        <AlertTriangle className="h-3 w-3" />
        Unknown
      </Badge>,
      color: 'border-gray-200'
    };
    
    switch (status.toLowerCase()) {
      case 'completed':
      case 'success':
      case 'indexed':
      case 'connected':
        return {
          badge: <Badge className="bg-green-500 text-white flex items-center gap-1">
            <CheckCircle className="h-3 w-3" />
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Badge>,
          color: 'border-green-200 hover:border-green-300'
        };
      case 'failed':
      case 'error':
        return {
          badge: <Badge className="bg-red-500 text-white flex items-center gap-1">
            <XCircle className="h-3 w-3" />
            Failed
          </Badge>,
          color: 'border-red-200 hover:border-red-300'
        };
      case 'in_progress':
      case 'running':
      case 'indexing':
      case 'requested':
        return {
          badge: <Badge className="bg-blue-500 text-white flex items-center gap-1">
            <Clock className="h-3 w-3 animate-pulse" />
            In Progress
          </Badge>,
          color: 'border-blue-200 hover:border-blue-300'
        };
      default:
        return {
          badge: <Badge variant="outline" className="flex items-center gap-1">
            <Activity className="h-3 w-3" />
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Badge>,
          color: 'border-gray-200 hover:border-gray-300'
        };
    }
  };

  // Function to format date
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  // Function to get relative time
  const getRelativeTime = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInDays < 7) return `${diffInDays}d ago`;
    return formatDate(dateString);
  };

  // Get total count
  const totalCount = filteredProcesses.length;
  const groupCount = Object.keys(groupedProcesses).length;

  // Function to get group priority (lower number = higher priority)
  const getGroupPriority = (groupType: string) => {
    switch (groupType.toLowerCase()) {
      case 'issue_resolution':
        return 1;
      case 'code_repository_integration':
        return 2;
      default:
        return 3;
    }
  };

  // Function to check if a group is code repository integration
  const isCodeRepoGroup = (groupType: string) => {
    return groupType.toLowerCase() === 'code_repository_integration';
  };

  // Function to get PR info from events
  const getPRInfo = (data: ProcessData) => {
    if (!data.events) return null;
    
    const completedEvent = data.events.find(event => 
      event.type === 'issue_resolution_completed'
    );
    
    if (completedEvent?.pr_url && completedEvent?.pr_number) {
      return {
        url: completedEvent.pr_url,
        number: completedEvent.pr_number
      };
    }
    
    return null;
  };

  return (
    <div className="flex flex-col min-w-0 h-dvh bg-background">
      <TaskHeader 
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        typeFilter={typeFilter}
        onTypeFilterChange={setTypeFilter}
        processTypes={processTypes}
        totalCount={totalCount}
        groupCount={groupCount}
        loading={loading}
      />

      <div className="flex-1 overflow-auto">
        <div className="container mx-auto py-6 px-4 lg:px-6">
          {/* Content */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-5 w-3/4 mb-2" />
                    <Skeleton className="h-4 w-1/2" />
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-2/3" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : error ? (
            <Card className="border-red-200">
              <CardHeader>
                <CardTitle className="text-red-500">Error Loading Tasks</CardTitle>
                <CardDescription>{error}</CardDescription>
              </CardHeader>
            </Card>
          ) : Object.keys(groupedProcesses).length === 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>No Tasks Found</CardTitle>
                <CardDescription>
                  {searchTerm || statusFilter !== 'all' || typeFilter !== 'all'
                      ? 'No tasks match your current filters. Try adjusting your search criteria.'
                      : 'No tasks have been created yet in this workspace.'
                  }
                </CardDescription>
              </CardHeader>
            </Card>
          ) : (
            <div className="space-y-8">
              {Object.entries(groupedProcesses)
                .sort(([a], [b]) => getGroupPriority(a) - getGroupPriority(b))
                .map(([groupType, groupProcesses]) => {
                const { icon, label, color } = getGroupHeaderInfo(groupType);
                const isCodeRepo = isCodeRepoGroup(groupType);
                
                return (
                  <motion.div
                    key={groupType}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className="space-y-4"
                  >
                    {/* Group Header */}
                    <div className="flex items-center gap-3 pb-2 border-b border-border">
                      <div className={`p-2 rounded-md ${color}`}>
                        {icon}
                      </div>
                      <div>
                        <h2 className="text-xl font-semibold">{label}</h2>
                        <p className="text-sm text-muted-foreground">
                          {groupProcesses.length} {groupProcesses.length === 1 ? 'task' : 'tasks'}
                        </p>
                      </div>
                    </div>

                    {/* Group Content */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {groupProcesses.map((process, index) => {
                        const { badge, color: statusColor } = getStatusBadgeWithIcon(process.status);
                        const { icon: typeIcon, label: typeLabel, color: typeColor } = getProcessTypeWithIcon(process.processType, process.type);
                        const prInfo = getPRInfo(process);
                        
                        return (
                          <motion.div
                            key={process.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3, delay: index * 0.05 }}
                          >
                            <Link href={`/tasks/${process.id}`}>
                              <Card className={`cursor-pointer transition-all duration-200 hover:shadow-md ${statusColor}`}>
                                <CardHeader className="pb-3">
                                  <div className="flex justify-between items-start mb-2">
                                    <div className="flex-1 min-w-0">
                                      <CardTitle className="text-lg truncate">
                                        {getTaskTitle(process)}
                                      </CardTitle>
                                      <CardDescription className="text-xs font-mono text-muted-foreground mt-1">
                                        {process.id.slice(0, 8)}...
                                      </CardDescription>
                                    </div>
                                    {badge}
                                  </div>
                                  
                                  <div className="flex items-center gap-2">
                                    <Badge variant="outline" className={`${typeColor} flex items-center gap-1`}>
                                      {typeIcon}
                                      <span className="text-xs">{typeLabel}</span>
                                    </Badge>
                                    {prInfo && (
                                      <span
                                        onClick={(e) => {
                                          e.preventDefault();
                                          e.stopPropagation();
                                          window.open(prInfo.url, '_blank', 'noopener,noreferrer');
                                        }}
                                        role="link"
                                        className="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-1 transition-colors cursor-pointer"
                                      >
                                        <ExternalLink className="h-3 w-3" />
                                        PR #{prInfo.number}
                                      </span>
                                    )}
                                  </div>
                                </CardHeader>
                                
                                <CardContent className="pt-0">
                                  {process.description && (
                                    <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                                      {process.description}
                                    </p>
                                  )}
                                  
                                  {process.createdAt && getRelativeTime(process.createdAt) !== 'Unknown' && (
                                    <div className="flex justify-between items-center text-xs text-muted-foreground">
                                      <span>Created {getRelativeTime(process.createdAt)}</span>
                                      {process.updatedAt && process.updatedAt !== process.createdAt && (
                                        <span>Updated {getRelativeTime(process.updatedAt)}</span>
                                      )}
                                    </div>
                                  )}
                                </CardContent>
                              </Card>
                            </Link>
                          </motion.div>
                        );
                      })}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 