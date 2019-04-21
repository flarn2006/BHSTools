#!/usr/bin/python3
import os
from sys import argv, exit
from threading import Thread
from intellibus import *

try:
	is_direct_exec = (argv[1] != '-i')
except IndexError:
	is_direct_exec = True

if is_direct_exec:
	if os.name == 'posix':
		if len(argv) < 2:
			print('Error: You must specify the name of the serial port on the command line.')
			exit(255)

		path = 'testbed/testbed.sh'
		try:
			os.execv(path, [path, argv[1]])
		except FileNotFoundError:
			print(path + ' was not found. Make sure you are running this script from the same directory!')
			exit(253)
	else:
		print('Sorry; testbed is only compatible with Unix-based operating systems, such as Linux and macOS.')
		print('If you are using Windows, try running under Windows Subsystem for Linux.')
		print('If this message is displayed in error, run {} directly.'.format(path))
		exit(254)


# Set up some shortcuts for common functions
fh = fromhex
th = tohex

bus = Intellibus(argv[2], debug='tx,rx', dbgout=open('testbed/log.txt', 'a'))
thread = Thread(target=bus.run)
thread.start()

print('Press Ctrl+A, \\ to quit.')
