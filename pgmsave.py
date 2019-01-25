#!/usr/bin/python3
from sys import argv, exit
import struct
from intellibus import *

if len(argv) != 2:
	print('Error: You must specify the name of the serial port on the command line.')
	exit(255)

class Dumper(VirtDevice):
	def __init__(self, ibus):
		super().__init__(ibus, 5, 3121, fromhex('00 00 FF FF FF FF'), 0, (7,1), 0x7FF7)
		self.next = (0x16, b'')
	
	def on_ping(self):
		if self.next is not None:
			self.send(self.next[0], self.next[1])
			self.next = None
	
	def handle_cmd(self, cmd, arg):
		if cmd == 0x17:
			self.next = (0x14, b'')
		elif 0xC8 <= cmd <= 0xD7:
			if cmd == 0xD7:
				try:
					icode = arg[0x1D:0x25].rstrip(b'\x00').decode('ascii')
					if len(icode) > 0:
						print('Found installer code: ' + icode)
					else:
						print("Didn't find installer code :(")
				except UnicodeDecodeError:
					print('Error reading installer code!')

			self.next = (cmd + 0x190, arg[2:4])
			index = struct.unpack('<H', self.next[1])[0]
			filename = '{:02X}-{}.pgm'.format(cmd, index)
			print('Writing ' + filename)
			with open(filename, 'wb') as f:
				f.write(arg)
		elif cmd == 0x15:
			print('Done!')
			bus.stop()

bus = Intellibus(argv[1])
dmp = Dumper(bus)
bus.run()
