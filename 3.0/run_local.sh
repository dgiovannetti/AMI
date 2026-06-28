#!/usr/bin/env bash
# Avvio AMI 3.x in locale (macOS/Linux). pkill con || true: se non c’è già un’istanza, non abortire.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
pkill -f "python3 -m ami.main" 2>/dev/null || true
pkill -f "python -m ami.main" 2>/dev/null || true
sleep 1
export PYTHONPATH=src
LOG="${TMPDIR:-/tmp}/ami-launch.log"
nohup python3 -m ami.main >> "$LOG" 2>&1 &
echo "$!" > "${TMPDIR:-/tmp}/ami-launch.pid"
sleep 2
if kill -0 "$(cat "${TMPDIR:-/tmp}/ami-launch.pid")" 2>/dev/null; then
  echo "AMI avviata — PID $(cat "${TMPDIR:-/tmp}/ami-launch.pid")"
  echo "Log: $LOG"
else
  echo "AMI non partita. Ultime righe del log:"
  tail -20 "$LOG" || true
  exit 1
fi
