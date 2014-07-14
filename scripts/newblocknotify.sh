#!/bin/csh

# TidePool Block notification script in pure Shell script.
# Usage: blocknotify.sh host port password

# Lock File ensures that this script isn't run too often when many blocks are found in a short period.
set SCRIPTNAME=`basename $0`
set PIDFILE=/var/run/${SCRIPTNAME}.pid

# check for existence of a lock file
# if the file exists make sure the pid that created it is still running then exit.

if (-e ${PIDFILE}) then
	#verify if the process is actually still running under this pid
	set PID=`cat ${PIDFILE}`

	ps -p "$PID" >&/dev/null
	# somebody else is running the script ?
	if ($? == 0) then
		echo "Notification already running as pid $PID"
		exit 1
	endif

	# put the current process as owner of the lock
	echo $$ > ${PIDFILE}
else
	# no file found - make one, own the lock,too.
	echo $$ > ${PIDFILE}
	chmod 777 ${PIDFILE}
endif

# Setup Variebles to connect to mining pool server
set HOST=$1
set PORT=$2
set PASSWORD=$3

# Use NETCAT to send the JSON message
printf '{"id": 1, "method": "mining.update_block", "params": ["'${PASSWORD}'"]}\n' | nc ${HOST} ${PORT} -i 1

# Check result
set FINAL_EXIT_CODE=$?
if ($FINAL_EXIT_CODE != 0) then
	echo "Notification falied!"
endif

# last lines of script - release lock file
rm -f ${PIDFILE}
exit $FINAL_EXIT_CODE