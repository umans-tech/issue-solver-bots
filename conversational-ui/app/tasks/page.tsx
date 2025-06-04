'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Skeleton } from '../../components/ui/skeleton';
import { TaskHeader } from '../../components/task-header';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import { 
  Search,
  Filter,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  GitBranch,
  Database,
  Zap,
  FolderOpen
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

  // Filter processes based on search and filters
  const filteredProcesses = processes.filter(process => {
    const matchesSearch = !searchTerm || 
      process.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (process.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (process.description || '').toLowerCase().includes(searchTerm.toLowerCase());
    
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

  // Function to format task type into a readable title
  const getTaskTitle = (data: ProcessData) => {
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

  return (
    <div className="flex flex-col min-w-0 h-dvh bg-background">
      <TaskHeader />

      <div className="flex-1 overflow-auto">
        <div className="container mx-auto py-8 px-4">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Tasks & Processes</h1>
            <div className="flex items-center gap-4">
              <p className="text-muted-foreground">
                Monitor and manage all processes in your current workspace
              </p>
              {session?.user?.selectedSpace && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <FolderOpen className="h-3 w-3" />
                  {session.user.selectedSpace.name}
                </Badge>
              )}
            </div>
            {!loading && (
              <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                <span>{totalCount} tasks</span>
                <span>•</span>
                <span>{groupCount} categories</span>
              </div>
            )}
          </div>

          {/* Filters */}
          <div className="mb-6 flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search tasks by ID, title, or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[140px]">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="connected">Connected</SelectItem>
                  <SelectItem value="indexed">Indexed</SelectItem>
                </SelectContent>
              </Select>

              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[140px]">
                  <Activity className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {processTypes.map(type => (
                    <SelectItem key={type} value={type}>
                      {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

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
                <CardTitle>
                  {!session?.user?.selectedSpace?.knowledgeBaseId
                    ? 'No Knowledge Base Connected'
                    : 'No Tasks Found'
                  }
                </CardTitle>
                <CardDescription>
                  {searchTerm || statusFilter !== 'all' || typeFilter !== 'all'
                      ? 'No tasks match your current filters. Try adjusting your search criteria.'
                      : !session?.user?.selectedSpace?.knowledgeBaseId
                          ? 'Connect a repository to your space to start seeing tasks and processes.'
                          : `No tasks have been created yet in the "${session.user.selectedSpace.name} space".`
                  }
                </CardDescription>
              </CardHeader>
            </Card>
          ) : (
            <div className="space-y-8">
              {Object.entries(groupedProcesses).map(([groupType, groupProcesses]) => {
                const { icon, label, color } = getGroupHeaderInfo(groupType);
                
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
                                  </div>
                                </CardHeader>
                                
                                <CardContent className="pt-0">
                                  {process.description && (
                                    <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                                      {process.description}
                                    </p>
                                  )}
                                  
                                  <div className="flex justify-between items-center text-xs text-muted-foreground">
                                    <span>Created {getRelativeTime(process.createdAt)}</span>
                                    {process.updatedAt && process.updatedAt !== process.createdAt && (
                                      <span>Updated {getRelativeTime(process.updatedAt)}</span>
                                    )}
                                  </div>
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