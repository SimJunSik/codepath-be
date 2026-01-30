#!/bin/bash
# Build the sandbox Docker image for secure code execution

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${1:-codepath-sandbox:latest}"

echo "Building sandbox image: $IMAGE_NAME"

docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"

echo "Sandbox image built successfully!"
echo ""
echo "To test the image, run:"
echo "  docker run --rm --network=none --memory=128m --cpus=0.5 --read-only $IMAGE_NAME 'print(1+1)'"
echo ""
echo "Security features enabled:"
echo "  - Non-root user (sandbox)"
echo "  - No network access (--network=none)"
echo "  - Memory limit (--memory=128m)"
echo "  - CPU limit (--cpus=0.5)"
echo "  - Read-only filesystem (--read-only)"
echo "  - No privilege escalation (--no-new-privileges)"
echo "  - All capabilities dropped (--cap-drop=ALL)"
