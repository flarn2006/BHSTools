from intellibus import *

class TestDevice(VirtDevice):
	def handle_cmd(self, cmd, arg):
		print('{:04X} ( {} )'.format(cmd, arg))

bus = Interface('/dev/ttyUSB0')
dev = TestDevice(0x06, 3249, fromhex('00 00 00 AB CD EF'), 0xFFFF, 0xFFFF)
dev.xmitters.append(bus.write)

while True:
	dev.receive(bus.read())
