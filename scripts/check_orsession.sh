#!/bin/bash
# Diagnostic script: check orsession process state
# Usage: ./scripts/check_orsession.sh

pid=$(pgrep -f "bin/orsession" 2>/dev/null | head -1)

if [ -z "$pid" ]; then
    echo "orsession is not running."
    exit 0
fi

echo "=== orsession PID: $pid ==="
echo ""

# Process state
echo "--- Process Status ---"
cat /proc/$pid/status 2>/dev/null | grep -E "^(State|Threads|VmRSS|VmSize|Name)"
echo ""

# Thread details
echo "--- Threads ---"
find /proc/$pid/task -maxdepth 1 -mindepth 1 -type d 2>/dev/null | while read tdir; do
    tid=$(basename "$tdir")
    comm=$(cat "$tdir/comm" 2>/dev/null)
    wchan=$(cat "$tdir/wchan" 2>/dev/null)
    state=$(cat "$tdir/status" 2>/dev/null | grep "^State:" | awk '{print $2, $3}')
    printf "  %-8s %-20s %-5s %s\n" "$tid" "$comm" "$state" "$wchan"
done
echo ""

# Check for child processes (opencode export)
echo "--- Child Processes ---"
children=$(pgrep -P $pid 2>/dev/null)
if [ -z "$children" ]; then
    echo "  (none)"
else
    ps -p $(echo $children | tr '\n' ',') -o pid,comm,state,time 2>/dev/null
fi
echo ""

# Check temp files
echo "--- Temp Export Files ---"
ls -la /tmp/orsession-*/opencode-session-*.json 2>/dev/null || echo "  (none)"
echo ""

# Summary
threads=$(cat /proc/$pid/status 2>/dev/null | grep "^Threads:" | awk '{print $2}')
if [ "$threads" = "3" ]; then
    echo "STATUS: Worker thread completed (only 3 textual threads remain)."
    echo "  If UI is frozen, the deadlock is in textual's render pipeline."
elif [ "$threads" = "4" ]; then
    echo "STATUS: Worker thread still running (4 threads)."
    echo "  Export may still be in progress."
else
    echo "STATUS: $threads threads (unexpected)."
fi
