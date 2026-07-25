#!/usr/bin/env bash
# Avvio AMI 3.x in locale (macOS/Linux). pkill con || true: se non c’è già un’istanza, non abortire.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
pkill -f "python3 -m ami.main" 2>/dev/null || true
pkill -f "python -m ami.main" 2>/dev/null || true
sleep 1

# macOS: preferisci AMI.app se presente (menu bar più affidabile del processo python nudo)
if [[ "$(uname -s)" == "Darwin" && -d "$ROOT/dist/AMI.app" ]]; then
  # Sblocca icona nascosta; forza posizione a sinistra (meno overflow «»)
  defaults delete tech.ciaoim.ami "NSStatusItem Visible tech.ciaoim.ami.status" 2>/dev/null || true
  defaults delete -g "NSStatusItem Visible tech.ciaoim.ami.status" 2>/dev/null || true
  defaults write tech.ciaoim.ami "NSStatusItem Preferred Position tech.ciaoim.ami.status" -float 0 2>/dev/null || true
  defaults write -g "NSStatusItem Preferred Position tech.ciaoim.ami.status" -float 0 2>/dev/null || true
  pkill -f "Contents/MacOS/AMI" 2>/dev/null || true
  sleep 1
  echo "Avvio AMI.app (consigliato su macOS)…"
  # Esecuzione diretta (non open): passa AMI_TRAY_* e AMI_DEBUG_TRAY al processo.
  nohup "$ROOT/dist/AMI.app/Contents/MacOS/AMI" >> "${TMPDIR:-/tmp}/ami-launch.log" 2>&1 &
  echo "$!" > "${TMPDIR:-/tmp}/ami-launch.pid"
  sleep 2
  if kill -0 "$(cat "${TMPDIR:-/tmp}/ami-launch.pid")" 2>/dev/null; then
    echo "AMI.app avviata — PID $(cat "${TMPDIR:-/tmp}/ami-launch.pid")"
    echo "Badge AMI in alto a destra + icona nella menu bar (se piena: controlla «» a destra)."
    echo "Se non vedi nulla: clicca l'icona AMI nel Dock (barra in basso)."
    echo "Log: ${TMPDIR:-/tmp}/ami-launch.log"
  else
    echo "AMI.app non partita. Ultime righe del log:"
    tail -20 "${TMPDIR:-/tmp}/ami-launch.log" || true
    exit 1
  fi
  exit 0
fi

export PYTHONPATH=src
LOG="${TMPDIR:-/tmp}/ami-launch.log"
nohup python3 -m ami.main >> "$LOG" 2>&1 &
echo "$!" > "${TMPDIR:-/tmp}/ami-launch.pid"
sleep 2
if kill -0 "$(cat "${TMPDIR:-/tmp}/ami-launch.pid")" 2>/dev/null; then
  echo "AMI avviata — PID $(cat "${TMPDIR:-/tmp}/ami-launch.pid")"
  echo "Log: $LOG"
  echo "Su macOS da sorgente l'icona menu bar può essere instabile; build: python3 build.py && ./run_local.sh"
else
  echo "AMI non partita. Ultime righe del log:"
  tail -20 "$LOG" || true
  exit 1
fi
