#!/usr/bin/python3
# Headless configuration download for BHS-3000/4000 panels.
#
# Does the same thing as clicking "Download Programming" in s3121.py, but with no
# browser: it impersonates the S3121 programmer, asks the panel to upload every
# configuration record, recovers the installer access code, and writes the result
# to disk (a human-readable hexdump report and a raw cmd+hex file).
#
# Usage:
#   ./download.py <serial_port> [output_prefix]
#
# Examples:
#   ./download.py /dev/ttyUSB0                 (Linux)
#   ./download.py /dev/cu.usbserial-XXXXXXXX   (macOS)
#   ./download.py COM3 mypanel                 (Windows; writes mypanel.txt / mypanel.raw)
#
# If output_prefix is omitted, nothing is written and the report is printed to stdout.

import sys
import time
import threading
from intellibus import *
import config_rpt_util


class Downloader(VirtDevice):
	# Address 0x7FFE is the one the real S3121 programmer uses.
	def __init__(self, ibus):
		super().__init__(ibus, 5, 3121, fromhex('00 00 FF FF FF FF'), 0, (7, 1), 0x7FFE)
		self.pending = (0x16, b'')     # cmd 22: (re)start upload
		self.results = []              # list of (cmd, arg), in order, de-duplicated
		self._seen = set()
		self.icode = None
		self.done = False
		self.last_progress = time.time()
		self._last_tx = 0.0

	# Retransmit whatever we're waiting to send, at most a few times a second, until
	# the panel's reply advances us to the next step. This tolerates dropped frames,
	# which is why it works headless where a fire-once approach can stall.
	def on_ping(self):
		if self.pending is not None:
			now = time.time()
			if now - self._last_tx >= 0.3:
				self._last_tx = now
				self.send_now(self.pending[0], self.pending[1])

	# Use the nosync handler so we act on replies regardless of bus sync state.
	def handle_cmd_nosync(self, cmd, arg, synced):
		if cmd == 0x17:                       # 23: restart-upload ACK -> request first record
			self.pending = (0x14, b'')        # cmd 20: request next config record
			self.last_progress = time.time()
		elif 0xC8 <= cmd <= 0xDA:             # 200..218: a config block
			key = (cmd, bytes(arg))
			if key not in self._seen:
				self._seen.add(key)
				self.results.append((cmd, bytes(arg)))
				self.last_progress = time.time()
				if cmd == 0xD7:               # installer-user block holds the access code
					try:
						code = arg[0x1D:0x25].decode('ascii')
						code = code.split('\0', 1)[0]
						self.icode = code or None
					except (UnicodeDecodeError, IndexError):
						self.icode = '<decode error>'
			# Always ACK (even a duplicate) so the panel streams the next record.
			self.pending = (cmd + 0x190, arg[2:4])
		elif cmd == 0x15:                     # 21: end of upload
			self.pending = None
			self.done = True


def render(results, icode, out=sys.stdout):
	print('=== BHS CONFIGURATION DOWNLOAD ===', file=out)
	print('records        : {}'.format(len(results)), file=out)
	print('installer code : {}'.format(icode if icode else '(not found)'), file=out)
	print('', file=out)
	for cmd, arg in results:
		print('-' * 72, file=out)
		print('{}   (len {})'.format(config_rpt_util.describe_config_block(cmd, arg), len(arg)), file=out)
		for addr, hexrow, ascii_row in config_rpt_util.make_hexdump(arg, 16):
			print('  {}:  {:<48}  |{}|'.format(addr, hexrow, ascii_row), file=out)


def main():
	if len(sys.argv) < 2:
		print('Usage: {} <serial_port> [output_prefix]'.format(sys.argv[0]), file=sys.stderr)
		sys.exit(255)
	port = sys.argv[1]
	prefix = sys.argv[2] if len(sys.argv) > 2 else None

	bus = Intellibus(port)
	dl = Downloader(bus)
	t = threading.Thread(target=bus.run, daemon=True)
	t.start()

	# Finish on an explicit end-of-upload, or when no new record has arrived for a
	# while (some panels don't send cmd 21), with an overall safety cap.
	hard_deadline = time.time() + 120
	while not dl.done and time.time() < hard_deadline:
		if dl.results and time.time() - dl.last_progress > 10:
			break
		time.sleep(0.2)
	bus.stop()

	if not dl.results:
		print('No records received. Check the connection (if you see no bus traffic at '
		      'all, TX/RX are probably swapped).', file=sys.stderr)
		sys.exit(1)

	render(dl.results, dl.icode)
	if prefix:
		with open(prefix + '.txt', 'w') as f:
			render(dl.results, dl.icode, out=f)
		with open(prefix + '.raw', 'w') as f:
			for cmd, arg in dl.results:
				f.write('{:04X} {}\n'.format(cmd, arg.hex()))
		print('\nWrote {0}.txt and {0}.raw'.format(prefix), file=sys.stderr)


if __name__ == '__main__':
	main()
