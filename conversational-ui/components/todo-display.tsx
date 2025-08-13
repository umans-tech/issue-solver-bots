import React from 'react';
import { cn } from '@/lib/utils';
import { CheckCircleFillIcon, ClockRewind, PlayIcon, XIcon } from './icons';

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
      return <CheckCircleFillIcon size={16} className="text-green-600" />;
    case 'in_progress':
      return <PlayIcon size={16} className="text-blue-600 animate-pulse" />;
    case 'cancelled':
      return <XIcon size={16} className="text-red-600" />;
    case 'pending':
    default:
      return <ClockRewind size={16} className="text-gray-400" />;
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

  // Group todos by status for better organization
  const todosByStatus = {
    in_progress: todos.filter(todo => todo.status === 'in_progress'),
    pending: todos.filter(todo => todo.status === 'pending'),
    completed: todos.filter(todo => todo.status === 'completed'),
    cancelled: todos.filter(todo => todo.status === 'cancelled'),
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Header with progress */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
              <CheckCircleFillIcon size={16} className="text-blue-600" />
            </div>
            <h3 className="text-sm font-semibold text-gray-900">Task Progress</h3>
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

      {/* Todo items */}
      <div className="divide-y divide-gray-100">
        {/* In Progress Items */}
        {todosByStatus.in_progress.map((todo) => (
          <div key={todo.id} className="p-4 hover:bg-blue-50/50 transition-colors">
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
                <p className="text-sm text-gray-900 font-medium">{todo.content}</p>
              </div>
            </div>
          </div>
        ))}

        {/* Pending Items */}
        {todosByStatus.pending.map((todo) => (
          <div key={todo.id} className="p-4 hover:bg-gray-50/50 transition-colors">
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
                <p className="text-sm text-gray-700">{todo.content}</p>
              </div>
            </div>
          </div>
        ))}

        {/* Completed Items */}
        {todosByStatus.completed.map((todo) => (
          <div key={todo.id} className="p-4 hover:bg-green-50/30 transition-colors opacity-75">
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
                <p className="text-sm text-gray-600 line-through">{todo.content}</p>
              </div>
            </div>
          </div>
        ))}

        {/* Cancelled Items */}
        {todosByStatus.cancelled.map((todo) => (
          <div key={todo.id} className="p-4 hover:bg-red-50/30 transition-colors opacity-60">
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
                <p className="text-sm text-gray-500 line-through">{todo.content}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty state */}
      {todos.length === 0 && (
        <div className="p-8 text-center">
          <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <CheckCircleFillIcon size={24} className="text-gray-400" />
          </div>
          <p className="text-sm text-gray-500">No tasks to display</p>
        </div>
      )}
    </div>
  );
};
