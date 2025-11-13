import { GitIcon } from '../icons';
import { getGitHubMCPToolCategory } from './github-mcp-types';

export const GitHubMCPAnimation = ({ toolName, args }: { toolName: string; args?: any }) => {
  const category = getGitHubMCPToolCategory(toolName);
  
  // Category-based animation configurations
  const getCategoryConfig = () => {
    switch (category) {
      case 'users':
        return {
          defaultText: 'Fetching user information...'
        };
      case 'issues':
        return {
          defaultText: 'Processing issue...'
        };
      case 'pullRequests':
        return {
          defaultText: 'Handling pull request...'
        };
      case 'repositories':
        return {
          defaultText: 'Accessing repository...'
        };
      case 'actions':
        return {
          defaultText: 'Managing workflow...'
        };
      case 'security':
        return {
          defaultText: 'Checking security...'
        };
      case 'notifications':
        return {
          defaultText: 'Managing notifications...'
        };
      default:
        return {
          defaultText: 'Processing GitHub request...'
        };
    }
  };

  // Specific tool customizations within categories
  const getSpecificText = () => {
    const categoryConfig = getCategoryConfig();
    
    switch (toolName) {
      // Users
      case 'get_me':
        return 'Getting your GitHub profile...';
      case 'search_users':
        return `Searching for users: "${args?.q}"...`;
      
      // Issues  
      case 'list_issues':
        return `Loading issues from ${args?.owner}/${args?.repo}...`;
      case 'issue_read': {
        const method = (args?.method ?? 'get').toLowerCase();
        if (method === 'get_comments') {
          return `Fetching comments for issue #${args?.issue_number ?? args?.number}...`;
        }
        return `Fetching issue #${args?.issue_number ?? args?.number}...`;
      }
      case 'issue_write': {
        const method = (args?.method ?? 'create').toLowerCase();
        if (method === 'update') {
          return `Updating issue #${args?.issue_number ?? args?.number}...`;
        }
        return 'Creating new issue...';
      }
      case 'search_issues':
        return `Searching issues: "${args?.query}"...`;
      
      // Pull Requests
      case 'list_pull_requests':
        return `Loading pull requests from ${args?.owner}/${args?.repo}...`;
      case 'get_pull_request':
        return `Fetching pull request #${args?.pullNumber}...`;
      case 'create_pull_request':
        return 'Creating pull request...';
      
      // Repositories
      case 'search_code':
        return `Searching code for "${args?.query}"...`;
      case 'get_file_contents':
        return `Reading ${args?.path}...`;
      case 'list_repositories':
        return 'Loading repositories...';
      case 'search_repositories':
        return `Searching repositories: "${args?.query}"...`;
      
      // Actions
      case 'list_workflows':
        return `Loading workflows from ${args?.owner}/${args?.repo}...`;
      case 'run_workflow':
        return `Triggering workflow: ${args?.workflow_id}...`;
      
      // Security
      case 'list_code_scanning_alerts':
        return 'Checking code scanning alerts...';
      case 'list_secret_scanning_alerts':
        return 'Checking secret scanning alerts...';
      
      // Notifications
      case 'list_notifications':
        return 'Loading your notifications...';
      
      default:
        return categoryConfig.defaultText;
    }
  };

  const text = getSpecificText();

  return (
    <div className="flex flex-col w-full">
      <div className="text-muted-foreground flex items-center gap-2">
        <GitIcon status="none" />
        <span className="animate-pulse">{text}</span>
      </div>
    </div>
  );
}; 
