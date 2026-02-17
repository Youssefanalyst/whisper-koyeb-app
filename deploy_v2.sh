#!/bin/bash
# =====================================================
# Deploy Whisper Transcription App to Koyeb (v2)
# =====================================================
# This script uses the Koyeb CLI to deploy the app.
# It uses the 'fra' region where GPU instances are likely available.
# =====================================================

export KOYEB_TOKEN="xvt7aoazqubnx2djjv69b5ounqmg3vsp445nmz6vwjladxx7ecmhfn1gigdd25ov"

# Make sure Koyeb CLI is installed
if ! command -v /home/y/.koyeb/bin/koyeb &> /dev/null; then
    echo "Installing Koyeb CLI..."
    curl -fsSL https://raw.githubusercontent.com/koyeb/koyeb-cli/master/install.sh | sh
fi

echo "Deploying Whisper Service..."

/home/y/.koyeb/bin/koyeb service create whisper-api \
  --app whisper-app-v2 \
  --git github.com/Youssefanalyst/whisper-koyeb-app \
  --git-branch main \
  --git-builder docker \
  --instance-type gpu-nvidia-rtx-4000-sff-ada \
  --ports 8000:http \
  --routes /:8000 \
  --regions fra \
  --checks 8000:http:/ \
  --token "${KOYEB_TOKEN}"
