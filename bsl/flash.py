#!/usr/bin/python3

from serial import Serial
from time import sleep
from os.path import isfile
import bsl
import sys

sector_sizes = [0x4000, 0x2000, 0x2000, 0x8000] + [0x10000]*31

if len(sys.argv) < 3:
	print('Usage: {} port binfile [startsector] [endsector]'.format(sys.argv[0]), file=sys.stderr)
	print('', file=sys.stderr)
	print('╔══════╤══════════╤══════════╤═══════╗', file=sys.stderr)
	print('║ Sec# │ Start    │ End      │ Bytes ║', file=sys.stderr)
	print('╟──────┼──────────┼──────────┼───────╢', file=sys.stderr)
	addr = 0
	for i in range(len(sector_sizes)):
		size = sector_sizes[i]
		old_addr = addr
		addr += size
		print('║ {:4d} │ 0x{:06X} │ 0x{:06X} │ {:5d} ║'.format(i, old_addr, addr-1, size), file=sys.stderr)
	print('╚══════╧══════════╧══════════╧═══════╝', file=sys.stderr)
	sys.exit(255)

def askyesno(prompt):
	while True:
		entry = input(prompt).lower()
		if entry == 'yes':
			return True
		elif entry == 'no':
			return False
		else:
			print("Please enter `yes' or `no'.")

if not isfile('.flash_warning_given.flag'):
	print('WARNING:')
	print("This will overwrite your panel's firmware and programming!")
	print('If you already have a good firmware dump, you SHOULD be able to reflash that if anything goes wrong.')
	print("However, I cannot guarantee that. Either way, make sure you've dumped your ROM first!")
	print('')
	if askyesno('Do you accept this risk? '):
		print('')
		if askyesno('Do you have a ROM dump? '):
			print('')
			if isfile('firmware.bin'):
				if not askyesno('This is your final warning. Are you absolutely sure you wish to proceed? '):
					sys.exit(2)
			else:
				print("I don't see a file with the default name that romdump.py writes to.")
				print("I'm guessing that's because you moved or renamed it?")
				print('')
				if not askyesno('This is your final warning. Are you absolutely sure you still have the ROM dump, and wish to proceed? '):
					print("Good idea, make sure you check that first. Email your dump to flarn2006@gmail.com if you have any doubt that it's good.")
					sys.exit(2)
		else:
			print('')
			print('Please do yourself a favor and do that first.')
			print('Power up your panel in BSL mode and run:')
			print('')
			print('\t./romdump.py {} 115200'.format(sys.argv[1]))
			print('')
			sys.exit(2)
	else:
		sys.exit(2)
	
	print('')
	print('OK, proceeding as instructed.')

	try:
		with open('.flash_warning_given.flag', 'w'):
			pass
		print('The previous warning will not appear again.')
	except OSError:
		pass

try:
	startsector = max(0, int(sys.argv[3]))
except IndexError:
	print('Skipping sector 0 by default.')
	startsector = 1
try:
	endsector = min(34, int(sys.argv[4]))
except IndexError:
	endsector = len(sector_sizes) - 1

with Serial(sys.argv[1], baudrate=115200) as s:
	bsl.init(s)
	with open(sys.argv[2], 'rb') as f:
		addr = 0
		for i in range(endsector+1):
			if i >= startsector:
				f.seek(addr)
				print('Sector {} (0x{:X}-0x{:X}, {} bytes):'.format(i, addr, addr+sector_sizes[i]-1, sector_sizes[i]))
				newdata = f.read(sector_sizes[i])
				print(' - Erasing...')
				bsl.flash_erase(s, addr)
				sleep(10)
				print(' - Programming...')
				if sector_sizes[i] > 0x8000:
					bsl.flash_write(s, addr, newdata[:0x8000])
					bsl.flash_write(s, addr + 0x8000, newdata[0x8000:])
				else:
					bsl.flash_write(s, addr, newdata)
				print(' - Verifying...')
				check = bsl.readmem(s, 0x200000 + addr, sector_sizes[i])
				if check != newdata:
					print('Verification failed on sector {}'.format(i))
					break
			addr += sector_sizes[i]

print('Complete.')
