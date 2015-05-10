#!/bin/csh

# TidePool Block notification script in pure Shell script.
# Usage: blocknotify.sh host port password

# Setup Variebles to connect to mining pool server
set HOST=$1
set PORT=$2
set PASSWORD=$3
set WORKER=$4


# Use NETCAT to send the JSON message
printf '{"id": 1, "method": "mining.update_worker_diff", "params": ["'${PASSWORD}'", "'${WORKER}'"]}\n' | nc ${HOST} ${PORT} -i 1 -w 2 -N
