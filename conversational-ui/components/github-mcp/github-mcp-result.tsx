import { useState } from 'react';
import { 
  ChevronDown, 
  ExternalLink, 
  MapPin, 
  Building, 
  Link, 
  Twitter, 
  Calendar,
  Star,
  GitFork,
  Eye
} from 'lucide-react';
import { GitIcon } from '../icons';
import { GitHubMCPResultProps, getGitHubMCPToolCategory } from './github-mcp-types';
import { getFileExtension, getLanguageIcon } from '../sources';

// Utility function to extract GitHub sources from MCP results
export const extractGitHubSources = (toolName: string, result: any, args: any): Array<{ sourceType: 'url'; id: string; url: string; title: string }> => {
  const sources: Array<{ sourceType: 'url'; id: string; url: string; title: string }> = [];
  
  try {
    // Extract data from MCP format if needed
    let data = result;
    if (result && result.content && Array.isArray(result.content) && result.content[0]?.text) {
      try {
        data = JSON.parse(result.content[0].text);
      } catch {
        data = result;
      }
    }

    switch (toolName) {
      case 'get_file_contents':
        if (data && typeof data === 'object') {
          const fileName = data.name || args?.path || 'Unknown file';
          const fileUrl = data.html_url || `https://github.com/search?q=filename:${encodeURIComponent(args?.path || fileName)}&type=code`;
          sources.push({
            sourceType: 'url',
            id: crypto.randomUUID(),
            url: fileUrl,
            title: fileName
          });
        }
        break;
        
      case 'search_code':
        if (Array.isArray(data)) {
          data.forEach((item: any) => {
            if (item.html_url && item.name) {
              sources.push({
                sourceType: 'url',
                id: crypto.randomUUID(),
                url: item.html_url,
                title: item.name
              });
            }
          });
        } else if (data && data.items && Array.isArray(data.items)) {
          data.items.forEach((item: any) => {
            if (item.html_url && item.name) {
              sources.push({
                sourceType: 'url',
                id: crypto.randomUUID(),
                url: item.html_url,
                title: item.name
              });
            }
          });
        }
        break;
        
      case 'get_issue':
        if (data && data.html_url && data.title) {
          sources.push({
            sourceType: 'url',
            id: crypto.randomUUID(),
            url: data.html_url,
            title: `Issue: ${data.title}`
          });
        }
        break;
        
      case 'get_pull_request':
        if (data && data.html_url && data.title) {
          sources.push({
            sourceType: 'url',
            id: crypto.randomUUID(),
            url: data.html_url,
            title: `PR: ${data.title}`
          });
        }
        break;
        
      case 'list_issues':
        if (Array.isArray(data)) {
          data.slice(0, 5).forEach((item: any) => { // Limit to first 5 to avoid too many sources
            if (item.html_url && item.title) {
              sources.push({
                sourceType: 'url',
                id: crypto.randomUUID(),
                url: item.html_url,
                title: `Issue: ${item.title}`
              });
            }
          });
        }
        break;
        
      case 'list_pull_requests':
        if (Array.isArray(data)) {
          data.slice(0, 5).forEach((item: any) => { // Limit to first 5 to avoid too many sources
            if (item.html_url && item.title) {
              sources.push({
                sourceType: 'url',
                id: crypto.randomUUID(),
                url: item.html_url,
                title: `PR: ${item.title}`
              });
            }
          });
        }
        break;
        
      case 'search_repositories':
      case 'list_repositories':
        if (Array.isArray(data)) {
          data.slice(0, 5).forEach((item: any) => { // Limit to first 5 to avoid too many sources
            if (item.html_url && item.full_name) {
              sources.push({
                sourceType: 'url',
                id: crypto.randomUUID(),
                url: item.html_url,
                title: `Repo: ${item.full_name}`
              });
            }
          });
        }
        break;
    }
  } catch (error) {
    console.warn('Error extracting GitHub sources:', error);
  }
  
  return sources;
};

export const GitHubMCPResult = ({ toolName, result, args }: GitHubMCPResultProps) => {

  const parts = Array.isArray(result?.content) ? result!.content! : [];
  let text_result = parts.find((p: any) => p?.type === 'text')?.text ?? null;
  let resource_result = parts.find((p: any) => p?.type === 'resource')?.resource ?? null;;

  if (text_result) {
    try{
      text_result = JSON.parse(text_result);
    } catch (error) {
      console.log('########### error');
      console.log(error);
    }
  }
  if (resource_result) {
    try{
      resource_result = JSON.parse(resource_result);
    } catch (error) {
      console.log('########### error');
      console.log(error);
    }
  }

  result = {
    text: text_result,
    resource: resource_result
  };


  const category = getGitHubMCPToolCategory(toolName);
  
  // Category-based result handling
  switch (category) {
    case 'users':
      return <GitHubUsersResult toolName={toolName} result={result.text} args={args} />;
    case 'issues':
      return <GitHubIssuesResult toolName={toolName} result={result.text} args={args} />;
    case 'pullRequests':
      return <GitHubPullRequestsResult toolName={toolName} result={result.text} args={args} />;
    case 'repositories':
      return <GitHubRepositoriesResult toolName={toolName} result={result} args={args} />;
    case 'actions':
      return <GitHubActionsResult toolName={toolName} result={result.text} args={args} />;
    case 'security':
      return <GitHubSecurityResult toolName={toolName} result={result.text} args={args} />;
    case 'notifications':
      return <GitHubNotificationsResult toolName={toolName} result={result.text} args={args} />;
    default:
      return <GitHubGenericResult toolName={toolName} result={result.text} args={args} />;
  }
};

// Category-specific result components

// Users category
const GitHubUsersResult = ({ toolName, result, args }: GitHubMCPResultProps) => {
  switch (toolName) {
    case 'get_me':
      return <GitHubUserProfile user={result} />;
    case 'search_users':
      return <GitHubUsersList users={result} query={args?.q} />;
    default:
      return <GitHubGenericResult toolName={toolName} result={result} args={args} />;
  }
};

// Issues category  
const GitHubIssuesResult = ({ toolName, result, args }: GitHubMCPResultProps) => {
  switch (toolName) {
    case 'list_issues':
      return <GitHubIssuesList issues={result} repository={`${args?.owner}/${args?.repo}`} />;
    case 'get_issue':
      return <GitHubIssueDetail issue={result} />;
    case 'create_issue':
      return <GitHubIssueDetail issue={result} />;
    case 'update_issue':
      return <GitHubIssueDetail issue={result} />;
    case 'search_issues':
      return <GitHubIssuesList issues={result} repository={`${args?.owner}/${args?.repo}`} />;
    default:
      return <GitHubGenericResult toolName={toolName} result={result} args={args} />;
  }
};

// Pull Requests category
const GitHubPullRequestsResult = ({ toolName, result, args }: GitHubMCPResultProps) => {
  switch (toolName) {
    case 'list_pull_requests':
      return <GitHubPullRequestsList pullRequests={result} repository={`${args?.owner}/${args?.repo}`} />;
    case 'get_pull_request':
      return <GitHubPullRequestDetail pullRequest={result} />;
    default:
      return <GitHubGenericResult toolName={toolName} result={result} args={args} />;
  }
};

// Repositories category
const GitHubRepositoriesResult = ({ toolName, result, args }: GitHubMCPResultProps) => {
  switch (toolName) {
    case 'search_repositories':
      return <GitHubRepositoriesList repositories={result.text} query={args?.query} />;
    case 'list_repositories':
      return <GitHubRepositoriesList repositories={result.text} />;
    case 'get_file_contents':
      return <GitHubFileContents file={result.resource} path={args?.path} />;
    case 'search_code':
      return <GitHubCodeSearchResults results={result.text} query={args?.query} />;
    default:
      return <GitHubGenericResult toolName={toolName} result={result.text} args={args} />;
  }
};

// Actions category
const GitHubActionsResult = ({ toolName, result, args }: GitHubMCPResultProps) => {
  switch (toolName) {
    case 'list_workflows':
      return <GitHubWorkflowsList workflows={result} repository={`${args?.owner}/${args?.repo}`} />;
    case 'list_workflow_runs':
      return <GitHubWorkflowRunsList runs={result} repository={`${args?.owner}/${args?.repo}`} />;
    default:
      return <GitHubGenericResult toolName={toolName} result={result} args={args} />;
  }
};

// Security category
const GitHubSecurityResult = ({ toolName, result, args }: GitHubMCPResultProps) => {
  switch (toolName) {
    case 'list_code_scanning_alerts':
      return <GitHubSecurityAlertsList alerts={result} type="Code Scanning" repository={`${args?.owner}/${args?.repo}`} />;
    case 'list_secret_scanning_alerts':
      return <GitHubSecurityAlertsList alerts={result} type="Secret Scanning" repository={`${args?.owner}/${args?.repo}`} />;
    default:
      return <GitHubGenericResult toolName={toolName} result={result} args={args} />;
  }
};

// Notifications category
const GitHubNotificationsResult = ({ toolName, result, args }: GitHubMCPResultProps) => {
  switch (toolName) {
    case 'list_notifications':
      return <GitHubNotificationsList notifications={result} />;
    default:
      return <GitHubGenericResult toolName={toolName} result={result} args={args} />;
  }
};

// Specific result components for individual tools

// User profile component  
const GitHubUserProfile = ({ user }: { user: any }) => {
  // Extract MCP content payload if present
  let userData = user;

  // Some payloads wrap the user data under { user: { ... } }
  if (userData && typeof userData === 'object' && (userData as any).user) {
    userData = (userData as any).user;
  }

  if (!userData || typeof userData !== 'object') {
    return <GitHubGenericResult toolName="get_me" result={user} />;
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  // Normalize commonly shifted fields coming from MCP
  const details = userData && typeof (userData as any).details === 'object' ? (userData as any).details : undefined;
  const publicRepos: number =
    typeof (userData as any).public_repos === 'number'
      ? (userData as any).public_repos
      : typeof details?.public_repos === 'number'
        ? details.public_repos
        : 0;
  const followers: number =
    typeof (userData as any).followers === 'number'
      ? (userData as any).followers
      : typeof details?.followers === 'number'
        ? details.followers
        : 0;
  const following: number =
    typeof (userData as any).following === 'number'
      ? (userData as any).following
      : typeof details?.following === 'number'
        ? details.following
        : 0;
  const createdAt: string | undefined = (userData as any).created_at ?? details?.created_at;
  const profileHref: string | undefined = (userData as any).html_url ?? (userData as any).profile_url;

  return (
    <div className="mt-1">
      <div className="flex items-center gap-2 text-sm mb-3">
        <GitIcon status="none" />
        <span className="text-muted-foreground">GitHub Profile</span>
      </div>
      
      <div className="border rounded-lg p-6 bg-card">
        {/* Header with avatar and basic info */}
        <div className="flex items-start gap-4 mb-4">
          {userData.avatar_url && (
            <img 
              src={userData.avatar_url} 
              alt="Profile Avatar" 
              className="w-16 h-16 rounded-full border-2 border-border" 
            />
          )}
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-foreground">
              {userData.name || userData.login}
            </h2>
            <p className="text-muted-foreground text-base mb-2">@{userData.login}</p>
            
            {userData.bio && (
              <p className="text-foreground text-sm leading-relaxed mb-3">
                {userData.bio}
              </p>
            )}
          </div>
        </div>

        {/* Profile details - Two column layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          <div className="space-y-3">
                      {userData.location && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <MapPin className="w-4 h-4" />
              <span>{userData.location}</span>
            </div>
          )}
            
            {userData.company && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Building className="w-4 h-4" />
                <span>{userData.company}</span>
              </div>
            )}

            {userData.blog && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Link className="w-4 h-4" />
                <a 
                  href={userData.blog.startsWith('http') ? userData.blog : `https://${userData.blog}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  {userData.blog}
                </a>
              </div>
            )}
          </div>

          <div className="space-y-3">
            {userData.twitter_username && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Twitter className="w-4 h-4" />
                <a
                  href={`https://twitter.com/${userData.twitter_username}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  @{userData.twitter_username}
                </a>
              </div>
            )}

            {createdAt && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="w-4 h-4" />
                <span>Joined {formatDate(createdAt)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="flex gap-6 text-sm">
          <div className="flex items-center gap-1">
            <span className="font-semibold text-foreground">{publicRepos}</span>
            <span className="text-muted-foreground">repositories</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="font-semibold text-foreground">{followers}</span>
            <span className="text-muted-foreground">followers</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="font-semibold text-foreground">{following}</span>
            <span className="text-muted-foreground">following</span>
          </div>
        </div>

        {/* View on GitHub link */}
        {typeof profileHref === 'string' && /^https?:\/\//.test(profileHref) && (
          <div className="mt-4 pt-4 border-t border-border">
            <a
              href={profileHref}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <span>View on GitHub</span>
              <ExternalLink size={14} />
            </a>
          </div>
        )}
      </div>
    </div>
  );
};

// For components that don't have specific implementations yet, create placeholders
const GitHubUsersList = ({ users, query }: { users: any; query?: string }) => (
  <GitHubGenericResult toolName="search_users" result={users} args={{ q: query }} />
);

const GitHubIssueDetail = ({ issue }: { issue: any }) => {
  // Use the same MCP content extraction logic
  let issueData = issue;
  
  if (!issueData || typeof issueData !== 'object') {
    return <GitHubGenericResult toolName="get_issue" result={issue} />;
  }

  return (
    <div className="mt-1">
      <div className="flex items-center gap-2 text-sm mb-2">
        <GitIcon status="none" />
        <span className="text-muted-foreground">GitHub Issue</span>
      </div>

      <a
        href={issueData.html_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block border rounded-lg p-4 bg-background hover:bg-muted/50 transition-colors cursor-pointer group"
      >
        <div className="flex items-start gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-medium text-base group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                {issueData.title}
              </h3>
              <span className="text-sm text-muted-foreground">#{issueData.number}</span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                issueData.state === 'open' 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' 
                  : 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'
              }`}>
                {issueData.state}
              </span>
            </div>
            
            {issueData.body && (
              <div className="text-sm text-muted-foreground mb-3 line-clamp-3">
                {issueData.body.length > 200 ? issueData.body.slice(0, 200) + '...' : issueData.body}
              </div>
            )}
            
            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
              <div className="flex items-center gap-2">
                {issueData.user?.avatar_url && (
                  <img 
                    src={issueData.user.avatar_url} 
                    alt={`@${issueData.user.login}`}
                    className="w-5 h-5 rounded-full"
                  />
                )}
                <span>@{issueData.user?.login}</span>
              </div>
              <span>opened {new Date(issueData.created_at).toLocaleDateString()}</span>
              {issueData.comments > 0 && (
                <span>{issueData.comments} comment{issueData.comments !== 1 ? 's' : ''}</span>
              )}
            </div>

            {issueData.labels && issueData.labels.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {issueData.labels.map((label: any) => (
                  <span 
                    key={label.id} 
                    className="px-2 py-0.5 rounded-full text-xs font-medium"
                    style={{ 
                      backgroundColor: `#${label.color}20`,
                      color: `#${label.color}`,
                      border: `1px solid #${label.color}40`
                    }}
                  >
                    {label.name}
                  </span>
                ))}
              </div>
            )}
          </div>
          
          <div className="text-muted-foreground group-hover:text-foreground transition-colors">
            <ExternalLink size={16} />
          </div>
        </div>
      </a>
    </div>
  );
};

const GitHubPullRequestsList = ({ pullRequests, repository }: { pullRequests: any; repository: string }) => {
  const [expanded, setExpanded] = useState(false);

  // Handle different response formats from GitHub MCP API (same logic as issues)
  let prsArray = pullRequests;

  if (!prsArray || prsArray.length === 0) {
    return null;
  }

  const displayedPRs = expanded ? prsArray : prsArray.slice(0, 3);

  return (
    <div className="mt-1">
      <div className="flex items-center gap-2 text-sm mb-2">
        <GitIcon status="none" />
        <span className="text-muted-foreground">
          Found {prsArray.length} pull request{prsArray.length !== 1 ? 's' : ''} in {repository}
        </span>
      </div>

      <div className="space-y-2">
        {displayedPRs.map((pr: any) => (
          <a
            key={pr.id}
            href={pr.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="block border rounded-lg p-3 bg-background hover:bg-muted/50 transition-colors cursor-pointer group"
          >
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-sm group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{pr.title}</h4>
                  <span className="text-xs text-muted-foreground">#{pr.number}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    pr.state === 'open' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' 
                      : pr.merged
                      ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                  }`}>
                    {pr.merged ? 'merged' : pr.state}
                  </span>
                </div>
                
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>@{pr.user?.login}</span>
                  <span>{new Date(pr.created_at).toLocaleDateString()}</span>
                  {pr.base && pr.head && (
                    <span>{pr.head.ref} → {pr.base.ref}</span>
                  )}
                  {pr.comments > 0 && (
                    <span>{pr.comments} comment{pr.comments !== 1 ? 's' : ''}</span>
                  )}
                </div>
              </div>
              
              <div className="text-muted-foreground group-hover:text-foreground transition-colors">
                <ExternalLink size={14} />
              </div>
            </div>
          </a>
        ))}
      </div>

      {prsArray.length > 3 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronDown 
            size={14} 
            className={`transition-transform ${expanded ? 'rotate-180' : ''}`} 
          />
          {expanded ? 'Show less' : `Show ${prsArray.length - 3} more PR${prsArray.length - 3 !== 1 ? 's' : ''}`}
        </button>
      )}
    </div>
  );
};

const GitHubPullRequestDetail = ({ pullRequest }: { pullRequest: any }) => {
  // Use the same MCP content extraction logic
  let prData = pullRequest;
  
  if (!prData || typeof prData !== 'object') {
    return <GitHubGenericResult toolName="get_pull_request" result={pullRequest} />;
  }

  return (
    <div className="mt-1">
      <div className="flex items-center gap-2 text-sm mb-2">
        <GitIcon status="none" />
        <span className="text-muted-foreground">GitHub Pull Request</span>
      </div>

      <a
        href={prData.html_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block border rounded-lg p-4 bg-background hover:bg-muted/50 transition-colors cursor-pointer group"
      >
        <div className="flex items-start gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-medium text-base group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                {prData.title}
              </h3>
              <span className="text-sm text-muted-foreground">#{prData.number}</span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                prData.state === 'open' 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' 
                  : prData.merged
                  ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'
                  : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
              }`}>
                {prData.merged ? 'merged' : prData.state}
              </span>
            </div>
            
            {prData.body && (
              <div className="text-sm text-muted-foreground mb-3 line-clamp-3">
                {prData.body.length > 200 ? prData.body.slice(0, 200) + '...' : prData.body}
              </div>
            )}
            
            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
              <div className="flex items-center gap-2">
                {prData.user?.avatar_url && (
                  <img 
                    src={prData.user.avatar_url} 
                    alt={`@${prData.user.login}`}
                    className="w-5 h-5 rounded-full"
                  />
                )}
                <span>@{prData.user?.login}</span>
              </div>
              <span>opened {new Date(prData.created_at).toLocaleDateString()}</span>
              {prData.base && prData.head && (
                <span className="font-mono text-xs bg-muted px-2 py-0.5 rounded">
                  {prData.head.ref} → {prData.base.ref}
                </span>
              )}
            </div>

            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              {prData.comments > 0 && (
                <span>{prData.comments} comment{prData.comments !== 1 ? 's' : ''}</span>
              )}
              {prData.commits && (
                <span>{prData.commits} commit{prData.commits !== 1 ? 's' : ''}</span>
              )}
              {prData.additions !== undefined && prData.deletions !== undefined && (
                <span className="flex items-center gap-1">
                  <span className="text-green-600">+{prData.additions}</span>
                  <span className="text-red-600">-{prData.deletions}</span>
                </span>
              )}
            </div>
          </div>
          
          <div className="text-muted-foreground group-hover:text-foreground transition-colors">
            <ExternalLink size={16} />
          </div>
        </div>
      </a>
    </div>
  );
};

const GitHubRepositoriesList = ({ repositories, query }: { repositories: any; query?: string }) => {
  const [expanded, setExpanded] = useState(false);

  // Handle different response formats from GitHub MCP API
  let reposArray = repositories.items;

  if (!reposArray || reposArray.length === 0) {
    return null;
  }

  const displayedRepos = expanded ? reposArray : reposArray.slice(0, 3);

  return (
    <div className="mt-1">
      <div className="flex items-center gap-2 text-sm mb-2">
        <GitIcon status="none" />
        <span className="text-muted-foreground">
          Found {reposArray.length} repositor{reposArray.length !== 1 ? 'ies' : 'y'}{query ? ` for "${query}"` : ''}
        </span>
      </div>

      <div className="space-y-2">
        {displayedRepos.map((repo: any) => (
          <a
            key={repo.id}
            href={repo.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="block border rounded-lg p-3 bg-background hover:bg-muted/50 transition-colors cursor-pointer group"
          >
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-sm group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {String(repo.full_name || repo.name || 'Unknown repository')}
                  </h4>
                  {repo.private && (
                    <span className="px-2 py-0.5 rounded text-xs bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
                      private
                    </span>
                  )}
                  {repo.fork && (
                    <span className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400">
                      fork
                    </span>
                  )}
                </div>
                
                {repo.description && (
                  <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                    {String(repo.description)}
                  </p>
                )}
                
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  {repo.language && (
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                      {String(repo.language)}
                    </span>
                  )}
                  {repo.stargazers_count !== undefined && (
                    <span className="flex items-center gap-1">
                      <Star className="w-3 h-3" />
                      {String(repo.stargazers_count)}
                    </span>
                  )}
                  {repo.forks_count !== undefined && (
                    <span className="flex items-center gap-1">
                      <GitFork className="w-3 h-3" />
                      {String(repo.forks_count)}
                    </span>
                  )}
                  {repo.updated_at && (
                    <span>Updated {new Date(repo.updated_at).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
              
              <div className="text-muted-foreground group-hover:text-foreground transition-colors">
                <ExternalLink size={14} />
              </div>
            </div>
          </a>
        ))}
      </div>

      {reposArray.length > 3 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronDown 
            size={14} 
            className={`transition-transform ${expanded ? 'rotate-180' : ''}`} 
          />
          {expanded ? 'Show less' : `Show ${reposArray.length - 3} more repositor${reposArray.length - 3 !== 1 ? 'ies' : 'y'}`}
        </button>
      )}
    </div>
  );
};

// Component to handle multiple file contents
const GitHubMultipleFileContents = ({ files }: { files: any[] }) => {
  const [expanded, setExpanded] = useState(false);
  
  const displayedFiles = expanded ? files : files.slice(0, 3);
  
  return (
    <div className="mt-1">
      <div className="flex items-center gap-2 text-sm mb-1">
        <GitIcon status="none" />
        <span className="text-muted-foreground">Retrieved {files.length} file{files.length !== 1 ? 's' : ''}</span>
      </div>
      
      {!expanded ? (
        <div 
          className="inline-flex h-8 items-center rounded-full border border-border bg-background px-3 text-sm font-medium gap-1.5 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => setExpanded(true)}
        >
          {displayedFiles.map((fileItem: any, index: number) => {
            const fileName = fileItem.name || fileItem.path || `File ${index + 1}`;
            const extension = getFileExtension(fileName);
            const languageIcon = getLanguageIcon(extension);
            
            return (
              <div key={index} className="flex items-center">
                {languageIcon ? (
                  <img 
                    src={languageIcon} 
                    alt={`${extension} file`} 
                    className="w-4 h-4 rounded-sm" 
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-4 h-4 rounded-sm bg-primary/10 flex items-center justify-center">
                    <svg 
                      width="10" 
                      height="10" 
                      viewBox="0 0 24 24" 
                      fill="none" 
                      xmlns="http://www.w3.org/2000/svg"
                      className="text-primary"
                    >
                      <path 
                        d="M7 8L3 12L7 16M17 8L21 12L17 16M14 4L10 20" 
                        stroke="currentColor" 
                        strokeWidth="2" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                )}
              </div>
            );
          })}
          <span className="text-xs font-medium text-muted-foreground">
            {files.length} file{files.length !== 1 ? 's' : ''}
          </span>
        </div>
      ) : (
        <div className="rounded-md border border-border overflow-hidden bg-background">
          <div 
            className="py-1.5 px-3 border-b border-border/50 flex items-center cursor-pointer hover:bg-muted/10 transition-colors"
            onClick={() => setExpanded(false)}
          >
            <div className="flex items-center gap-1.5 flex-grow">
              <span className="text-xs font-medium text-muted-foreground">File Contents</span>
            </div>
            <button 
              className="text-xs text-muted-foreground hover:text-foreground p-1 rounded hover:bg-muted/50"
              aria-label="Close file contents"
              onClick={(e) => {
                e.stopPropagation();
                setExpanded(false);
              }}
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                width="14" 
                height="14" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              >
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div className="space-y-3 p-3">
            {displayedFiles.map((fileItem: any, index: number) => (
              <GitHubSingleFileDisplay key={index} fileData={fileItem} />
            ))}
          </div>
          
          {files.length > 3 && (
            <div className="border-t border-border/50 p-3">
              <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
              >
                <ChevronDown 
                  size={14} 
                  className={`transition-transform ${expanded ? 'rotate-180' : ''}`} 
                />
                {expanded ? 'Show less' : `Show ${files.length - 3} more file${files.length - 3 !== 1 ? 's' : ''}`}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Component to display a single file's content
const GitHubSingleFileDisplay = ({ fileData }: { fileData: any }) => {
  let actualContent = '';
  let fileName = fileData.name || fileData.path || 'Unknown file';
  let fileUrl = fileData.html_url || '';
  let fileSize = fileData.size || 0;
  
  if (fileData.content) {
    const isBase64 = fileData.encoding === 'base64';
    const isText = fileData.encoding === 'text';
    
    try {
      if (isBase64) {
        actualContent = atob(fileData.content.replace(/\n/g, ''));
      } else if (isText) {
        actualContent = fileData.content;
      } else {
        actualContent = fileData.content;
      }
    } catch (error) {
      // Error decoding - return null like codebase search
      return null;
    }
  }
  
  const getFileType = (name: string) => {
    const ext = name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'js': case 'jsx': return 'javascript';
      case 'ts': case 'tsx': return 'typescript';
      case 'py': return 'python';
      case 'json': return 'json';
      case 'md': return 'markdown';
      case 'yml': case 'yaml': return 'yaml';
      case 'xml': return 'xml';
      case 'css': return 'css';
      case 'html': return 'html';
      default: return 'text';
    }
  };

  const fileType = getFileType(fileName);
  const extension = getFileExtension(fileName);
  const languageIcon = getLanguageIcon(extension);
  const githubUrl = fileUrl || `https://github.com/search?q=filename:${encodeURIComponent(fileName)}&type=code`;

  return (
    <div className="border rounded-lg p-3 bg-background">
      <div className="flex items-start gap-2">
        <div className="flex-shrink-0 mt-0.5">
          {languageIcon ? (
            <img 
              src={languageIcon} 
              alt={`${extension} file`} 
              className="w-5 h-5 rounded-sm" 
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          ) : (
            <div className="w-5 h-5 rounded-sm bg-primary/10 flex items-center justify-center">
              <svg 
                width="12" 
                height="12" 
                viewBox="0 0 24 24" 
                fill="none" 
                xmlns="http://www.w3.org/2000/svg"
                className="text-primary"
              >
                <path 
                  d="M7 8L3 12L7 16M17 8L21 12L17 16M14 4L10 20" 
                  stroke="currentColor" 
                  strokeWidth="2" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          )}
        </div>
        <div className="flex flex-col gap-0 flex-grow">
          <div className="flex items-center gap-2 mb-1">
            <a 
              href={githubUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-base font-medium text-primary hover:underline line-clamp-1"
            >
              {fileName}
            </a>
            {fileSize > 0 && (
              <span className="text-xs text-muted-foreground">
                ({fileSize > 1024 ? `${(fileSize / 1024).toFixed(1)}KB` : `${fileSize}B`})
              </span>
            )}
            <span className="text-xs bg-muted px-2 py-0.5 rounded">{fileType}</span>
          </div>
          
          {actualContent ? (
            <div className="text-sm bg-muted/20 p-3 rounded font-mono overflow-auto max-h-64">
              <pre className="whitespace-pre-wrap">{actualContent}</pre>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">
              No content available
            </div>
          )}
          
          <div className="text-xs text-muted-foreground mt-2">
            {githubUrl}
          </div>
        </div>
      </div>
    </div>
  );
};

const GitHubFileContents = ({ file, path }: { file: any; path?: string }) => {
  const [expanded, setExpanded] = useState(false);
  
  // Extract file content from MCP response
  let fileData = file;
  let errorMessage = '';

  // let uri = fileData.uri
  // let mimeType = fileData.mimeType
  // let content = fileData.text

  // Handle multiple files case
  if (Array.isArray(fileData) && fileData.length > 0) {
    return <GitHubMultipleFileContents files={fileData} />;
  }

  // Handle single file case
  let actualContent = '';
  let fileName = path || 'Unknown file';
  let fileUrl = '';
  let fileSize = 0;
  
  // Handle error case - return null like codebase search
  if (errorMessage) {
    return null;
  }
  
  if (fileData && typeof fileData === 'object') {
    // GitHub API returns file content in 'content' field, usually base64 encoded
    if (fileData.content) {
      const isBase64 = fileData.encoding === 'base64';
      const isText = fileData.encoding === 'text';
      
      try {
        if (isBase64) {
          actualContent = atob(fileData.content.replace(/\n/g, ''));
        } else if (isText) {
          actualContent = fileData.content;
        } else {
          // Default handling
          actualContent = fileData.content;
        }
      } catch (error) {
        // Error decoding - return null like codebase search
        return null;
      }
    }
    
    fileName = fileData.name || path || 'Unknown file';
    fileUrl = fileData.uri || '';
    fileSize = fileData.size || 0;
  } else if (typeof fileData === 'string') {
    actualContent = fileData;
  } else if (fileData === null) {
    // No file data - return null like codebase search
    return null;
  } else {
    // Debug: show the raw data structure if we can't parse it
    actualContent = `Debug: ${JSON.stringify(fileData, null, 2)}`;
  }

  // Determine file type for syntax highlighting hint
  const getFileType = (name: string) => {
    const ext = name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'js': case 'jsx': return 'javascript';
      case 'ts': case 'tsx': return 'typescript';
      case 'py': return 'python';
      case 'json': return 'json';
      case 'md': return 'markdown';
      case 'yml': case 'yaml': return 'yaml';
      case 'xml': return 'xml';
      case 'css': return 'css';
      case 'html': return 'html';
      default: return 'text';
    }
  };

  const fileType = getFileType(fileName);
  const extension = getFileExtension(fileName);
  const languageIcon = getLanguageIcon(extension);
  const githubUrl = fileUrl || `https://github.com/search?q=filename:${encodeURIComponent(path || fileName)}&type=code`;

  return (
    <div className="mt-1">
      <div className="flex items-center gap-2 text-sm mb-1">
        <GitIcon status="none" />
        <span className="text-muted-foreground">Retrieved file contents: "{path || fileName}"</span>
      </div>
      
      {!expanded ? (
        <div 
          className="inline-flex h-8 items-center rounded-full border border-border bg-background px-3 text-sm font-medium gap-1.5 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => setExpanded(true)}
        >
          <div className="flex items-center">
            {languageIcon ? (
              <img 
                src={languageIcon} 
                alt={`${extension} file`} 
                className="w-4 h-4 rounded-sm" 
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            ) : (
              <div className="w-4 h-4 rounded-sm bg-primary/10 flex items-center justify-center">
                <svg 
                  width="10" 
                  height="10" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  xmlns="http://www.w3.org/2000/svg"
                  className="text-primary"
                >
                  <path 
                    d="M7 8L3 12L7 16M17 8L21 12L17 16M14 4L10 20" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
            )}
          </div>
          <span className="text-xs font-medium text-muted-foreground">
            {fileName}
          </span>
        </div>
      ) : (
        <div className="rounded-md border border-border overflow-hidden bg-background">
          <div 
            className="py-1.5 px-3 border-b border-border/50 flex items-center cursor-pointer hover:bg-muted/10 transition-colors"
            onClick={() => setExpanded(false)}
          >
            <div className="flex items-center gap-1.5 flex-grow">
              <span className="text-xs font-medium text-muted-foreground">File Contents</span>
            </div>
            <button 
              className="text-xs text-muted-foreground hover:text-foreground p-1 rounded hover:bg-muted/50"
              aria-label="Close file contents"
              onClick={(e) => {
                e.stopPropagation();
                setExpanded(false);
              }}
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                width="14" 
                height="14" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              >
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div className="flex flex-col gap-1 p-3">
            <div className="flex items-start gap-2">
              <div className="flex-shrink-0 mt-0.5">
                {languageIcon ? (
                  <img 
                    src={languageIcon} 
                    alt={`${extension} file`} 
                    className="w-5 h-5 rounded-sm" 
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-5 h-5 rounded-sm bg-primary/10 flex items-center justify-center">
                    <svg 
                      width="12" 
                      height="12" 
                      viewBox="0 0 24 24" 
                      fill="none" 
                      xmlns="http://www.w3.org/2000/svg"
                      className="text-primary"
                    >
                      <path 
                        d="M7 8L3 12L7 16M17 8L21 12L17 16M14 4L10 20" 
                        stroke="currentColor" 
                        strokeWidth="2" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                )}
              </div>
              <div className="flex flex-col gap-0 flex-grow">
                <div className="flex items-center gap-2 mb-1">
                  <a 
                    href={githubUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-base font-medium text-primary hover:underline line-clamp-1"
                  >
                    {fileName}
                  </a>
                  {fileSize > 0 && (
                    <span className="text-xs text-muted-foreground">
                      ({fileSize > 1024 ? `${(fileSize / 1024).toFixed(1)}KB` : `${fileSize}B`})
                    </span>
                  )}
                  <span className="text-xs bg-muted px-2 py-0.5 rounded">{fileType}</span>
                </div>
                
                {actualContent && actualContent.startsWith('Error:') ? (
                  <div className="text-sm text-red-600 dark:text-red-400 mb-2">
                    {actualContent.replace('Error: ', '')}
                  </div>
                ) : actualContent && !actualContent.startsWith('Debug:') ? (
                  <div className="text-sm bg-muted/20 p-3 rounded font-mono overflow-auto max-h-96">
                    <pre className="whitespace-pre-wrap">{actualContent}</pre>
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground">
                    {actualContent ? 'Binary file or no preview available' : 'No content available'}
                  </div>
                )}
                
                <div className="text-xs text-muted-foreground mt-2">
                  {githubUrl}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const GitHubCodeSearchResults = ({ results, query }: { results: any; query?: string }) => {
  const [expanded, setExpanded] = useState(false);

  // Handle different response formats from GitHub MCP API
  let resultsArray = results.items;

  if (!resultsArray || resultsArray.length === 0) {
    return null;
  }

  const displayedResults = expanded ? resultsArray : resultsArray.slice(0, 3);

  return (
    <div className="mt-1">
      <div className="flex items-center gap-2 text-sm mb-2">
        <GitIcon status="none" />
        <span className="text-muted-foreground">
          Found {resultsArray.length} code result{resultsArray.length !== 1 ? 's' : ''}{query ? ` for "${query}"` : ''}
        </span>
      </div>

      <div className="space-y-2">
        {displayedResults.map((result: any, index: number) => (
          <a
            key={result.sha || index}
            href={result.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="block border rounded-lg p-3 bg-background hover:bg-muted/50 transition-colors cursor-pointer group"
          >
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-sm group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {String(result.name || 'Unknown file')}
                  </h4>
                  <span className="text-xs text-muted-foreground font-mono">
                    {String(result.repository?.full_name || '')}
                  </span>
                </div>
                
                <div className="text-xs text-muted-foreground mb-2">
                  {String(result.path || '')}
                </div>

                {result.text_matches && result.text_matches.length > 0 && (
                  <div className="text-xs bg-muted/50 p-2 rounded font-mono overflow-hidden">
                    {typeof result.text_matches[0].fragment === 'string' 
                      ? result.text_matches[0].fragment 
                      : JSON.stringify(result.text_matches[0].fragment)
                    }
                  </div>
                )}
              </div>
              
              <div className="text-muted-foreground group-hover:text-foreground transition-colors">
                <ExternalLink size={14} />
              </div>
            </div>
          </a>
        ))}
      </div>

      {resultsArray.length > 3 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronDown 
            size={14} 
            className={`transition-transform ${expanded ? 'rotate-180' : ''}`} 
          />
          {expanded ? 'Show less' : `Show ${resultsArray.length - 3} more result${resultsArray.length - 3 !== 1 ? 's' : ''}`}
        </button>
      )}
    </div>
  );
};

const GitHubWorkflowsList = ({ workflows, repository }: { workflows: any; repository: string }) => (
  <GitHubGenericResult toolName="list_workflows" result={workflows} args={{ repository }} />
);

const GitHubWorkflowRunsList = ({ runs, repository }: { runs: any; repository: string }) => (
  <GitHubGenericResult toolName="list_workflow_runs" result={runs} args={{ repository }} />
);

const GitHubSecurityAlertsList = ({ alerts, type, repository }: { alerts: any; type: string; repository: string }) => (
  <GitHubGenericResult toolName="list_security_alerts" result={alerts} args={{ type, repository }} />
);

const GitHubNotificationsList = ({ notifications }: { notifications: any }) => (
  <GitHubGenericResult toolName="list_notifications" result={notifications} />
);

function issueWebUrl(issue: any, owner: string, repo: string) {
  // prefer direct fields if they exist on other servers
  const direct = issue?.html_url ?? issue?.url;
  if (direct) return direct;

  // REST "issues" may include PRs; those have a `pull_request` field
  const path = issue?.pull_request ? 'pull' : 'issues';
  return issue?.number ? `https://github.com/${owner}/${repo}/${path}/${issue.number}` : null;
}

// Existing issues list component (renamed for consistency)
const GitHubIssuesList = ({ issues, repository }: { issues: any; repository: string }) => {
  const [expanded, setExpanded] = useState(false);

  // Handle different response formats from GitHub MCP API
  let issuesArray = issues.issues;

  if (!issuesArray || issuesArray.length === 0) {
    return null;
  }

  const displayedIssues = expanded ? issuesArray : issuesArray.slice(0, 3);

  return (
    <div className="mt-1">
      <div className="flex items-center gap-2 text-sm mb-2">
        <GitIcon status="none" />
        <span className="text-muted-foreground">
          Found {issuesArray.length} issue{issuesArray.length !== 1 ? 's' : ''} in {repository}
        </span>
      </div>

      <div className="space-y-2">
        {displayedIssues.map((issue: any) => (
          <a
            key={issue.id}
            href={issueWebUrl(issue, repository.split('/')[0], repository.split('/')[1])}
            target="_blank"
            rel="noopener noreferrer"
            className="block border rounded-lg p-3 bg-background hover:bg-muted/50 transition-colors cursor-pointer group"
          >
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-sm group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{issue.title}</h4>
                  <span className="text-xs text-muted-foreground">#{issue.number}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    issue.state === 'open' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' 
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
                  }`}>
                    {issue.state}
                  </span>
                </div>
                
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>@{issue.user?.login}</span>
                  <span>{new Date(issue.created_at).toLocaleDateString()}</span>
                  {issue.labels?.length > 0 && (
                    <div className="flex gap-1">
                      {issue.labels.slice(0, 2).map((label: any) => (
                        <span 
                          key={label.id} 
                          className="px-1.5 py-0.5 rounded text-xs"
                          style={{ 
                            backgroundColor: `#${label.color}20`,
                            color: `#${label.color}`,
                            border: `1px solid #${label.color}30`
                          }}
                        >
                          {label.name}
                        </span>
                      ))}
                      {issue.labels.length > 2 && (
                        <span className="text-xs text-muted-foreground">
                          +{issue.labels.length - 2} more
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="text-muted-foreground group-hover:text-foreground transition-colors">
                <ExternalLink size={14} />
              </div>
            </div>
          </a>
        ))}
      </div>

      {issuesArray.length > 3 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronDown 
            size={14} 
            className={`transition-transform ${expanded ? 'rotate-180' : ''}`} 
          />
          {expanded ? 'Show less' : `Show ${issuesArray.length - 3} more issue${issuesArray.length - 3 !== 1 ? 's' : ''}`}
        </button>
      )}
    </div>
  );
};

// Generic fallback for other GitHub MCP tools
const GitHubGenericResult = ({ toolName, result }: { toolName: string; result: any; args?: any }) => {
  const [expanded, setExpanded] = useState(false);

  const processedResult = result;
  
  // Get a human-readable preview
  const getPreview = () => {
    if (typeof processedResult === 'string') {
      return processedResult.length > 100 ? processedResult.slice(0, 100) + '...' : processedResult;
    }
    if (typeof processedResult === 'object' && processedResult !== null) {
      // Try to extract meaningful info for common GitHub objects
      if (processedResult.login) {
        return `User: ${processedResult.login} (${processedResult.name || 'No name'})`;
      }
      if (processedResult.full_name) {
        return `Repository: ${processedResult.full_name}`;
      }
      if (Array.isArray(processedResult)) {
        return `Array with ${processedResult.length} items`;
      }
      return 'View result details';
    }
    return String(processedResult);
  };

  const formatContent = () => {
    if (typeof processedResult === 'string') {
      return processedResult;
    }
    return JSON.stringify(processedResult, null, 2);
  };

  return (
    <div className="mt-1">
      <div className="flex items-center gap-2 text-sm mb-2">
        <GitIcon status="none" />
        <span className="text-muted-foreground">GitHub {toolName.replace('_', ' ')}</span>
      </div>

      {!expanded ? (
        <div 
          className="inline-flex h-8 items-center rounded-full border border-border bg-background px-3 text-sm font-medium gap-1.5 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => setExpanded(true)}
        >
          <span className="text-xs text-muted-foreground">
            {getPreview()}
          </span>
        </div>
      ) : (
        <div className="rounded-md border border-border overflow-hidden bg-background">
          <div 
            className="py-1.5 px-3 border-b border-border/50 flex items-center cursor-pointer hover:bg-muted/10 transition-colors"
            onClick={() => setExpanded(false)}
          >
            <span className="text-xs font-medium text-muted-foreground flex-grow">
              {toolName.replace('_', ' ')} result
            </span>
            <ChevronDown size={14} className="text-muted-foreground rotate-180" />
          </div>
          <div className="p-3">
            <pre className="text-sm overflow-auto max-h-96 bg-muted/20 p-3 rounded">
              {formatContent()}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}; 
