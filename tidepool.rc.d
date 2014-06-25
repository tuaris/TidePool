#!/bin/sh

# $FreeBSD$
#
# PROVIDE: tidepool
# REQUIRE: LOGIN
# KEYWORD: shutdown
#
# Add the following lines to /etc/rc.conf.local or /etc/rc.conf
# to enable this service:
#
# tidepool_enable (bool):	Set to NO by default.
#				Set it to YES to enable tidepool.
# tidepool_confdir (path):	Set to /usr/local/etc/tidepool
#				by default.
# tidepool_poolname (name):	Set to tidepool
#				by default.

. /etc/rc.subr

name=tidepool
rcvar=${name}_enable

load_rc_config ${name}

: ${tidepool_enable:="NO"}
: ${tidepool_confdir="/usr/local/etc/tidepool"}
: ${tidepool_poolname="tidepool"}

# This handles profile specific vars.
if [ -n "$2" ]; then
	profile="$2"
	if [ -n "${tidepool_profiles}" ]; then
		eval tidepool_enable="\${tidepool_${profile}_enable:-${tidepool_enable}}"
		tidepool_poolname=${profile}
	else
		echo "$0: extra argument ignored"
	fi
else
	if [ -n "${tidepool_profiles}" -a -n "$1" ]; then
		for profile in ${tidepool_profiles}; do
			echo "===> ${name} profile: ${profile}"
			/usr/local/etc/rc.d/${name} $1 ${profile}
			retcode="$?"
			if [ "0${retcode}" -ne 0 ]; then
				failed="${profile} (${retcode}) ${failed:-}"
			else
				success="${profile} ${success:-}"
			fi
		done
		# It exits so that non-profile rc.d is not started when there are profiles.
		exit 0
	fi
fi

tidepool_chdir=/usr/local/${name}

tacfile=${tidepool_confdir}/tacs/${tidepool_poolname}.tac
pidfile=/var/run/${tidepool_poolname}.pid
procname=${tidepool_poolname}d
command="/usr/local/bin/twistd"
required_files=${tacfile}
command_args="-y ${tacfile} --pidfile ${pidfile} -l /var/log/${tidepool_poolname}.log"

run_rc_command "$1"
