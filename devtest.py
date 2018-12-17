from intellibus import *

class TestDevice(VirtDevice):
	def handle_cmd(self, cmd, arg):
		print('{:04X} ( {} )'.format(cmd, arg))
		if cmd == 0x4BD:
			bus.send(0, self.addr, (0x4BD, arg), count=3)

bus = Intellibus('/dev/ttyUSB0', debug='tx,sync')
dev = TestDevice(bus, 6, 3249, fromhex('00 00 00 AB CD EF'), 0xFFFF, (0xFF, 0xEE))
bus.run()
