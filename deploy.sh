#!/bin/bash
# =====================================================
# Deploy Whisper Transcription App to Koyeb
# =====================================================
# This script deploys the app using Koyeb API directly.
# It creates the app and service with GPU instance.
# =====================================================

API_TOKEN="xvt7aoazqubnx2djjv69b5ounqmg3vsp445nmz6vwjladxx7ecmhfn1gigdd25ov"
APP_NAME="whisper-transcriber"
SERVICE_NAME="whisper-api"
REGION="was"  # Washington D.C. (closest for good latency)
INSTANCE_TYPE="gpu-nvidia-rtx-4000-sff-ada"  # RTX 4000 SFF Ada (available: 1)

echo "============================================="
echo "  Deploying Whisper Transcriber to Koyeb"
echo "============================================="

# Step 1: Check if app already exists
echo "[1/3] Checking existing apps..."
EXISTING=$(curl -s "https://app.koyeb.com/v1/apps" \
  -H "Authorization: Bearer ${API_TOKEN}" | python3 -c "
import json,sys
data=json.load(sys.stdin)
for app in data.get('apps',[]):
    if app['name'] == '${APP_NAME}':
        print(app['id'])
        break
" 2>/dev/null)

if [ -n "$EXISTING" ]; then
    echo "    App '${APP_NAME}' already exists (ID: ${EXISTING}). Updating..."
else
    echo "    Creating new app '${APP_NAME}'..."
fi

# Step 2: Deploy using Koyeb API
echo "[2/3] Deploying service with GPU..."

# We need to use a Docker registry. Koyeb supports building from a Git repo
# or pulling from a Docker registry. Since we want to avoid building locally,
# we'll push our code to a GitHub repo or use Koyeb's built-in builder.

# For simplicity, we'll use the Koyeb CLI approach:
echo "[INFO] To deploy, you need the Koyeb CLI. Installing..."
curl -fsSL https://raw.githubusercontent.com/koyeb/koyeb-cli/master/install.sh | sh

# Configure CLI
export KOYEB_TOKEN="${API_TOKEN}"

echo "[3/3] Creating service..."
koyeb service create "${SERVICE_NAME}" \
  --app "${APP_NAME}" \
  --docker "ghcr.io/YOUR_REGISTRY/whisper-app:latest" \
  --instance-type "${INSTANCE_TYPE}" \
  --regions "${REGION}" \
  --ports "8000:http" \
  --routes "/:8000" \
  --min-scale 0 \
  --max-scale 1 \
  --checks "8000:http:/:20"

echo ""
echo "============================================="
echo "  Deployment initiated!"
echo "  Your app will be available at:"
echo "  https://${APP_NAME}-XXXXX.koyeb.app"
echo "============================================="
