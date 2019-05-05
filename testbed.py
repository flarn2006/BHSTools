#!/usr/bin/python3
import os
from sys import argv, exit
from threading import Thread
from intellibus import *
from time import sleep

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
	if dest == 0 and cmd == 0x2F:
		raise ValueError('And risk bricking the panel? If you really want to, do bus.send(0, 0x7FFE, (0x2F, {})).'.format(repr(arg)))
	else:
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

def dlpoke(cmd, addr, new):
	send(0, cmd, poke(cmd, addr, new))

hd = hexdump

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
print('Press Ctrl+A, \\ to quit.')
