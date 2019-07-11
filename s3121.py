#!/usr/bin/python3
from sys import argv, exit
from threading import Thread
from intellibus import *
import intellibus.devices as devices
import flask
import json
import config_rpt_util
import logging
from base64 import b64encode

app = flask.Flask(__name__)

@app.route('/')
def flask_index():
	return flask.send_file('static/s3121.html')

@app.route('/status')
def flask_status():
	global pgm, dl, kp
	cpos = 16 * pgm.curY + pgm.curX
	lcdbits = ''.join(['1' if b else '0' for b in kp.lcd])
	d = {'text':process_display_str(pgm.display), 'cursor':{'pos':cpos, 'visible':pgm.curVis}, 'dl_complete':dl.complete, 'keypad_lcd':lcdbits}
	return (json.dumps(d), {'Content-Type': 'application/json'})

@app.route('/key', methods=['POST'])
def flask_key():
	global pgm
	pgm.key(flask.request.data.decode('ascii'))
	return 'Done'

@app.route('/kpkey', methods=['POST'])
def flask_kpkey():
	global kp
	kp.key(flask.request.data.decode('ascii'))
	return 'Done'

@app.route('/start_download', methods=['POST'])
def flask_start_download():
	global dl
	dl.start_download()
	return 'Download started'

@app.route('/download_status')
def flask_download_status():
	global dl
	blocks = [config_rpt_util.describe_config_block(c,a) for c,a in dl.results]
	return (json.dumps({'icode':dl.icode, 'blocks':blocks}), {'Content-Type': 'application/json'})

@app.route('/config_rpt')
def flask_config_rpt():
	global dl
	return flask.render_template('config_rpt.html', results=dl.results, util=config_rpt_util, b64encode=b64encode)

def process_display_str(text):
	try:
		return text.decode('ascii')
	except UnicodeDecodeError:
		out = ''
		for b in text:
			out += chr(b) if 32<=b<=126 else '.'
		return out

class Downloader(VirtDevice):
	def __init__(self, ibus):
		super().__init__(ibus, 5, 3121, fromhex('00 00 FF FF FF FF'), 0, (7,1), 0x7FFE)
		self.next = None
		self.results = []
		self.complete = False
		self.icode = None
	
	def start_download(self):
		self.next = (0x16, b'')
		self.results = []
		self.complete = False
		self.icode = None
	
	def on_ping(self):
		if self.next is not None:
			self.send_now(self.next[0], self.next[1])
			self.next = None
	
	def handle_cmd(self, cmd, arg):
		if cmd == 0x17:
			self.next = (0x14, b'')
		elif 0xC8 <= cmd <= 0xDA:
			if cmd == 0xD7:
				try:
					icode = arg[0x1D:0x25].decode('ascii') + '\0'
					icode = icode[:icode.find('\0')]
					self.icode = icode
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

def start(bus):
	global pgm, dl, kp, webthread

	logging.getLogger('werkzeug').setLevel(logging.ERROR)

	pgm = devices.Programmer(bus)
	dl = Downloader(bus)
	kp = devices.IconKeypad(bus, fromhex('13 37 1D EC 0D ED'), 0x1337, (0,0))
	kp.addr = 0x7FFE
	webthread.start()

if __name__ == '__main__':
	if len(argv) != 2:
		print('Error: You must specify the name of the serial port on the command line.')
		exit(255)

	try:
		bus = Intellibus(argv[1], debug='rx,tx')
		start(bus)
		bus.run()
	except KeyboardInterrupt:
		pass
	finally:
		webthread.join()
