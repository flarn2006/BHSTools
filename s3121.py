from sys import argv, exit
from threading import Thread
from queue import Queue
from intellibus import *
import flask

if len(argv) != 2:
	print('Error: You must specify the name of the serial port on the command line.')
	exit(255)

app = flask.Flask(__name__)
bus = Interface(argv[1])
sync = SyncState(0x7FFE)
display = b' ' * 16 * 4
ping_counter = 0
curX = 0
curY = 0
keyqueue = Queue()

w = bus.write
def new_bus_write(msg):
	if type(msg) is Message: print('TX {}'.format(msg))
	w(msg)
bus.write = new_bus_write

@app.route('/')
def flask_index():
	return flask.send_file('static/s3121.html')

@app.route('/display')
def flask_display():
	return (process_display_str(display), {'Content-Type': 'text/plain'})

@app.route('/key', methods=['POST'])
def flask_key():
	keyqueue.put(flask.request.data.decode('ascii'))
	return 'Done'

webthread = Thread(target=app.run, kwargs={'host':'0.0.0.0', 'port':3121})
webthread.start()

def writestr(dest, index, src):
	return dest[:index] + src[:len(dest)-index] + dest[index+len(src):]

def process_display_str(text):
	return text.decode('ascii')

try:
	while True:
		pkt = bus.read()
		if not sync.receive(pkt):
			continue
		
		if type(pkt) is SyncPing and pkt.addr == 0x7FFE:
			bus.write(sync.reply())
			if keyqueue.empty():
				if ping_counter == 0:
					bus.write(Message(0, 0x7FFE, fromhex('B9 0B 00 00 FF FF FF FF 00 01 30 0C 05 00 00 00 07 01'), 0))
				ping_counter = (ping_counter + 1) % 60
			else:
				keycode = keyqueue.get()[:2].rjust(2, '0')
				if keycode.upper() in '3C BC 68 E8 3E BE 1B 9B 73 F3 08 88 2D AD 2B AB'.split(' '):
					keycode = '1B ' + keycode
				pkt = Message(0, 0x7FFE, fromhex('E4 07 ' + keycode), sync.next(False))
				for _ in range(6):
					bus.write(pkt)
		elif type(pkt) is Message:
			print('RX {}'.format(pkt))
			cmd = pkt.getcmd()
			if cmd == 0x7DC:
				arg = pkt.getarg()
				text = arg[3:].rstrip(b'\0')
				if b'\x0c' in text:
					display = b' '*16*4
					curX = 0
					curY = 0
				else:
					acct, row, col = struct.unpack('<bbb', arg[:3])
					row &= 0x7F
					if col > 0:
						curY = col - 1
					if row > 0:
						curX = row - 1
					display = writestr(display, 16*curY + curX, text)
					curX += len(text)
					curY += curX // 16
					curX %= 16
			elif cmd == 0x7E4:
				bus.write(Message(0, 0x7FFE, pkt.payload, sync.next(False)))
			elif cmd == 0x7B8 and pkt.dest == 0x7FFE:
				bus.write(Message(0, 0x7FFE, fromhex('B9 0B 00 00 FF FF FF FF 00 01 30 0C 05 00 00 00 07 01'), 0))
			elif cmd == 0x7BF and pkt.dest == 0x7FFE:
				bus.write(Message(0, 0x7FFE, fromhex('C0 0B')))

except KeyboardInterrupt:
	pass
finally:
	webthread.join()
