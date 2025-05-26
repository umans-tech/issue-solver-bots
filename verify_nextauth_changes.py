#!/usr/bin/env python3
import os
import re

def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def check_adr():
    adr_path = os.path.join(os.getcwd(), 'docs', 'adr_001_nextauth_authentication.md')
    if not os.path.exists(adr_path):
        print(f"❌ ADR file not found at: {adr_path}")
        return False
    
    print(f"✅ ADR file exists at: {adr_path}")
    
    adr_content = read_file(adr_path)
    required_sections = ['Status', 'Context', 'Decision', 'Consequences']
    
    all_sections_present = True
    for section in required_sections:
        if not re.search(r'##\s+' + section, adr_content):
            print(f"❌ ADR is missing the required '{section}' section")
            all_sections_present = False
    
    if all_sections_present:
        print("✅ ADR follows the Nygard template with all required sections")
    
    # Check for social providers and email verification in ADR content
    if 'social provider' in adr_content and 'email verification' in adr_content:
        print("✅ ADR documents the decision to use social providers and email verification")
    else:
        print("❌ ADR is missing documentation about social providers or email verification")
        return False
    
    return True

def check_auth_implementation():
    auth_path = os.path.join(os.getcwd(), 'conversational-ui', 'app', '(auth)', 'auth.ts')
    if not os.path.exists(auth_path):
        print(f"❌ NextAuth.js implementation file not found at: {auth_path}")
        return False
    
    print(f"✅ NextAuth.js implementation file exists at: {auth_path}")
    
    auth_content = read_file(auth_path)
    required_providers = ['GoogleProvider', 'GitHubProvider', 'EmailProvider']
    
    all_providers_present = True
    for provider in required_providers:
        if provider not in auth_content:
            print(f"❌ Missing {provider} in auth.ts")
            all_providers_present = False
    
    if all_providers_present:
        print("✅ Social providers and email verification are implemented")
    else:
        return False
    
    return True

def check_types_declaration():
    types_path = os.path.join(os.getcwd(), 'conversational-ui', 'types', 'next-auth.d.ts')
    if not os.path.exists(types_path):
        print(f"❌ NextAuth.js TypeScript declarations file not found at: {types_path}")
        return False
    
    print(f"✅ NextAuth.js TypeScript declarations file exists at: {types_path}")
    
    types_content = read_file(types_path)
    required_fields = ['provider?', 'emailVerified?']
    
    all_fields_present = True
    for field in required_fields:
        if field not in types_content:
            print(f"❌ Type declarations are missing {field} field")
            all_fields_present = False
    
    if all_fields_present:
        print("✅ Type declarations support social providers and email verification")
    else:
        return False
    
    return True

def main():
    print("Verifying NextAuth.js implementation...\n")
    
    adr_check = check_adr()
    print("")
    auth_check = check_auth_implementation()
    print("")
    types_check = check_types_declaration()
    
    print("\nVerification complete!")
    
    if adr_check and auth_check and types_check:
        print("✅ All changes successfully implemented!")
    else:
        print("❌ Some issues were found. Please review the output above.")

if __name__ == "__main__":
    main()