import os
import sys

# Check if toto.txt exists in the repository root
repo_path = '/tmp/repo/496a3c45-2fa1-4fe4-b67b-4615e8b9da00'
toto_path = os.path.join(repo_path, 'toto.txt')

# Function to check file permissions
def check_permissions(file_path):
    if not os.access(file_path, os.R_OK):
        return "File is not readable."
    if not os.access(file_path, os.W_OK):
        return "File is not writable."
    return "File has read and write permissions."

# Check if file exists
if not os.path.exists(toto_path):
    print(f"FAILURE: File {toto_path} does not exist.")
    sys.exit(1)

print(f"SUCCESS: File {toto_path} exists.")

# Check if it's a file (not a directory or symlink)
if not os.path.isfile(toto_path):
    print(f"FAILURE: {toto_path} exists but is not a regular file.")
    sys.exit(1)

print(f"SUCCESS: {toto_path} is a regular file.")

# Check file permissions
permissions = check_permissions(toto_path)
print(f"INFO: {permissions}")

# Check file content
try:
    with open(toto_path, 'r') as f:
        content = f.read().strip()
    
    expected_content = "hello world"
    if content != expected_content:
        print(f"FAILURE: File content mismatch. Expected '{expected_content}', got '{content}'.")
        sys.exit(1)
    
    print(f"SUCCESS: File content is correct: '{content}'")
except Exception as e:
    print(f"FAILURE: Error reading file: {str(e)}")
    sys.exit(1)

print("All checks passed successfully!")