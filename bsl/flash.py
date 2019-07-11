#!/usr/bin/python3

from serial import Serial
from time import sleep
from os.path import isfile
import bsl
import sys

sector_sizes = [0x4000, 0x2000, 0x2000, 0x8000] + [0x10000]*31

def print_sector_chart():
	print('╔══════╤══════════╤══════════╤═══════╗')
	print('║ Sec# │ Start    │ End      │ Bytes ║')
	print('╟──────┼──────────┼──────────┼───────╢')
	addr = 0
	for i in range(len(sector_sizes)):
		size = sector_sizes[i]
		old_addr = addr
		addr += size
		print('║ {:4d} │ 0x{:06X} │ 0x{:06X} │ {:5d} ║'.format(i, old_addr, addr-1, size))
	print('╚══════╧══════════╧══════════╧═══════╝')

if len(sys.argv) < 3:
	print('Usage: {} port binfile sector-range'.format(sys.argv[0]), file=sys.stderr)
	print('', file=sys.stderr)
	print_sector_chart()
	sys.exit(255)

def parse_range(range_str):
	sectors = set()
	for part in range_str.split(','):
		dash = part.find('-')
		if dash == -1:
			sectors.add(int(part))
		else:
			start = int(part[:dash])
			end = int(part[dash+1:])
			for s in range(start, end+1):
				sectors.add(s)
	return sectors

def askyesno(prompt):
	while True:
		entry = input(prompt).lower()
		if entry == 'yes':
			return True
		elif entry == 'no':
			return False
		else:
			print("Please enter `yes' or `no'.")

def give_warning():
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
						return False
				else:
					print("I don't see a file with the default name that romdump.py writes to.")
					print("I'm guessing that's because you moved or renamed it?")
					print('')
					if not askyesno('This is your final warning. Are you absolutely sure you still have the ROM dump, and wish to proceed? '):
						print("Good idea, make sure you check that first. Email your dump to flarn2006@gmail.com if you have any doubt that it's good.")
						return False
			else:
				print('')
				print('Please do yourself a favor and do that first.')
				print('Power up your panel in BSL mode and run:')
				print('')
				print('\t./romdump.py {} 115200'.format(sys.argv[1]))
				print('')
				return False
		else:
			return False
		
		print('')
		print('OK, proceeding as instructed.')

		try:
			with open('.flash_warning_given.flag', 'w'):
				pass
			print('The previous warning will not appear again.')
		except OSError:
			pass
	
	return True

if not give_warning():
	sys.exit(254)

try:
	sectors = parse_range(sys.argv[3])
except (IndexError, ValueError):
	def print_examples(file=sys.stdout):
		print('\tSingle sector:     6', file=file)
		print('\tRange of sectors:  1-34', file=file)
		print('\tMixed set:         4,7-16,18 (sector 4 + sectors 7-16 + sector 18)', file=file)

	if False:  # TODO: use this code somewhere else
		if askyesno('Reflash everything except boot sector? '):
			print('OK. In the future, specify the range directly (e.g. 1-34) to suppress this warning.')
		else:
			print('Please specify which sector(s) to reflash on the command line.')
			print('Examples:')
			print_examples()
			sys.exit(2)

	print('Invalid range entered.', file=sys.stderr)
	print('Examples of valid ranges:', file=sys.stderr)
	print_examples(sys.stderr)
	sys.exit(255)

with Serial(sys.argv[1], baudrate=115200) as s:
	with open(sys.argv[2], 'rb') as f:
		bsl.init(s)
		addr = 0
		for i in range(35):
			if i in sectors:
				f.seek(addr)
				print('Sector {} (0x{:X}-0x{:X}, {} bytes):'.format(i, addr, addr+sector_sizes[i]-1, sector_sizes[i]))
				newdata = f.read(sector_sizes[i])
				print(' - Erasing...')
				bsl.flash_erase(s, addr)
				sleep(7)  # Maximum erase time as listed in AM29F160DB datasheet
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
