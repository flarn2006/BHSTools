#!/usr/bin/python3
import os
from sys import argv, exit, stdout
from threading import Thread
from intellibus import *
from intellibus.modem import *
from time import sleep
from base64 import b64decode
from config_rpt_util import describe_config_block
import json
import traceback

try:
	is_direct_exec = (argv[1] != '-i')
except IndexError:
	is_direct_exec = True

if is_direct_exec:
	if os.name == 'posix':
		if len(argv) < 2:
			print('Error: You must specify the name of the serial port on the command line.')
			exit(255)

		path = 'testbed-modem/testbed.sh'
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

s3121_running = False

def s3121_start():
	global s3121_running
	if s3121_running:
		print('Already running!')
	else:
		__import__('s3121').start(bus)
		s3121_running = True

fh = fromhex
th = tohex

def send(cmd, arg=b''):
	if not m.connected:
		raise IOError('Connection not established.')
	else:
		if type(arg) == str:
			arg = fh(arg)
		m.write(Packet(b'\x26\x79\x1e\0' + arg))

onRXlist={}

def onRX(cmd):
	def wrapper(f):
		onRXlist[cmd] = f
	return wrapper

def hexdump(data):
	if type(data) is int:
		data = last[data]

	for i in range(0, len(data), 16):
		row = data[i:i+16]
		asc = ''.join([chr(b) if chr(b).isprintable() else '.' for b in row])
		print('{:04X}:  {:47s}  |{:16s}|'.format(i, tohex(row), asc))

def poke(data, addr, new):
	if type(data) is int:
		data = last[data]
	if type(new) is int:
		new = bytes([new])
	return data[:addr] + new + data[addr+len(new):]

hd = hexdump

def msg_out(msg):
	out.write(msg + '\n')
	out.flush()

out = open('testbed-modem/log.txt', 'w')
session_params = {'panel_id':None, 'debug':'tx,rx,sync', 'dbgout':out}

m = ModemInterface(argv[2], msg_callback=msg_out)
v = VivaldiSession(m, **session_params)
last={}

print('NOTE: THIS IS UNSTABLE AND NOT EXPECTED TO WORK WELL IF AT ALL.')
print("If you don't understand Python and Brinks protocols, there is likely nothing useful for you here.")

def modem_thread():
	while True:
		try:
			v.read()
		except (KeyboardInterrupt, SystemExit):
			break
		except Exception as ex:
			msg_out(traceback.format_exc())

def keep_alive_thread():
	while True:
		try:
			m.write(Packet(b'\xff\xff\xff\xff\2\0'))
			sleep(2)
		except (KeyboardInterrupt, SystemExit):
			break
		except Exception as ex:
			msg_out(traceback.format_exc())

# Add your own stuff below this line

thread = Thread(target=modem_thread)
#thread2 = Thread(target=keep_alive_thread)
thread.start()
#thread2.start()

print('Press Ctrl+A, \\ to quit.')
