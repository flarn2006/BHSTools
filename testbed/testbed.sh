#!/bin/sh
set -e

if [ ! -d testbed ]; then
	echo 'Error: testbed directory not found. Are you running in the correct directory?'
fi

if [ -z "$1" ]; then
	echo "Error: You must specify the name of the serial port on the command line." >&2
	exit 255
fi

echo "$1" > testbed/port.txt
echo > testbed/log.txt
exec screen -c testbed/screenrc
