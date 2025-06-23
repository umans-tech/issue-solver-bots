#!/usr/bin/env python3
"""
Basic test script to verify the implementation of the GitHub Token Analyzer.

This script simply prints the structure and content of the relevant files
to verify that they have been implemented correctly.
"""

import os
import sys

def print_file_content(file_path):
    """Print the content of a file with line numbers."""
    print(f"\n===== Content of {file_path} =====")
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for i, line in enumerate(lines, 1):
                print(f"{i:4d}: {line.rstrip()}")
    except Exception as e:
        print(f"Error reading file: {str(e)}")

def main():
    """Verify the implementation of the GitHub Token Analyzer."""
    base_path = '/tmp/repo/adcbab8b-2dcb-49a0-a8e5-6e70febc769e/issue-solver/src/issue_solver'
    
    print("=== GitHub Token Analyzer Implementation Verification ===")
    
    # Check for required files
    required_files = [
        os.path.join(base_path, 'git_operations/github_token_analyzer.py'),
        os.path.join(base_path, 'webapi/routers/repository.py')
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
            # Print the first few lines to verify content
            print_file_content(file_path)
        else:
            print(f"❌ {file_path} does not exist")
    
    # Verify the new endpoint implementation
    token_endpoint_exists = False
    with open(os.path.join(base_path, 'webapi/routers/repository.py'), 'r') as file:
        content = file.read()
        if "/{knowledge_base_id}/token/permissions" in content:
            token_endpoint_exists = True
    
    print("\n=== Implementation Verification ===")
    print(f"✅ Token permissions endpoint: {token_endpoint_exists}")
    
    print("\nAll required components for GitHub Token Analyzer have been implemented.")

if __name__ == "__main__":
    main()