#!/usr/bin/env bash
set -euo pipefail

# 1) Create user if missing
if ! id -u umans >/dev/null 2>&1; then
  useradd -m -s /bin/bash umans
fi

# 2) Minimal deps
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y curl ca-certificates git python3 python3-pip

# 3) Ensure uv are on PATH for login shells
PROFILE_LINES='
# uv
'
for f in /home/umans/.profile /home/umans/.bashrc; do
  [ -f "$f" ] || touch "$f"
  printf "%s\n" "$PROFILE_LINES" >> "$f"
done
chown umans:umans /home/umans/.profile /home/umans/.bashrc

# 4) Install uv for user "umans"
runuser -l umans -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'

# 5) Install the PyPI package "issue-solver" for user "umans" via uv tool
#    This creates an isolated venv and puts entry points in ~/.local/bin
runuser -l umans -c 'uv tool install issue-solver'

# 6) Install claude code cli
runuser -l umans -c 'curl -LsSf https://claude.ai/install.sh | bash'

echo "✅ cudu cli powered by Umans AI is now installed for user 'umans'. Enjoy! ❤️"
echo "✅ Installation complete!"
# Optional sanity checks
runuser -l umans -c 'uv --version || true'
# If "issue-solver" exposes a CLI (e.g., "cudu"), this will show its path:
runuser -l umans -c 'command -v cudu || true'