import os

# Check if toto.txt exists in the repository root
repo_path = '/tmp/repo/496a3c45-2fa1-4fe4-b67b-4615e8b9da00'
toto_path = os.path.join(repo_path, 'toto.txt')

if os.path.exists(toto_path):
    print(f"File {toto_path} exists.")
    with open(toto_path, 'r') as f:
        content = f.read()
    print(f"Content: {content}")
else:
    print(f"File {toto_path} does not exist.")