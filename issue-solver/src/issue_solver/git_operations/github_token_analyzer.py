import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Literal, Optional

try:
    import requests
except ImportError:
    # For testing purposes when requests is not available
    requests = None

from pydantic import BaseModel, Field


class FeatureStatus(str, Literal["available", "limited", "unavailable"]):
    pass


class FeatureCompatibility(BaseModel):
    code_search: FeatureStatus = Field(default="unavailable")
    issue_management: FeatureStatus = Field(default="unavailable")
    pull_request_creation: FeatureStatus = Field(default="unavailable")
    repository_indexing: FeatureStatus = Field(default="unavailable")
    workflow_triggers: FeatureStatus = Field(default="unavailable")


class TokenPermissionsResponse(BaseModel):
    scopes: List[str] = Field(default_factory=list, description="Current token scopes")
    expires_at: Optional[datetime] = Field(default=None, description="Token expiration date")
    rate_limit_remaining: int = Field(default=0, description="API calls remaining")
    rate_limit_reset_at: datetime = Field(default_factory=datetime.now, description="Rate limit reset time")
    feature_compatibility: FeatureCompatibility = Field(
        default_factory=FeatureCompatibility, description="Feature compatibility status"
    )
    missing_scopes: List[str] = Field(
        default_factory=list, description="Scopes needed for full functionality"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="User-friendly improvement suggestions"
    )
    optimal_scopes: List[str] = Field(
        default_factory=list, description="Recommended scopes for best experience"
    )


class GitHubTokenAnalyzer:
    """Service to analyze GitHub token permissions and capabilities."""

    # Mapping of features to required GitHub permissions
    FEATURE_REQUIREMENTS: Dict[str, List[str]] = {
        "code_search": ["repo"],
        "issue_management": ["repo", "issues:write"],
        "pull_request_creation": ["repo", "pull_requests:write"],
        "repository_indexing": ["repo", "contents:read"],
        "workflow_triggers": ["repo", "actions:write"]
    }

    # Optimal set of scopes for full functionality
    OPTIMAL_SCOPES = ["repo", "workflow", "read:user", "user:email"]

    def __init__(self, logger: Optional[logging.Logger] = None, test_mode: bool = False):
        self.logger = logger or logging.getLogger(__name__)
        self.test_mode = test_mode or (os.environ.get("GITHUB_TOKEN_ANALYZER_TEST_MODE") == "1")

    def analyze_token(self, access_token: str, repository_url: str) -> TokenPermissionsResponse:
        """
        Analyze a GitHub token for its permissions and capabilities.
        
        Args:
            access_token: GitHub personal access token
            repository_url: URL of the GitHub repository
        
        Returns:
            TokenPermissionsResponse: Analysis of token permissions and capabilities
        """
        try:
            self.logger.info(f"Analyzing token for repository: {repository_url}")
            
            # In test mode, return mock data instead of making real API calls
            if self.test_mode:
                return self._get_mock_token_analysis()
            
            # Initialize response
            response = TokenPermissionsResponse()
            
            # Extract owner and repo from URL
            repo_parts = repository_url.rstrip("/").split("/")
            if "github.com" in repo_parts:
                github_index = repo_parts.index("github.com")
                if len(repo_parts) >= github_index + 3:
                    owner = repo_parts[github_index + 1]
                    repo = repo_parts[github_index + 2].replace(".git", "")
                else:
                    self.logger.error(f"Invalid GitHub repository URL: {repository_url}")
                    return response
            else:
                self.logger.error(f"Not a GitHub repository URL: {repository_url}")
                return response
            
            # Set up headers for GitHub API requests
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Get token scopes from GitHub API
            user_response = requests.get("https://api.github.com/user", headers=headers)
            if "X-OAuth-Scopes" in user_response.headers:
                scopes_header = user_response.headers["X-OAuth-Scopes"]
                response.scopes = [scope.strip() for scope in scopes_header.split(",")] if scopes_header else []
            
            # Check rate limit status
            rate_limit_response = requests.get("https://api.github.com/rate_limit", headers=headers)
            if rate_limit_response.status_code == 200:
                rate_limit_data = rate_limit_response.json()
                response.rate_limit_remaining = rate_limit_data["resources"]["core"]["remaining"]
                reset_timestamp = rate_limit_data["resources"]["core"]["reset"]
                response.rate_limit_reset_at = datetime.fromtimestamp(reset_timestamp)
            
            # Test repository access
            repo_access_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}", headers=headers
            )
            repo_access = repo_access_response.status_code == 200
            
            # Analyze feature compatibility based on scopes
            response.feature_compatibility = self._analyze_feature_compatibility(response.scopes, repo_access)
            
            # Determine missing scopes
            response.missing_scopes = self._get_missing_scopes(response.scopes)
            
            # Generate recommendations
            response.recommendations = self._generate_recommendations(
                response.scopes, response.feature_compatibility, response.rate_limit_remaining
            )
            
            # Set optimal scopes
            response.optimal_scopes = self.OPTIMAL_SCOPES
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error analyzing GitHub token: {str(e)}")
            return TokenPermissionsResponse()
    
    def _get_mock_token_analysis(self) -> TokenPermissionsResponse:
        """Return mock token analysis data for testing purposes."""
        self.logger.info("Using mock data for token analysis (test mode)")
        
        # Create a response with mock data
        response = TokenPermissionsResponse(
            scopes=["repo", "read:user"],
            expires_at=None,  # No expiration
            rate_limit_remaining=4847,
            rate_limit_reset_at=datetime.now() + timedelta(hours=1),
            feature_compatibility=FeatureCompatibility(
                code_search="available",
                repository_indexing="available",
                issue_management="limited",
                pull_request_creation="limited",
                workflow_triggers="unavailable"
            ),
            missing_scopes=["workflow"],
            recommendations=[
                "Add 'workflow' scope for triggering GitHub Actions",
                "Add 'issues:write' scope to create and manage issues"
            ],
            optimal_scopes=self.OPTIMAL_SCOPES
        )
        
        return response
    
    def _analyze_feature_compatibility(
        self, scopes: List[str], repo_access: bool
    ) -> FeatureCompatibility:
        """Analyze which features are available with the current token scopes."""
        compatibility = FeatureCompatibility()
        
        if not repo_access:
            return compatibility
        
        # Helper function to check if all required scopes are present
        def has_required_scopes(required_scopes: List[str]) -> FeatureStatus:
            # Direct scope match
            if all(scope in scopes for scope in required_scopes):
                return "available"
            
            # Check for broader scopes that include the required ones
            if "repo" in scopes and any(scope.startswith("repo:") for scope in required_scopes):
                return "available"
            
            # Check for read-only access when write is required
            if all(
                scope in scopes or scope.replace(":write", ":read") in scopes
                for scope in required_scopes
            ):
                return "limited"
            
            # Check if at least basic repo access is available
            if "repo" in scopes or "repo:read" in scopes:
                return "limited"
                
            return "unavailable"
        
        # Analyze each feature
        for feature, required_scopes in self.FEATURE_REQUIREMENTS.items():
            setattr(compatibility, feature, has_required_scopes(required_scopes))
        
        return compatibility
    
    def _get_missing_scopes(self, current_scopes: List[str]) -> List[str]:
        """Determine which scopes are missing for full functionality."""
        missing_scopes = []
        
        # If 'repo' is present, it covers most functionality
        if "repo" in current_scopes:
            return missing_scopes
        
        # Check for missing scopes based on the optimal set
        for scope in self.OPTIMAL_SCOPES:
            if scope not in current_scopes and not any(
                s.startswith(f"{scope}:") for s in current_scopes
            ):
                missing_scopes.append(scope)
        
        return missing_scopes
    
    def _generate_recommendations(
        self, 
        scopes: List[str], 
        compatibility: FeatureCompatibility,
        rate_limit_remaining: int
    ) -> List[str]:
        """Generate actionable recommendations for token improvement."""
        recommendations = []
        
        # Recommend adding 'repo' scope if missing critical features
        if "repo" not in scopes and (
            compatibility.code_search != "available" or
            compatibility.repository_indexing != "available"
        ):
            recommendations.append(
                "Add 'repo' scope for full repository access (code search, PR creation, etc.)"
            )
        
        # Specific recommendations for limited features
        if compatibility.issue_management == "limited":
            recommendations.append(
                "Add 'issues:write' scope to create and manage issues"
            )
        
        if compatibility.pull_request_creation == "limited":
            recommendations.append(
                "Add 'pull_requests:write' scope to create pull requests"
            )
        
        if compatibility.workflow_triggers == "limited":
            recommendations.append(
                "Add 'actions:write' scope to trigger workflows"
            )
        
        # Rate limit recommendation
        if rate_limit_remaining < 1000:
            recommendations.append(
                "Your rate limit is running low. Consider using a token with higher rate limits."
            )
        
        return recommendations