#!/bin/sh
set -e

if [ ! -d testbed-modem ]; then
	echo 'Error: testbed-modem directory not found. Are you running in the correct directory?'
fi

if [ -z "$1" ]; then
	echo "Error: You must specify the name of the serial port on the command line." >&2
	exit 255
fi

echo "$1" > testbed-modem/port.txt
echo > testbed-modem/log.txt
exec screen -c testbed-modem/screenrc
