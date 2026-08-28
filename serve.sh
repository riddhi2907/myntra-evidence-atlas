#!/usr/bin/env bash
#
# Start/stop the live discovery engine.
#
#   ./serve.sh start | stop | restart | status
#
# The server is found by the port it listens on, not by a stored PID or a shell
# job number. A job number only exists inside the shell that launched it, which
# is exactly what a second terminal does not have -- and a stale pidfile can
# name a PID the OS has since reused. The listening socket is the one thing
# that is true no matter who is asking.
#
# Binds to 127.0.0.1 by default. Streamlit's own default binds every interface,
# which puts a page that queries live APIs on your keys within reach of anyone
# on the network. Override deliberately if you want that:
#
#   ADDR=0.0.0.0 ./serve.sh start
#   PORT=8600 ./serve.sh start

set -uo pipefail

PORT="${PORT:-8501}"
ADDR="${ADDR:-127.0.0.1}"

cd "$(dirname "$0")" || exit 1
LOG="$PWD/streamlit.log"

# Echo the PID(s) listening on $PORT, one per line, or nothing.
listener_pids() {
  if command -v netstat >/dev/null 2>&1 && netstat -ano >/dev/null 2>&1; then
    # Windows netstat: ... LISTENING <pid>
    netstat -ano 2>/dev/null \
      | grep -E "[^0-9]${PORT}[[:space:]]" \
      | grep -i 'LISTENING' \
      | awk '{print $NF}' | sort -u
  elif command -v lsof >/dev/null 2>&1; then
    lsof -ti "tcp:${PORT}" -s TCP:LISTEN 2>/dev/null | sort -u
  else
    ss -lptnH "sport = :${PORT}" 2>/dev/null \
      | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u
  fi
}

kill_pid() {
  if command -v taskkill >/dev/null 2>&1; then
    taskkill //PID "$1" //F >/dev/null 2>&1
  else
    kill -TERM "$1" 2>/dev/null || kill -KILL "$1" 2>/dev/null
  fi
}

cmd_status() {
  local pids
  pids="$(listener_pids)"
  if [ -n "$pids" ]; then
    echo "running on http://${ADDR}:${PORT}  (pid $(echo "$pids" | tr '\n' ' ' | sed 's/ $//'))"
    return 0
  fi
  echo "not running (nothing listening on port ${PORT})"
  return 1
}

cmd_start() {
  if [ -n "$(listener_pids)" ]; then
    echo "already running:"
    cmd_status
    return 0
  fi

  echo "starting on http://${ADDR}:${PORT} ..."
  nohup python -m streamlit run app.py \
    --server.port "$PORT" \
    --server.address "$ADDR" \
    --server.headless true \
    > "$LOG" 2>&1 &
  disown 2>/dev/null

  # Streamlit takes a couple of seconds to bind. Poll rather than sleep blind,
  # so a start that fails reports the log instead of a false success.
  for _ in $(seq 1 30); do
    if [ -n "$(listener_pids)" ]; then
      cmd_status
      echo "log: $LOG"
      return 0
    fi
    sleep 0.5
  done

  echo "failed to start within 15s. Last lines of $LOG:" >&2
  tail -n 15 "$LOG" >&2
  return 1
}

cmd_stop() {
  local pids
  pids="$(listener_pids)"
  if [ -z "$pids" ]; then
    echo "not running (nothing listening on port ${PORT})"
    return 0
  fi
  for pid in $pids; do
    kill_pid "$pid" && echo "stopped pid $pid"
  done
  for _ in $(seq 1 10); do
    [ -z "$(listener_pids)" ] && { echo "port ${PORT} released"; return 0; }
    sleep 0.5
  done
  echo "port ${PORT} still held after 5s" >&2
  return 1
}

case "${1:-status}" in
  start)   cmd_start ;;
  stop)    cmd_stop ;;
  restart) cmd_stop && cmd_start ;;
  status)  cmd_status ;;
  *)
    echo "usage: $0 {start|stop|restart|status}" >&2
    echo "  PORT=8600 ADDR=0.0.0.0 $0 start   # override port / bind address" >&2
    exit 2
    ;;
esac
