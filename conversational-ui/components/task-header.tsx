'use client';

import { SharedHeader } from '@/components/shared-header';
import { Input } from './ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Activity, Filter, Search } from 'lucide-react';
import { useEffect, useMemo, useRef } from 'react';

interface TaskHeaderProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  statusFilter: string;
  onStatusFilterChange: (value: string) => void;
  typeFilter: string;
  onTypeFilterChange: (value: string) => void;
  processTypes: string[];
  totalCount: number;
  groupCount: number;
  loading?: boolean;
}

const STATUS_OPTIONS = [
  { value: 'all', label: 'All Status' },
  { value: 'completed', label: 'Completed' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'failed', label: 'Failed' },
  { value: 'connected', label: 'Connected' },
  { value: 'indexed', label: 'Indexed' },
];

export function TaskHeader({
  searchTerm,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  typeFilter,
  onTypeFilterChange,
  processTypes,
  totalCount,
  groupCount,
  loading = false,
}: TaskHeaderProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const typeOptions = useMemo(() => {
    return [
      { value: 'all', label: 'All Types' },
      ...processTypes.map((type) => ({
        value: type,
        label: type.replace(/_/g, ' ').replace(/\w/g, (l) => l.toUpperCase()),
      })),
    ];
  }, [processTypes]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        inputRef.current?.focus();
        inputRef.current?.select();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  return (
    <SharedHeader
      rightExtra={
        <div className="hidden md:flex shrink-0 items-center gap-3 text-sm text-muted-foreground">
          <span>
            {loading
              ? 'Loading…'
              : `${totalCount} ${totalCount === 1 ? 'task' : 'tasks'}`}
          </span>
          <span aria-hidden="true">•</span>
          <span>
            {groupCount} {groupCount === 1 ? 'category' : 'categories'}
          </span>
        </div>
      }
    >
      <div className="flex-1 min-w-0 px-3 py-2 md:px-6">
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:gap-4">
            <span className="text-lg lg:text-xl font-semibold text-foreground whitespace-nowrap">
              Tasks &amp; Processes
            </span>
            <div className="relative w-full md:flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                ref={inputRef}
                value={searchTerm}
                onChange={(event) => onSearchChange(event.target.value)}
                placeholder="Search by ID, title, or description"
                className="pl-10 pr-12 text-sm"
              />
              <span className="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 rounded-md border px-2 py-0.5 text-[11px] text-muted-foreground/80 md:inline-flex">
                ⌘K
              </span>
            </div>

            <div className="hidden md:flex flex-shrink-0 items-center gap-2">
              <Select value={statusFilter} onValueChange={onStatusFilterChange}>
                <SelectTrigger className="w-[150px] text-sm">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={typeFilter} onValueChange={onTypeFilterChange}>
                <SelectTrigger className="w-[150px] text-sm">
                  <Activity className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  {typeOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {!loading && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground md:hidden">
              <span>
                {totalCount} {totalCount === 1 ? 'task' : 'tasks'}
              </span>
              <span aria-hidden="true">•</span>
              <span>
                {groupCount} {groupCount === 1 ? 'category' : 'categories'}
              </span>
            </div>
          )}
        </div>
      </div>
    </SharedHeader>
  );
}
