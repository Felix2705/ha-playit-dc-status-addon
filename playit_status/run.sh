#!/usr/bin/env bash
set -e

# Load options from config if provided by Supervisor (via /data/options.json)
OPTIONS_FILE="/data/options.json"
STATUS_URL="https://dc.status.playit.gg/"
INTERVAL=60

if [ -f "$OPTIONS_FILE" ]; then
  STATUS_URL=$(jq -r '.status_url // "https://dc.status.playit.gg/"' "$OPTIONS_FILE")
  INTERVAL=$(jq -r '.interval // 60' "$OPTIONS_FILE")
fi

echo "Starting Playit Status Add-on"
echo "Polling $STATUS_URL every ${INTERVAL}s"

while true; do
  python3 /addon/poll.py "$STATUS_URL" || echo "poll failed"
  sleep "$INTERVAL"
done
