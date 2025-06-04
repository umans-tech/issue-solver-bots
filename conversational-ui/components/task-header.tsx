'use client';

import { SharedHeader } from '@/components/shared-header';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Button } from './ui/button';
import { Search, Filter, Activity, X } from 'lucide-react';
import { useState } from 'react';

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
  loading = false
}: TaskHeaderProps) {
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);

  const handleSearchToggle = () => {
    setIsSearchExpanded(!isSearchExpanded);
    if (isSearchExpanded && searchTerm) {
      onSearchChange(''); // Clear search when closing
    }
  };

  return (
    <SharedHeader>
      <div className="flex items-center justify-between mx-2 lg:mx-4 flex-1 min-w-0">
        {/* Mobile Search Expanded Mode */}
        {isSearchExpanded && (
          <div className="flex items-center gap-2 flex-1 md:hidden">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search by ID or title..."
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-10 text-sm"
                autoFocus
              />
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleSearchToggle}
              className="px-2"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Normal Layout (Always on Desktop, Mobile when search not expanded) */}
        <div className={`flex items-center justify-between flex-1 ${isSearchExpanded ? 'hidden md:flex' : 'flex'}`}>
          {/* Title and Stats */}
          <div className="flex items-center gap-3 text-sm min-w-0">
            <span className="text-lg lg:text-xl font-semibold text-foreground truncate">
              Tasks & Processes
            </span>
            {!loading && (
              <div className="hidden xl:flex items-center gap-2 text-muted-foreground text-sm">
                <span>•</span>
                <span>{totalCount} tasks</span>
                <span>•</span>
                <span>{groupCount} categories</span>
              </div>
            )}
          </div>
          
          {/* Search and Filters */}
          <div className="flex items-center gap-2 min-w-0">
            {/* Mobile Search Button */}
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleSearchToggle}
              className="md:hidden px-3"
            >
              <Search className="h-4 w-4" />
            </Button>

            {/* Desktop Search */}
            <div className="relative hidden md:block w-60 lg:w-80">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search by ID or title..."
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-10 text-sm"
              />
            </div>
            
            {/* Desktop Filters */}
            <div className="hidden lg:flex items-center gap-2">
              <Select value={statusFilter} onValueChange={onStatusFilterChange}>
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

              <Select value={typeFilter} onValueChange={onTypeFilterChange}>
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
        </div>
      </div>
    </SharedHeader>
  );
} 