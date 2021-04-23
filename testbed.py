#!/usr/bin/python3
import os
from sys import argv, exit, stdout
from threading import Thread
from intellibus import *
from time import sleep
from base64 import b64decode
from config_rpt_util import describe_config_block
import json

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

def send(dest, cmd, arg=b'', src=None):
	if type(arg) == str:
		arg = fh(arg)
	if src is None:
		src = 0x7FFE if dest == 0 else 0
	bus.send(dest, src, (cmd, arg))

class TestDevice(VirtDevice):
	def __init__(self, ibus, kind, model=3999):
		super().__init__(ibus, kind, model, b'123456', 0, (0,0))
		self.replymap = {}
	
	def handle_cmd(self, cmd, arg):
		if cmd in self.replymap:
			reply = self.replymap[cmd]
			if type(reply) is int:
				reply = (reply, arg)
			elif type(reply) is not tuple:
				reply = reply(cmd, arg)
			self.send(reply[0], reply[1])

onRXlist={}

def onRX(cmd):
	def wrapper(f):
		onRXlist[cmd] = f
	return wrapper

def poke(data, addr, new):
	if type(data) is int:
		data = last[data]
	if type(new) is int:
		new = bytes([new])
	return data[:addr] + new + data[addr+len(new):]

def dlpoke(cmd, addr, new):
	send(0, cmd, poke(cmd, addr, new))

def upload_from_json(filename):
	with open(filename, 'r') as f:
		j = json.load(f)
	
	if type(j) is list:
		j = j[0]
	
	if j['version'] == 0:
		count = len(j['data'])
		n = 0
		print('Starting upload of {} data items in 2 seconds.'.format(count))
		sleep(1) #the rest of the delay is in the loop
		for item in j['data']:
			sleep(1)
			n += 1
			arg = b64decode(item['arg'])
			print('({} of {}) Uploading {}...'.format(n, count, describe_config_block(item['cmd'], arg)))
			send(0, item['cmd'], arg)
	
	try:
		stdout.write('\a')
		for i in range(30):
			stdout.write('\rUpload complete. Restarting panel in 30 seconds... (press Ctrl+C to abort)')
			stdout.flush()
			sleep(1)
		print('\nPanel will now restart.')
		send(0, 32)
	except KeyboardInterrupt:
		print('\nPanel restart aborted.')
		print('Some uploaded programming may not take effect until you manually power cycle the panel.')

def hd(data):
	if type(data) is int:
		data = last[data]
	print(hexdump(data))

numpy_imported = False
try:
	import numpy as np

	def ta(data):
		if type(data) is int:
			data = last[data]
		return np.array(list(data), dtype=np.uint8)

	hd_inner = hd
	def hd(data):
		if type(data) is np.array:
			data = bytes(data)
	
	numpy_imported = True
except ModuleNotFoundError:
	pass
except Exception as ex:
	print('')
	print("An error occurred while loading numpy, and it wasn't just \"module not found\":")
	print('')
	print(f'{type(ex).__name__}: {ex}')
	print('')
	print("Numpy is only used by an optional utility function that you probably won't need,")
	print('so this is most likely nothing to worry about.')
	print('')

bus = Intellibus(argv[2], debug='tx,rx', dbgout=open('testbed/log.txt', 'a'))
last={}

@add_listener(bus)
def onRXsupp(pkt, synced):
	if type(pkt) is Message:
		cmd, arg = pkt.getcmd(), pkt.getarg()
		if synced:
			if cmd in onRXlist:
				onRXlist[cmd](arg)
		last[cmd] = arg

# Add your own stuff below this line



thread = Thread(target=bus.run)
thread.start()

print('Send messages using send(dest, cmd[, arg]).')
print('To access received data, do last[cmd]. E.g. last[200] to receive the uploaded panel config.')
print('')
print('Or you can script responses to commands like this:')
print('')
print('    @onRX(cmd)')
print('    def func(arg):')
print('        #write code here')
print('')
print('Utility functions:')
print('')
print('    th(bytes) - To Hex')
print('    fh("hex") - From Hex (to bytes)')
print('    hd(bytes) - Hex Dump')
print('    poke(data, n, byte) - Replaces byte n (0-based) in data with byte')
if numpy_imported:
	print('    ta(data) - To Array (numpy array, useful for bitwise operations)')
print('')
print('Specialized Functions:')
print('')
print('    dlpoke(cmd, addr, byte) - Shortcut for send(0, cmd, poke(last[cmd], addr, byte))')
print('    upload_from_json("filename") - Upload system configuration from a JSON file exported using the web UI')
print('    s3121_start() - Starts Soft3121 (must be started this way if testbed is running)')
print('')

print('Press Ctrl+A, \\ to quit.')
