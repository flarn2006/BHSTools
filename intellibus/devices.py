from queue import Queue
from intellibus import *

class Keypad(VirtDevice):
	def __init__(self, ibus:Intellibus, kind:int, model:int, serial_no:bytes, hdw_conf:int=0, fw_ver:(int,int)=0, addr:int=None):
		super().__init__(ibus, kind, model, serial_no, hdw_conf, fw_ver, addr)
		self.keyqueue = Queue()
	
	def on_ping(self):
		while not self.keyqueue.empty():
			keycode = self.keyqueue.get()[:2].rjust(2, '0')
			if keycode.upper() in '3C BC 68 E8 3E BE 1B 9B 73 F3 08 88 2D AD 2B AB'.split(' '):
				keycode = '1B ' + keycode
			self.send_now(2020, fromhex(keycode))
	
	def key(self, keycode):
		self.keyqueue.put(keycode)


class IconKeypad(Keypad):
	def __init__(self, ibus:Intellibus, serial_no:bytes, hdw_conf:int=0, fw_ver:(int,int)=0, model:int=3101):
		super().__init__(ibus, 1, model, serial_no, hdw_conf, fw_ver)
		self.acct = 0
		self.lcd = [False] * 64
	
	def handle_cmd(self, cmd, arg):
		if cmd == 2010 and len(arg) >= 9 and arg[0] == self.acct:
			for index in range(64):
				byte = index // 8
				bit = index % 8
				self.lcd[index] = (arg[byte+1] & (1<<bit) > 0)


class Programmer(Keypad):
	def __init__(self, ibus):
		super().__init__(ibus, 5, 3121, fromhex('00 00 FF FF FF FF'), 0, (7,1), 0x7FFE)
		self.display = b' ' * 16 * 4
		self.ping_counter = 0
		self.curX = 0
		self.curY = 0
		self.curVis = False

	def writestr(self, index, src):
		dest = self.display
		self.display = dest[:index] + src[:len(dest)-index] + dest[index+len(src):]

	def handle_cmd(self, cmd, arg):
		if cmd == 2012:
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
				self.writestr(16*self.curY + self.curX, text)
				self.curX += len(text)
				self.curY += self.curX // 16
				self.curX %= 16
