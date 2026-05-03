#!/usr/bin/env bash
# start_agents.sh — Launch all LogSnap agents in the background.
# Logs go to logs/agent_<name>.log
# Safe to run before sleep — agents survive terminal close.
#
# Usage:
#   ./start_agents.sh          # start all agents
#   ./start_agents.sh stop     # kill all agents
#   ./start_agents.sh status   # show running agents

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGS="$ROOT/logs"
mkdir -p "$LOGS"

AGENTS=(natnael biruk liya tigist endalk selam abel)

start_all() {
    echo "Starting LogSnap agents..."
    for agent in "${AGENTS[@]}"; do
        LOG="$LOGS/agent_${agent}.log"
        PID_FILE="$LOGS/${agent}.pid"

        # Skip if already running
        if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "  [${agent}] already running (PID $(cat "$PID_FILE"))"
            continue
        fi

        nohup python3 "$ROOT/agents/${agent}.py" \
            >> "$LOG" 2>&1 &
        echo $! > "$PID_FILE"
        echo "  [${agent}] started → PID $! | log: logs/agent_${agent}.log"
        sleep 1  # stagger startup to avoid rate limits
    done
    echo ""
    echo "All agents running. You can close this terminal and go to sleep."
    echo "Monitor: tail -f logs/agent_*.log"
    echo "Matrix:  http://localhost:8008 (Element web)"
}

stop_all() {
    echo "Stopping LogSnap agents..."
    for agent in "${AGENTS[@]}"; do
        PID_FILE="$LOGS/${agent}.pid"
        if [[ -f "$PID_FILE" ]]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                echo "  [${agent}] stopped (PID $PID)"
            else
                echo "  [${agent}] not running"
            fi
            rm -f "$PID_FILE"
        fi
    done
}

status_all() {
    echo "LogSnap agent status:"
    for agent in "${AGENTS[@]}"; do
        PID_FILE="$LOGS/${agent}.pid"
        if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "  [${agent}] ✓ running (PID $(cat "$PID_FILE"))"
        else
            echo "  [${agent}] ✗ not running"
        fi
    done
}

case "${1:-start}" in
    start)  start_all ;;
    stop)   stop_all  ;;
    status) status_all ;;
    *)      echo "Usage: $0 [start|stop|status]" ;;
esac
