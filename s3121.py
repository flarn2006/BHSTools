#!/usr/bin/python3
from sys import argv, exit
from threading import Thread
from queue import Queue
from intellibus import *
import flask
import json
import config_rpt_util

if len(argv) != 2:
	print('Error: You must specify the name of the serial port on the command line.')
	exit(255)

app = flask.Flask(__name__)

@app.route('/')
def flask_index():
	return flask.send_file('static/s3121.html')

@app.route('/status')
def flask_status():
	global pgm, dl
	cpos = 16 * pgm.curY + pgm.curX
	d = {'text':process_display_str(pgm.display), 'cursor':{'pos':cpos, 'visible':pgm.curVis}, 'dl_complete':dl.complete}
	return (json.dumps(d), {'Content-Type': 'application/json'})

@app.route('/key', methods=['POST'])
def flask_key():
	global pgm
	pgm.key(flask.request.data.decode('ascii'))
	return 'Done'

@app.route('/start_download', methods=['POST'])
def flask_start_download():
	global dl
	dl.start_download()
	return 'Download started'

@app.route('/config_rpt')
def flask_config_rpt():
	global dl
	return flask.render_template('config_rpt.html', results=dl.results, util=config_rpt_util)

def writestr(dest, index, src):
	return dest[:index] + src[:len(dest)-index] + dest[index+len(src):]

def process_display_str(text):
	return text.decode('ascii')

class Programmer(VirtDevice):
	def __init__(self, ibus):
		super().__init__(ibus, 5, 3121, fromhex('00 00 FF FF FF FF'), 0, (7,1), 0x7FFE)
		self.display = b' ' * 16 * 4
		self.ping_counter = 0
		self.curX = 0
		self.curY = 0
		self.curVis = False
		self.keyqueue = Queue()

	def on_ping(self):
		while not self.keyqueue.empty():
			keycode = self.keyqueue.get()[:2].rjust(2, '0')
			if keycode.upper() in '3C BC 68 E8 3E BE 1B 9B 73 F3 08 88 2D AD 2B AB'.split(' '):
				keycode = '1B ' + keycode
			self.send(0x7E4, fromhex(keycode))

	def handle_cmd(self, cmd, arg):
		if cmd == 0x7DC:
			text = arg[3:].rstrip(b'\0')
			if b'\x0c' in text:
				self.display = b' '*16*4
				self.curX = 0
				self.curY = 0
			else:
				acct, row, col = struct.unpack('<bbb', arg[:3])
				if col & 0x80:
					col &= 0x7F
					self.curVis = True
				else:
					self.curVis = False
				if col > 0:
					self.curY = col - 1
				if row > 0:
					self.curX = row - 1
				self.display = writestr(self.display, 16*self.curY + self.curX, text)
				self.curX += len(text)
				self.curY += self.curX // 16
				self.curX %= 16
	
	def key(self, keycode):
		self.keyqueue.put(keycode)

class Downloader(VirtDevice):
	def __init__(self, ibus):
		super().__init__(ibus, 5, 3121, fromhex('00 00 FF FF FF FF'), 0, (7,1), 0x7FFE)
		self.next = None
		self.results = []
		self.complete = False
	
	def start_download(self):
		self.next = (0x16, b'')
		self.results = []
		self.complete = False
	
	def on_ping(self):
		if self.next is not None:
			self.send(self.next[0], self.next[1])
			self.next = None
	
	def handle_cmd(self, cmd, arg):
		if cmd == 0x17:
			self.next = (0x14, b'')
		elif 0xC8 <= cmd <= 0xDA:
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
			self.results.append((cmd, arg))
		elif cmd == 0x15:
			print('Done!')
			self.complete = []

webthread = Thread(target=app.run, kwargs={'host':'0.0.0.0', 'port':3121})

try:
	bus = Intellibus(argv[1], debug='rx,tx')
	pgm = Programmer(bus)
	dl = Downloader(bus)
	webthread.start()
	bus.run()
except KeyboardInterrupt:
	pass
finally:
	webthread.join()
