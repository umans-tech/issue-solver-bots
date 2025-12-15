'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useSession } from 'next-auth/react';
import {
  Activity,
  AlertTriangle,
  ArrowUp,
  BookOpen,
  CheckCircle,
  ClipboardList,
  Clock,
  Database,
  ExternalLink,
  GitBranch,
  XCircle,
  Zap,
} from 'lucide-react';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { TaskHeader } from '@/components/task-header';

interface ProcessEvent {
  id: string;
  type: string;
  occurred_at?: string;
  data?: any;
  issue?: {
    title?: string;
    description: string;
  };
  pr_url?: string;
  pr_number?: string;
}

interface ProcessData {
  id: string;
  status: string;
  title?: string;
  description?: string;
  createdAt?: string;
  updatedAt?: string;
  processType?: string;
  type?: string;
  run_id?: string;
  events?: ProcessEvent[];
}

const parseTimestamp = (value?: string) => {
  if (!value) return null;
  const timestamp = Date.parse(value);
  return Number.isNaN(timestamp) ? null : timestamp;
};

const getProcessActivityTimestamp = (process: ProcessData) => {
  const timestamps: number[] = [];

  const addTimestamp = (value?: string) => {
    const parsed = parseTimestamp(value);
    if (parsed !== null) {
      timestamps.push(parsed);
    }
  };

  addTimestamp(process.updatedAt);
  addTimestamp(process.createdAt);
  process.events?.forEach((event) => addTimestamp(event.occurred_at));

  if (timestamps.length === 0) {
    return 0;
  }

  return Math.max(...timestamps);
};

const getProcessTypeWithIcon = (processType?: string, type?: string) => {
  const processTypeValue = (processType || type || 'unknown').toLowerCase();

  switch (processTypeValue) {
    case 'issue_resolution':
    case 'issue_resolution_requested':
      return {
        icon: <Zap className="h-4 w-4" />,
        label: 'Issue Resolution',
        color: 'bg-purple-500/10 text-purple-600 border-purple-500/20',
      };
    case 'code_repository_connected':
    case 'repository':
    case 'code_repository_integration':
      return {
        icon: <GitBranch className="h-4 w-4" />,
        label: 'Repository',
        color: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
      };
    case 'code_repository_indexed':
    case 'indexing':
      return {
        icon: <Database className="h-4 w-4" />,
        label: 'Indexing',
        color: 'bg-green-500/10 text-green-600 border-green-500/20',
      };
    case 'docs_generation':
      return {
        icon: <BookOpen className="h-4 w-4" />,
        label: 'Docs Generation',
        color: 'bg-cyan-500/10 text-cyan-600 border-cyan-500/20',
      };
    case 'docs_setup':
      return {
        icon: <BookOpen className="h-4 w-4" />,
        label: 'Docs Setup',
        color: 'bg-cyan-500/10 text-cyan-600 border-cyan-500/20',
      };
    default:
      return {
        icon: <Activity className="h-4 w-4" />,
        label: processTypeValue
          .replace(/_/g, ' ')
          .replace(/\b\w/g, (l) => l.toUpperCase()),
        color: 'bg-gray-500/10 text-gray-600 border-gray-500/20',
      };
  }
};

const GROUP_PRIORITY = new Map<string, number>([
  ['issue_resolution', 1],
  ['issue_resolution_requested', 1],
  ['code_repository_integration', 2],
  ['code_repository_connected', 2],
  ['code_repository_indexed', 3],
]);

const LOADING_SKELETON_KEYS = ['one', 'two', 'three', 'four', 'five', 'six'];

const getGroupPriority = (groupType: string) =>
  GROUP_PRIORITY.get(groupType.toLowerCase()) ?? 10;

const getStatusBadgeWithIcon = (status?: string) => {
  if (!status) {
    return {
      badge: (
        <Badge variant="outline" className="flex items-center gap-1">
          <AlertTriangle className="h-3 w-3" />
          Unknown
        </Badge>
      ),
      color: 'border-gray-200',
    };
  }

  switch (status.toLowerCase()) {
    case 'completed':
    case 'success':
    case 'indexed':
    case 'connected':
      return {
        badge: (
          <Badge className="bg-green-500 text-white flex items-center gap-1">
            <CheckCircle className="h-3 w-3" />
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Badge>
        ),
        color: 'border-green-200 hover:border-green-300',
      };
    case 'failed':
    case 'error':
      return {
        badge: (
          <Badge className="bg-red-500 text-white flex items-center gap-1">
            <XCircle className="h-3 w-3" />
            Failed
          </Badge>
        ),
        color: 'border-red-200 hover:border-red-300',
      };
    case 'in_progress':
    case 'running':
    case 'indexing':
    case 'requested':
      return {
        badge: (
          <Badge className="bg-blue-500 text-white flex items-center gap-1">
            <Clock className="h-3 w-3 animate-pulse" />
            In Progress
          </Badge>
        ),
        color: 'border-blue-200 hover:border-blue-300',
      };
    default:
      return {
        badge: (
          <Badge variant="outline" className="flex items-center gap-1">
            <Activity className="h-3 w-3" />
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Badge>
        ),
        color: 'border-gray-200 hover:border-gray-300',
      };
  }
};

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
  return date.toLocaleDateString();
};

const getTaskTitle = (process: ProcessData) => {
  if (
    (process.type === 'issue_resolution' ||
      process.processType === 'issue_resolution') &&
    process.events
  ) {
    const issueRequestedEvent = process.events.find(
      (event) =>
        event.type === 'issue_resolution_requested' ||
        event.type === 'IssueResolutionRequested',
    );

    if (issueRequestedEvent?.data?.issue?.title) {
      return issueRequestedEvent.data.issue.title;
    }

    if (issueRequestedEvent?.issue?.title) {
      return issueRequestedEvent.issue.title;
    }
  }

  if (process.title) return process.title;

  const source = process.type || process.processType;
  if (source) {
    return `${source
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')} Task`;
  }

  return `Task ${process.id.slice(0, 8)}...`;
};

const getPRInfo = (process: ProcessData) => {
  if (!process.events) return null;
  const completedEvent = process.events.find(
    (event) => event.type === 'issue_resolution_completed',
  );
  if (completedEvent?.pr_url && completedEvent?.pr_number) {
    return { url: completedEvent.pr_url, number: completedEvent.pr_number };
  }
  return null;
};

const getTimelineMeta = (process: ProcessData) => {
  const created = process.createdAt || (process as any).created_at;
  const updated = process.updatedAt || (process as any).updated_at;
  const eventTimestamp = process.events
    ?.map((event) => event.occurred_at)
    .filter((value): value is string => Boolean(value))
    .sort()[0];

  const initial = created || eventTimestamp || updated;
  if (!initial) return null;

  if (updated && updated !== created) {
    return { label: 'Updated', value: updated } as const;
  }
  return { label: 'Started', value: initial } as const;
};

export default function TasksPage() {
  const { data: session } = useSession();
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [processes, setProcesses] = useState<ProcessData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [showScrollTop, setShowScrollTop] = useState(false);

  useEffect(() => {
    const knowledgeBaseId = session?.user?.selectedSpace?.knowledgeBaseId;
    if (!knowledgeBaseId) {
      setProcesses([]);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    setLoading(true);

    const fetchProcesses = async () => {
      try {
        const queryParams = new URLSearchParams({
          knowledge_base_id: knowledgeBaseId,
        });
        const response = await fetch(
          `/api/processes?${queryParams.toString()}`,
          {
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch processes: ${response.statusText}`);
        }

        const data = await response.json();
        setProcesses(data.processes || []);
        setError(null);
      } catch (err) {
        if ((err as Error).name === 'AbortError') return;
        console.error('Error fetching processes:', err);
        setError(err instanceof Error ? err.message : 'Failed to load tasks');
        setProcesses([]);
      } finally {
        setLoading(false);
      }
    };

    fetchProcesses();

    return () => controller.abort();
  }, [session?.user?.selectedSpace?.knowledgeBaseId]);

  const processTypes = useMemo(() => {
    return Array.from(
      new Set(
        processes
          .map((process) => process.processType || process.type)
          .filter((type): type is string => Boolean(type)),
      ),
    ).sort();
  }, [processes]);

  useEffect(() => {
    if (typeFilter !== 'all' && !processTypes.includes(typeFilter)) {
      setTypeFilter('all');
    }
  }, [typeFilter, processTypes]);

  const sortedProcesses = useMemo(() => {
    return [...processes].sort(
      (a, b) => getProcessActivityTimestamp(b) - getProcessActivityTimestamp(a),
    );
  }, [processes]);

  const filteredProcesses = useMemo(() => {
    const trimmedSearch = searchTerm.trim().toLowerCase();

    return sortedProcesses.filter((process) => {
      const computedTitle = getTaskTitle(process).toLowerCase();
      const matchesSearch =
        !trimmedSearch ||
        process.id.toLowerCase().includes(trimmedSearch) ||
        (process.title || '').toLowerCase().includes(trimmedSearch) ||
        (process.description || '').toLowerCase().includes(trimmedSearch) ||
        computedTitle.includes(trimmedSearch);

      const matchesStatus =
        statusFilter === 'all' ||
        process.status?.toLowerCase() === statusFilter;
      const matchesType =
        typeFilter === 'all' ||
        process.processType?.toLowerCase() === typeFilter.toLowerCase() ||
        process.type?.toLowerCase() === typeFilter.toLowerCase();

      return matchesSearch && matchesStatus && matchesType;
    });
  }, [sortedProcesses, searchTerm, statusFilter, typeFilter]);

  const groupedEntries = useMemo(() => {
    const groups = new Map<string, ProcessData[]>();

    filteredProcesses.forEach((process) => {
      const key = (
        process.processType ||
        process.type ||
        'unknown'
      ).toLowerCase();
      const existing = groups.get(key);

      if (existing) {
        existing.push(process);
        return;
      }

      groups.set(key, [process]);
    });

    return Array.from(groups.entries())
      .map(([key, items]) => ({
        key,
        items: [...items].sort(
          (first, second) =>
            getProcessActivityTimestamp(second) -
            getProcessActivityTimestamp(first),
        ),
        header: getProcessTypeWithIcon(key),
      }))
      .sort((a, b) => getGroupPriority(a.key) - getGroupPriority(b.key));
  }, [filteredProcesses]);

  const navItems = useMemo(
    () =>
      groupedEntries.map(({ key, header, items }) => ({
        id: key,
        label: header.label,
        count: items.length,
      })),
    [groupedEntries],
  );

  const totalCount = filteredProcesses.length;
  const groupCount = groupedEntries.length;

  const handleGroupJump = useCallback((groupId: string) => {
    const container = containerRef.current;
    if (!container) return;
    const target = container.querySelector<HTMLDivElement>(
      `[data-group-id="${groupId}"]`,
    );
    if (!target) return;

    const offsetTop = target.offsetTop;
    container.scrollTo({ top: offsetTop - 12, behavior: 'smooth' });
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      setShowScrollTop(container.scrollTop > 400);
    };

    handleScroll();
    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    container.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleConnectRepo = useCallback(() => {
    if (typeof window === 'undefined') return;
    window.dispatchEvent(new Event('open-repo-dialog'));
  }, []);

  const renderEmptyState = () => {
    const hasFilters = Boolean(
      searchTerm || statusFilter !== 'all' || typeFilter !== 'all',
    );
    return (
      <Card className="border-dashed border-muted">
        <CardHeader className="flex flex-col items-center text-center gap-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <ClipboardList className="h-6 w-6 text-muted-foreground" />
          </div>
          <CardTitle className="text-lg">
            {hasFilters ? 'No matching tasks' : 'No tasks yet'}
          </CardTitle>
          <CardDescription className="max-w-md">
            {hasFilters
              ? 'We couldn’t find tasks that match your search or filters. Try broadening them or clearing the search.'
              : 'Once you run an issue resolution or connect a repository, tasks will show up here.'}
          </CardDescription>
          <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
            {hasFilters ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSearchTerm('');
                  setStatusFilter('all');
                  setTypeFilter('all');
                }}
              >
                Clear filters
              </Button>
            ) : (
              <Button size="sm" variant="secondary" onClick={handleConnectRepo}>
                Connect repository
              </Button>
            )}
          </div>
        </CardHeader>
      </Card>
    );
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

      <div ref={containerRef} className="flex-1 overflow-auto">
        <div className="container mx-auto py-6 px-4 lg:px-6">
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {LOADING_SKELETON_KEYS.map((placeholderKey) => (
                <Card key={`loading-${placeholderKey}`}>
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
                <CardTitle className="text-red-500">
                  Error loading tasks
                </CardTitle>
                <CardDescription>{error}</CardDescription>
              </CardHeader>
            </Card>
          ) : groupCount === 0 ? (
            renderEmptyState()
          ) : (
            <div className="flex flex-col lg:grid lg:grid-cols-[minmax(0,1fr)_220px] lg:gap-6">
              <div className="space-y-8">
                {groupedEntries.map(({ key, items, header }) => {
                  const anchorId = `group-${key}`;
                  return (
                    <motion.section
                      key={key}
                      data-group-id={key}
                      id={anchorId}
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="space-y-4"
                    >
                      <div className="flex items-center gap-3 pb-2 border-b border-border">
                        <div className={`p-2 rounded-md ${header.color}`}>
                          {header.icon}
                        </div>
                        <div>
                          <h2 className="text-xl font-semibold">
                            {header.label}
                          </h2>
                          <p className="text-sm text-muted-foreground">
                            {items.length}{' '}
                            {items.length === 1 ? 'task' : 'tasks'}
                          </p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                        {(() => {
                          // Group docs_generation by run_id
                          if (key === 'docs_generation') {
                            const runGroups = new Map<string, ProcessData[]>();
                            const standalone: ProcessData[] = [];

                            items.forEach((process) => {
                              if (process.run_id) {
                                const existing = runGroups.get(process.run_id);
                                if (existing) {
                                  existing.push(process);
                                } else {
                                  runGroups.set(process.run_id, [process]);
                                }
                              } else {
                                standalone.push(process);
                              }
                            });

                            const renderProcess = (
                              process: ProcessData,
                              index: number,
                            ) => {
                              const { badge, color: statusColor } =
                                getStatusBadgeWithIcon(process.status);
                              const typeMeta = getProcessTypeWithIcon(
                                process.processType,
                                process.type,
                              );
                              const prInfo = getPRInfo(process);
                              const timelineMeta = getTimelineMeta(process);

                              return (
                                <motion.div
                                  key={process.id}
                                  initial={{ opacity: 0, y: 12 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  transition={{
                                    duration: 0.25,
                                    delay: index * 0.05,
                                  }}
                                >
                                  <Link href={`/tasks/${process.id}`}>
                                    <Card
                                      className={`cursor-pointer transition-all duration-200 hover:shadow-md ${statusColor}`}
                                    >
                                      <CardHeader className="pb-3">
                                        <div className="flex justify-between items-start gap-3 mb-2">
                                          <div className="min-w-0 flex-1">
                                            <CardTitle className="text-base font-semibold leading-tight line-clamp-2">
                                              {getTaskTitle(process)}
                                            </CardTitle>
                                            <CardDescription className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                                              <span className="font-mono">
                                                {process.id.slice(0, 8)}...
                                              </span>
                                            </CardDescription>
                                          </div>
                                          <div className="flex flex-col items-end gap-1">
                                            {badge}
                                            {prInfo && (
                                              <button
                                                type="button"
                                                onClick={(event) => {
                                                  event.preventDefault();
                                                  event.stopPropagation();
                                                  window.open(
                                                    prInfo.url,
                                                    '_blank',
                                                    'noopener,noreferrer',
                                                  );
                                                }}
                                                className="text-[0.7rem] text-blue-500 hover:text-blue-700 flex items-center gap-1 transition-colors"
                                              >
                                                <ExternalLink className="h-3 w-3" />
                                                PR #{prInfo.number}
                                              </button>
                                            )}
                                          </div>
                                        </div>

                                        <div className="flex flex-wrap items-center gap-2">
                                          <Badge
                                            variant="outline"
                                            className={`${typeMeta.color} flex items-center gap-1`}
                                          >
                                            {typeMeta.icon}
                                            <span className="text-xs">
                                              {typeMeta.label}
                                            </span>
                                          </Badge>
                                          {timelineMeta && (
                                            <Badge
                                              variant="outline"
                                              className="flex items-center gap-1 text-xs text-muted-foreground"
                                            >
                                              <Clock className="h-3 w-3" />
                                              <span>
                                                {timelineMeta.label}{' '}
                                                {getRelativeTime(
                                                  timelineMeta.value,
                                                )}
                                              </span>
                                            </Badge>
                                          )}
                                        </div>
                                      </CardHeader>

                                      <CardContent className="pt-0 space-y-3">
                                        {process.description && (
                                          <p className="text-sm text-muted-foreground line-clamp-2">
                                            {process.description}
                                          </p>
                                        )}
                                      </CardContent>
                                    </Card>
                                  </Link>
                                </motion.div>
                              );
                            };

                            let renderIndex = 0;
                            const elements: React.ReactElement[] = [];

                            // Render grouped processes
                            Array.from(runGroups.entries()).forEach(
                              ([runId, processes]) => {
                                if (processes.length > 1) {
                                  // Add simple group label for first item
                                  processes.forEach((p, idx) => {
                                    const isFirst = idx === 0;
                                    elements.push(
                                      <div key={p.id} className="relative">
                                        {isFirst && (
                                          <div className="absolute -top-8 left-0 flex items-center gap-2 text-xs text-muted-foreground">
                                            <BookOpen className="h-3 w-3" />
                                            <span>
                                              Run {runId.slice(0, 8)} •{' '}
                                              {processes.length} prompts
                                            </span>
                                          </div>
                                        )}
                                        {renderProcess(p, renderIndex++)}
                                      </div>,
                                    );
                                  });
                                } else {
                                  // Single process in run, render normally
                                  elements.push(
                                    renderProcess(processes[0], renderIndex++),
                                  );
                                }
                              },
                            );

                            // Render standalone processes
                            standalone.forEach((p) => {
                              elements.push(renderProcess(p, renderIndex++));
                            });

                            return elements;
                          } else {
                            // Non-docs_generation types: render normally
                            return items.map((process, index) => {
                              const { badge, color: statusColor } =
                                getStatusBadgeWithIcon(process.status);
                              const typeMeta = getProcessTypeWithIcon(
                                process.processType,
                                process.type,
                              );
                              const prInfo = getPRInfo(process);
                              const timelineMeta = getTimelineMeta(process);

                              return (
                                <motion.div
                                  key={process.id}
                                  initial={{ opacity: 0, y: 12 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  transition={{
                                    duration: 0.25,
                                    delay: index * 0.05,
                                  }}
                                >
                                  <Link href={`/tasks/${process.id}`}>
                                    <Card
                                      className={`cursor-pointer transition-all duration-200 hover:shadow-md ${statusColor}`}
                                    >
                                      <CardHeader className="pb-3">
                                        <div className="flex justify-between items-start gap-3 mb-2">
                                          <div className="min-w-0 flex-1">
                                            <CardTitle className="text-base font-semibold leading-tight line-clamp-2">
                                              {getTaskTitle(process)}
                                            </CardTitle>
                                            <CardDescription className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                                              <span className="font-mono">
                                                {process.id.slice(0, 8)}...
                                              </span>
                                            </CardDescription>
                                          </div>
                                          <div className="flex flex-col items-end gap-1">
                                            {badge}
                                            {prInfo && (
                                              <button
                                                type="button"
                                                onClick={(event) => {
                                                  event.preventDefault();
                                                  event.stopPropagation();
                                                  window.open(
                                                    prInfo.url,
                                                    '_blank',
                                                    'noopener,noreferrer',
                                                  );
                                                }}
                                                className="text-[0.7rem] text-blue-500 hover:text-blue-700 flex items-center gap-1 transition-colors"
                                              >
                                                <ExternalLink className="h-2.5 w-2.5" />
                                                PR #{prInfo.number}
                                              </button>
                                            )}
                                          </div>
                                        </div>

                                        <div className="flex flex-wrap items-center gap-2">
                                          <Badge
                                            variant="outline"
                                            className={`${typeMeta.color} flex items-center gap-1`}
                                          >
                                            {typeMeta.icon}
                                            <span className="text-xs">
                                              {typeMeta.label}
                                            </span>
                                          </Badge>
                                          {timelineMeta && (
                                            <Badge
                                              variant="outline"
                                              className="flex items-center gap-1 text-xs text-muted-foreground"
                                            >
                                              <Clock className="h-3 w-3" />
                                              <span>
                                                {timelineMeta.label}{' '}
                                                {getRelativeTime(
                                                  timelineMeta.value,
                                                )}
                                              </span>
                                            </Badge>
                                          )}
                                        </div>
                                      </CardHeader>

                                      <CardContent className="pt-0 space-y-3">
                                        {process.description && (
                                          <p className="text-sm text-muted-foreground line-clamp-2">
                                            {process.description}
                                          </p>
                                        )}
                                      </CardContent>
                                    </Card>
                                  </Link>
                                </motion.div>
                              );
                            });
                          }
                        })()}
                      </div>
                    </motion.section>
                  );
                })}
              </div>

              <aside className="hidden lg:block lg:sticky lg:top-24 h-fit">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-semibold">
                      Jump to category
                    </CardTitle>
                    <CardDescription className="text-xs text-muted-foreground">
                      Quick navigation for long task lists
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {navItems.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => handleGroupJump(item.id)}
                        className="w-full rounded-md border border-border px-3 py-2 text-left text-sm hover:bg-muted transition"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="truncate">{item.label}</span>
                          <span className="text-xs text-muted-foreground">
                            {item.count}
                          </span>
                        </div>
                      </button>
                    ))}
                  </CardContent>
                </Card>
              </aside>
            </div>
          )}
        </div>
      </div>

      {showScrollTop && (
        <Button
          type="button"
          onClick={scrollToTop}
          className="fixed bottom-6 right-6 z-40 shadow-lg"
          size="icon"
        >
          <ArrowUp className="h-4 w-4" />
          <span className="sr-only">Scroll to top</span>
        </Button>
      )}
    </div>
  );
}
