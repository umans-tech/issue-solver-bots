#!/usr/bin/env python3
"""
This script verifies that the README.md file contains all the required sections
as specified in the PR description.
"""

import re
import sys
from pathlib import Path

# Required sections from the PR description
REQUIRED_SECTIONS = [
    "Project Structure Overview",
    "System Architecture",
    "Component Details",
    "Directory Structure",
    "Deployment Architecture",
    "Key Workflows",
    "Onboarding Guide",
    "Getting Started",
    "Next Steps"
]

# Check for Mermaid diagrams
MERMAID_REQUIRED = True

def main():
    """Check the README for required sections and features."""
    readme_path = Path("/tmp/repo/d8eee309-e9e0-494f-abd6-32ddbd43bc59/README.md")
    
    if not readme_path.exists():
        print(f"ERROR: README file not found at {readme_path}")
        return 1
    
    content = readme_path.read_text()
    
    # Check for required sections
    missing_sections = []
    for section in REQUIRED_SECTIONS:
        pattern = rf"## {section}"
        if not re.search(pattern, content):
            missing_sections.append(section)
    
    # Check for Mermaid diagrams
    has_mermaid = "```mermaid" in content
    
    # Print results
    print("README.md Update Verification Results:")
    print("-" * 40)
    
    if missing_sections:
        print("❌ Missing required sections:")
        for section in missing_sections:
            print(f"  - {section}")
    else:
        print("✅ All required sections are present!")
    
    if MERMAID_REQUIRED:
        if has_mermaid:
            print("✅ Mermaid diagrams are included!")
        else:
            print("❌ Mermaid diagrams are missing!")
    
    # Check component explanations
    if "Conversational-UI" in content and "Issue-Solver" in content:
        print("✅ Both main components (Conversational-UI and Issue-Solver) are explained!")
    else:
        print("❌ One or both main components are not explained!")
    
    # Return success if all checks pass
    if not missing_sections and has_mermaid and "Conversational-UI" in content and "Issue-Solver" in content:
        print("\n🎉 All requirements for the README update have been met!")
        return 0
    else:
        print("\n⚠️ Some requirements for the README update are not met!")
        return 1

if __name__ == "__main__":
    sys.exit(main())