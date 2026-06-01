#!/bin/bash
# deploy_blogs.sh — Hot-deploy blog content to production
# Usage: bash deploy_blogs.sh (or run from Git Bash / WSL on Windows)

set -e

SSH_KEY="$HOME/.ssh/id_ed25519"
SERVER="rovie_segubre@34.55.175.24"
REMOTE_DIR="~/sovereign/landing/"

echo "📤 Uploading blog files..."
scp -r -i "$SSH_KEY" -o StrictHostKeyChecking=no landing/blogs "$SERVER:$REMOTE_DIR"

echo "🔐 Fixing permissions for NGINX..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER" "chmod -R 755 ~/sovereign/landing/blogs/"

echo "✅ Blog deployed successfully!"
echo "🌐 Check: https://sovereign-api.com/blogs/"
