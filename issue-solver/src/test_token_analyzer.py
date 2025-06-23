#!/usr/bin/env python3
"""
Test script for GitHub Token Analyzer functionality.

This script creates a mock GitHub token and repository URL, then calls the GitHubTokenAnalyzer
to test the token analysis functionality.
"""

import json
import logging
import sys
from datetime import datetime

# Add the src directory to the Python path
sys.path.append('/tmp/repo/adcbab8b-2dcb-49a0-a8e5-6e70febc769e/issue-solver/src')

from issue_solver.git_operations.github_token_analyzer import GitHubTokenAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_datetime(dt):
    """Format datetime objects for JSON serialization."""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return dt

def main():
    """Run the test for GitHubTokenAnalyzer."""
    logger.info("Testing GitHub Token Analyzer")
    
    # Create a mock token and repository URL
    mock_token = "github_pat_mock_token123456789"
    mock_repo_url = "https://github.com/username/repository"
    
    # Initialize the analyzer with test mode enabled
    analyzer = GitHubTokenAnalyzer(logger=logger, test_mode=True)
    
    try:
        # Using test mode to avoid actual API calls to GitHub
        logger.info(f"Analyzing token for repository: {mock_repo_url}")
        token_analysis = analyzer.analyze_token(mock_token, mock_repo_url)
        
        # Convert to dict for better display
        analysis_dict = token_analysis.model_dump()
        
        # Convert datetime objects to strings for display
        for key, value in analysis_dict.items():
            if isinstance(value, datetime):
                analysis_dict[key] = format_datetime(value)
        
        # Print the analysis result
        logger.info("Token Analysis Result:")
        print(json.dumps(analysis_dict, indent=2, default=format_datetime))
        
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        raise

if __name__ == "__main__":
    main()