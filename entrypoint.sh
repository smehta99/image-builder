#!/bin/bash
set -euo pipefail

if [[ -w /etc/subuid && -w /etc/subgid ]]; then
  echo "builder:1001:${USERNS_RANGE:-65536}" > /etc/subuid
  echo "builder:1001:${USERNS_RANGE:-65536}" > /etc/subgid
fi

# Make sure builder owns its homedir (optional if baked into image)
chown -R builder /home/builder || true

# Run buildah directly
exec su builder -c "buildah unshare $*"
