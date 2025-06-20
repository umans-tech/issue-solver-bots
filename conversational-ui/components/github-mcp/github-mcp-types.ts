// GitHub MCP tool categories and comprehensive tool list
export const GITHUB_MCP_TOOL_CATEGORIES = {
  // Users (2 tools)
  users: ['get_me', 'search_users'],
  
  // Issues (8 tools)  
  issues: [
    'get_issue', 'get_issue_comments', 'create_issue', 'add_issue_comment',
    'list_issues', 'update_issue', 'search_issues', 'assign_copilot_to_issue'
  ],
  
  // Pull Requests (17 tools)
  pullRequests: [
    'get_pull_request', 'list_pull_requests', 'merge_pull_request', 
    'get_pull_request_files', 'get_pull_request_status', 'update_pull_request_branch',
    'get_pull_request_comments', 'get_pull_request_reviews', 'get_pull_request_diff',
    'create_pending_pull_request_review', 'add_pull_request_review_comment_to_pending_review',
    'submit_pending_pull_request_review', 'delete_pending_pull_request_review',
    'create_and_submit_pull_request_review', 'create_pull_request', 'update_pull_request',
    'request_copilot_review'
  ],
  
  // Repositories (14 tools)
  repositories: [
    'create_or_update_file', 'delete_file', 'list_branches', 'push_files',
    'search_repositories', 'create_repository', 'get_file_contents', 'fork_repository',
    'create_branch', 'list_commits', 'get_commit', 'get_tag', 'list_tags', 'search_code'
  ],
  
  // Actions (14 tools) 
  actions: [
    'list_workflows', 'list_workflow_runs', 'run_workflow', 'get_workflow_run',
    'get_workflow_run_logs', 'list_workflow_jobs', 'get_job_logs', 'rerun_workflow_run',
    'rerun_failed_jobs', 'cancel_workflow_run', 'list_workflow_run_artifacts',
    'download_workflow_run_artifact', 'delete_workflow_run_logs', 'get_workflow_run_usage'
  ],
  
  // Security (4 tools)
  security: [
    'get_code_scanning_alert', 'list_code_scanning_alerts',
    'get_secret_scanning_alert', 'list_secret_scanning_alerts'
  ],
  
  // Notifications (6 tools)
  notifications: [
    'list_notifications', 'get_notification_details', 'dismiss_notification',
    'mark_all_notifications_read', 'manage_notification_subscription',
    'manage_repository_notification_subscription'
  ]
} as const;

// Flatten all tools for easy lookup
export const ALL_GITHUB_MCP_TOOLS = Object.values(GITHUB_MCP_TOOL_CATEGORIES).flat();

export type GitHubMCPToolCategory = keyof typeof GITHUB_MCP_TOOL_CATEGORIES;
export type GitHubMCPTool = typeof ALL_GITHUB_MCP_TOOLS[number];

// Helper functions
export const isGitHubMCPTool = (toolName: string): boolean => {
  return ALL_GITHUB_MCP_TOOLS.includes(toolName as any);
};

export const getGitHubMCPToolCategory = (toolName: string): GitHubMCPToolCategory | null => {
  for (const [category, tools] of Object.entries(GITHUB_MCP_TOOL_CATEGORIES)) {
    if ((tools as readonly string[]).includes(toolName)) {
      return category as GitHubMCPToolCategory;
    }
  }
  return null;
};

export interface GitHubMCPResultProps {
  toolName: string;
  result: any;
  args?: any;
} 