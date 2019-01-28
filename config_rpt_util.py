from intellibus import tohex
import struct

def fmt_16bit_hex(n):
	return '{:04X}'.format(n)

def make_hexdump(data, width=32):
	row_count = len(data) // width
	if len(data) % width > 1:
		row_count += 1
	
	rows = []

	for i in range(row_count):
		addr = width*i
		row_bytes = data[addr:addr+width]
		addr_str = fmt_16bit_hex(addr)
		data_row_str = tohex(row_bytes)
		ascii_str = ''.join([chr(n) if 32 <= n <= 126 else '.' for n in row_bytes])
		rows.append((addr_str, data_row_str, ascii_str))
	
	return rows

def describe_config_block(cmd, arg):
	def int16(offset):
		return struct.unpack('<H', arg[offset:offset+2])[0]
	
	name = 'Unknown Data'
	if cmd == 0xC8:
		name = 'Panel Configuration'
	elif cmd == 0xC9:
		name = 'Communicator {}'.format(int16(2) + 1)
	elif cmd == 0xCA:
		name = 'Account {}'.format(arg[1] + 1)
	elif cmd == 0xCC:
		name = 'Alarm Output'
	elif cmd == 0xD0:
		name = 'User {}'.format(int16(2) + 1)
	elif cmd == 0xD1:
		name = 'Zone {}'.format(arg[3] + 1)
	elif cmd == 0xD3:
		name = 'Device {0} (0x{0:04X})'.format(int16(18))
	elif cmd == 0xD5:
		name = 'Input'
	elif cmd == 0xD7:
		name = 'Installer User'
	elif cmd == 0xDA:
		name = 'Script {}'.format(int16(4) + 1)
	
	return '[{:04X}] {}'.format(cmd, name)

if __name__ == '__main__':
	print('This Python script is designed to be imported as a library, not run directly.')
