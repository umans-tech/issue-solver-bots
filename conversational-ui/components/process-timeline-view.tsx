'use client';

import { useMemo, useState } from 'react';
import { Badge } from './ui/badge';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircleFillIcon, 
  AlertCircle, 
  ClockRewind,
  ChevronDownIcon,
  InfoIcon,
  LoaderIcon
} from './icons';

interface TimelineEvent {
  id: string;
  type: string;
  timestamp?: string;
  occurred_at?: string;
  data?: any;
  reason?: string;
  error_message?: string;
  pr_url?: string;
  pr_number?: number;
}

interface ProcessTimelineViewProps {
  events?: TimelineEvent[];
  className?: string;
}

export function ProcessTimelineView({ events = [], className }: ProcessTimelineViewProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const sortedEvents = useMemo(() => {
    return [...events].sort((a, b) => {
      const dateA = a.occurred_at ? new Date(a.occurred_at) : new Date(0);
      const dateB = b.occurred_at ? new Date(b.occurred_at) : new Date(0);
      return dateA.getTime() - dateB.getTime();
    });
  }, [events]);

  // Function to format date strings
  const formatDate = (event: TimelineEvent) => {
    try {
      if (event.occurred_at) {
        return new Date(event.occurred_at).toLocaleString();
      }
      return "N/A";
    } catch (e) {
      return "Invalid Date";
    }
  };

  // Function to get event icon and color based on event type
  const getEventTypeDetails = (eventType: string) => {
    const type = eventType.toLowerCase();
    
    // Consistent check mark icon for all completion states
    const CheckIcon = () => (
      <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
    );
    
    // Extract the action part from event type (e.g., "requested" from "issue_resolution_requested")
    const getActionFromType = (type: string) => {
      // Split by underscore and get the last part
      const parts = type.split('_');
      if (parts.length > 0) {
        // Capitalize first letter
        const action = parts[parts.length - 1];
        return action.charAt(0).toUpperCase() + action.slice(1);
      }
      return '';
    };

    const actionLabel = getActionFromType(type);
    
    if (type.includes('start')) {
      return {
        icon: <ClockRewind size={16} />,
        color: 'bg-blue-500/10 border-blue-500/20',
        textColor: 'text-blue-500',
        label: actionLabel || 'Started'
      };
    } else if (type.includes('indexed')) {
      return {
        icon: <CheckIcon />,
        color: 'bg-green-500/10 border-green-500/20',
        textColor: 'text-green-500',
        label: actionLabel || 'Indexed'
      };
    } else if (type.includes('complete') || type.includes('success')) {
      return {
        icon: <CheckIcon />,
        color: 'bg-green-500/10 border-green-500/20',
        textColor: 'text-green-500',
        label: actionLabel || 'Completed'
      };
    } else if (type.includes('fail') || type.includes('error')) {
      return {
        icon: <AlertCircle size={16} />,
        color: 'bg-red-500/10 border-red-500/20',
        textColor: 'text-red-500',
        label: actionLabel || 'Failed'
      };
    } else if (type.includes('request')) {
      return {
        icon: <InfoIcon size={16} />,
        color: 'bg-purple-500/10 border-purple-500/20',
        textColor: 'text-purple-500',
        label: actionLabel || 'Requested'
      };
    } else if (type.includes('progress') || type.includes('update')) {
      return {
        icon: <LoaderIcon size={16} />,
        color: 'bg-yellow-500/10 border-yellow-500/20',
        textColor: 'text-yellow-500',
        label: actionLabel || 'In Progress'
      };
    } else {
      return {
        icon: <InfoIcon size={16} />,
        color: 'bg-gray-500/10 border-gray-500/20',
        textColor: 'text-gray-500',
        label: actionLabel || 'Event'
      };
    }
  };

  const variants = {
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

  if (!events || events.length === 0) {
    return (
      <div className={cn("text-center py-4 text-muted-foreground", className)}>
        No timeline events available
      </div>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      {/* Timeline header with toggle */}
      <div 
        className="flex items-center gap-2 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h3 className="font-medium text-sm text-muted-foreground">Timeline</h3>
        <div className={cn("transition-transform", isExpanded ? "rotate-180" : "")}>
          <ChevronDownIcon size={16} />
        </div>
      </div>

      {/* Timeline content (collapsible) */}
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            key="timeline-content"
            initial="collapsed"
            animate="expanded"
            exit="collapsed"
            variants={variants}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            style={{ overflow: 'hidden' }}
          >
            {/* Horizontal timeline */}
            <div className="flex overflow-x-auto pb-2 gap-2">
              {sortedEvents.map((event, index) => {
                const { icon, color, textColor, label } = getEventTypeDetails(event.type);
                
                return (
                  <div 
                    key={event.id || index} 
                    className={cn(
                      "flex-shrink-0 border rounded-md p-1.5 min-w-[150px] max-w-[200px]", 
                      color
                    )}
                  >
                    <div className="flex items-center gap-1">
                      <div className={cn("w-4 h-4 flex items-center justify-center", textColor)}>
                        {icon}
                      </div>
                      <div>
                        <span className={cn("font-medium text-xs", textColor)}>{label}</span>
                      </div>
                    </div>
                    
                    <time className="text-xs text-muted-foreground block">
                      {formatDate(event)}
                    </time>
                    
                    {event.data && (
                      <div className="mt-1 text-xs bg-background/50 p-1 rounded-md">
                        <pre className="whitespace-pre-wrap break-words overflow-hidden text-ellipsis max-h-[80px]">
                          {typeof event.data === 'string' 
                            ? event.data 
                            : JSON.stringify(event.data, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
} 