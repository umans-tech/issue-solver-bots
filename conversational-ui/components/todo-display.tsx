import React from 'react';
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from './ui/tooltip';
import { CheckedSquare, UncheckedSquare, PlayIcon, XIcon, InfoIcon } from './icons';

interface TodoItem {
  id: string;
  content: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority?: 'low' | 'medium' | 'high';
}

interface TodoDisplayProps {
  todos: TodoItem[];
  toolName?: string;
}

const getStatusIcon = (status: TodoItem['status']) => {
  switch (status) {
    case 'completed':
      return <span className="text-green-600"><CheckedSquare size={16} /></span>;
    case 'in_progress':
      return <span className="text-blue-600 animate-pulse"><PlayIcon size={16} /></span>;
    case 'cancelled':
      return <span className="text-red-600"><XIcon size={16} /></span>;
    case 'pending':
    default:
      return <span className="text-gray-400"><UncheckedSquare size={16} /></span>;
  }
};

const getStatusText = (status: TodoItem['status']) => {
  switch (status) {
    case 'completed':
      return 'Completed';
    case 'in_progress':
      return 'In Progress';
    case 'cancelled':
      return 'Cancelled';
    case 'pending':
    default:
      return 'Pending';
  }
};

const getStatusColor = (status: TodoItem['status']) => {
  switch (status) {
    case 'completed':
      return 'text-green-600 bg-green-50 border-green-200';
    case 'in_progress':
      return 'text-blue-600 bg-blue-50 border-blue-200';
    case 'cancelled':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'pending':
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

const getPriorityColor = (priority?: TodoItem['priority']) => {
  switch (priority) {
    case 'high':
      return 'bg-red-100 text-red-700 border-red-200';
    case 'medium':
      return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    case 'low':
      return 'bg-green-100 text-green-700 border-green-200';
    default:
      return '';
  }
};

export const TodoDisplay: React.FC<TodoDisplayProps> = ({ todos, toolName }) => {
  const completedCount = todos.filter(todo => todo.status === 'completed').length;
  const totalCount = todos.length;
  const progressPercentage = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  // Keep todos in original order from payload

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Header with progress */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-sm font-semibold text-gray-900">Task Progress</h3>
            
            {/* Hover info icon */}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button className="opacity-60 hover:opacity-100 transition-opacity">
                    <span className="text-gray-500"><InfoIcon size={14} /></span>
                  </button>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">
                    <strong>{toolName || 'TodoWrite'}</strong> tool executed successfully
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <div className="text-sm text-gray-600">
            {completedCount}/{totalCount} completed
          </div>
        </div>
        
        {/* Progress bar */}
        <div className="mt-2">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Todo items in original order */}
      <div className="divide-y divide-gray-100">
        {todos.map((todo) => {
          const isCompleted = todo.status === 'completed';
          const isCancelled = todo.status === 'cancelled';
          const isInProgress = todo.status === 'in_progress';
          
          const hoverClass = isInProgress ? 'hover:bg-blue-50/50' : 
                            isCompleted ? 'hover:bg-green-50/30' :
                            isCancelled ? 'hover:bg-red-50/30' : 'hover:bg-gray-50/50';
          
          const opacity = isCompleted ? 'opacity-75' : isCancelled ? 'opacity-60' : '';
          
          return (
            <div key={todo.id} className={cn("p-4 transition-colors", hoverClass, opacity)}>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  {getStatusIcon(todo.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={cn(
                      'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border',
                      getStatusColor(todo.status)
                    )}>
                      {getStatusText(todo.status)}
                    </span>
                    {todo.priority && (
                      <span className={cn(
                        'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border',
                        getPriorityColor(todo.priority)
                      )}>
                        {todo.priority} priority
                      </span>
                    )}
                  </div>
                  <p className={cn(
                    "text-sm",
                    isCompleted || isCancelled ? "line-through" : "",
                    isCompleted ? "text-gray-600" : 
                    isCancelled ? "text-gray-500" :
                    isInProgress ? "text-gray-900 font-medium" : "text-gray-700"
                  )}>
                    {todo.content}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty state */}
      {todos.length === 0 && (
        <div className="p-8 text-center">
          <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <span className="text-gray-400"><CheckedSquare size={24} /></span>
          </div>
          <p className="text-sm text-gray-500">No tasks to display</p>
        </div>
      )}
    </div>
  );
};
