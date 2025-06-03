# Tasks & Processes Feature

## Overview

This feature provides a comprehensive interface for viewing and managing tasks and processes in the current user workspace. The implementation includes both a tasks list view and detailed individual task pages with modern, clean design principles.

## Features Added

### 1. Main Tasks List Page (`/tasks`)

- **Grid Layout**: Displays tasks in a responsive card grid (1-3 columns based on screen size)
- **Search & Filters**: 
  - Search by task ID, title, or description
  - Filter by status (All, Completed, In Progress, Failed, Connected, Indexed)
  - Filter by process type (dynamically populated from available tasks)
- **Modern Card Design**: Each task card shows:
  - Task title with clear typography
  - Process type with appropriate icons
  - Status badges with color coding and icons
  - Relative timestamps (e.g., "2h ago", "3d ago")
  - Process ID (truncated for better UX)
- **Visual Indicators**:
  - Color-coded borders based on status
  - Animated status icons for in-progress tasks
  - Smooth hover transitions

### 2. Enhanced Task Detail Page (`/tasks/[processId]`)

- **Comprehensive Header**: 
  - Large task title with process type icons
  - Process ID in monospace font
  - Multiple status and type badges
  - Action buttons for completed/failed tasks
- **Process Information Card**:
  - Basic information (ID, type, status)
  - Timing details (created, updated, event count)
  - Events summary with visual timeline
  - Clean two-column layout on larger screens
- **Enhanced Status Display**:
  - Real-time status indicators
  - Animated progress indicators for active tasks
  - Clear error state handling with detailed error dialogs

### 3. API Integration

- **New API Route**: `/api/processes`
  - Fetches processes from backend service
  - Supports filtering by space_id, process_type, status
  - Pagination support (limit/offset)
  - Data normalization for consistent field names
- **Error Handling**: Graceful fallbacks and user-friendly error messages

### 4. Navigation Integration

- **Sidebar Integration**: Tasks button in sidebar now links to main tasks page
- **Breadcrumb Navigation**: Easy navigation between list and detail views
- **Responsive Design**: Works seamlessly on mobile, tablet, and desktop

## Design Principles

### Modern & Clean Interface
- Consistent spacing and typography
- Subtle shadows and borders
- Clean color palette with purpose-driven colors
- Smooth animations and transitions

### Clear Process Information
- **Process Types** with distinct icons:
  - ⚡ Issue Resolution (purple)
  - 🔀 Repository (blue) 
  - 🗃️ Indexing (green)
  - ⚙️ General processes (gray)

- **Status Indicators** with colors and icons:
  - ✅ Completed/Success (green)
  - ❌ Failed/Error (red)
  - 🕐 In Progress/Running (blue with animation)
  - ⚠️ Unknown (gray)

### Responsive & Accessible
- Mobile-first responsive design
- Proper semantic HTML
- Keyboard navigation support
- Clear visual hierarchy

## Technical Implementation

### Frontend Stack
- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **Lucide React** for icons

### State Management
- React hooks for local state
- Real-time data fetching
- Proper error boundaries

### Performance Optimizations
- Lazy loading with suspense
- Optimized re-renders
- Efficient filtering and search
- Image optimization

## Usage

1. **Access Tasks**: Click "Tasks" in the sidebar or navigate to `/tasks`
2. **Browse Tasks**: Use search and filters to find specific tasks
3. **View Details**: Click any task card to see comprehensive details
4. **Monitor Progress**: Real-time status updates for active tasks
5. **Handle Errors**: Click "View Error Details" for failed tasks

## Future Enhancements

- Real-time WebSocket updates for live status changes
- Bulk actions (pause, resume, cancel multiple tasks)
- Task creation and management interface
- Advanced filtering and sorting options
- Export capabilities (CSV, JSON)
- Task performance analytics and metrics 