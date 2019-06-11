#!/usr/bin/python3
import sys
from serial import Serial
from bsl import load_bsl, fromhex

program = fromhex(''.join([
	'E6FB2000', # mov r11, #20h
	'50AA',     # xor r10, r10
	#loop:
	'DC0B',     # exts r11, #1
	'A92A',     # movb rl1, [r10]
	'C5F2B0FE', # movbz S0TBUF, rl1
	#wait:
	'9AB6FE70', # jnb S0TIR, wait
	'7EB6',     # bclr S0TIR
	'08A1',     # add r10, #1
	'18B0',     # addc r11, #0
	'0DF6',     # jmpr cc_UC, loop
]))

if len(sys.argv) != 3:
	sys.stderr.write('Usage: {} port baudrate\n'.format(sys.argv[0]))
	sys.stderr.write('Output goes to firmware.bin\n')
	sys.exit(255)

s = Serial(port=sys.argv[1], baudrate=int(sys.argv[2]))
load_bsl(s, program)

addr = 0
with open('firmware.bin', 'wb') as f:
	print('Dumping 0x000000-0x1FFFFF:')
	try:
		while addr < 0x200000:
			f.write(s.read())
			addr += 1
			if addr & 0xFFF == 0:
				print('Dumped 0x{:06X}-0x{:06X}'.format(addr-0x1000, addr-1))
				f.flush()
	except KeyboardInterrupt:
		pass

s.close()
