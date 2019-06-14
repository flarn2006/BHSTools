#!/usr/bin/python3
import sys
from serial import Serial
from bsl import load_bsl, fromhex

program = fromhex(''.join([
	'E60C0540', # mov ADDRSEL1, #4005h
	'E68A0F04', # mov BUSCON1, #40Fh
	'E6FB4000', # mov r11, #40h
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

addr = 0x400000
with open('ram.bin', 'wb') as f:
	print('Dumping 0x400000-0x41FFFF:')
	print('\nIMPORTANT:')
	print('Keep in mind you must enter BSL mode from a running state')
	print('to preserve the contents of RAM. To do this, ground P0L.4')
	print('with the panel running, and induce a system reset. If you')
	print('power off the panel, the contents of RAM will be lost.')
	print('\nYou can induce a reset (crash) from testbed as follows:')
	print('\n\tsend(0, 32)\n')
	try:
		while addr < 0x420000:
			data = s.read()
			f.write(data)
			addr += 1
			if addr & 0xFFF == 0:
				print('Dumped 0x{:06X}-0x{:06X}'.format(addr-0x1000, addr-1))
				f.flush()
	except KeyboardInterrupt:
		pass

s.close()
