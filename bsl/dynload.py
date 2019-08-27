#!/usr/bin/python3
from serial import Serial
import bsl
import sys
import struct
from time import sleep
from os.path import isfile

sector = 0x90000

if not isfile('.flash_warning_given.flag'):
	print("This script writes to your panel's Flash memory. Please run flash.py and accept the warning first.")

with open('mod/header.inc') as f:
	head = f.read()
with open(sys.argv[2], 'r') as f:
	asm = f.read()

code = bsl.assemble(asm, header=head)

ser = Serial(sys.argv[1], 38400)
bsl.init(ser)

bootcode = bsl.fromhex(''.join([
	'E6F40001',  # mov r4, #100h
	# findbit:
	'D7000900',  # exts #9, #1
	'9884',      # mov r8, [r4+]
	'2DFC',      # jmpr cc_Z, findbit
	'26F40201',  # sub r4, #102h
	'5C44',      # shl r4, #4
	'2B58',      # prior r5, r8
	'5C15',      # shl r5, #1
	'0045',      # add r4, r5
	'06F40010',  # add r4, #1000h
	'9C04',      # jmpi cc_UC, [r4]
]))

def flash_bootcode():
	print('Flashing bootcode...')
	bsl.flash_write(ser, sector, bootcode)

if bsl.readmem(ser, sector, 2) == b'\xff\xff':
	flash_bootcode()

print('Looking for address...')
addr = 0
addrbits = bsl.readmem(ser, sector+0x100, 0xF00)
for i in range(0x100, 0x1000, 2):
	dataindex = i - 0x100
	data = addrbits[dataindex:dataindex+2]
	print('0x{:X} = {}'.format(i, bsl.tohex(data)))
	word = 256 * data[1] + data[0]
	if word > 0:
		bitaddr = i
		addr = 16 * (i - 0x100) + 0x1000
		print('addr='+hex(addr))
		while word < 0x8000:
			addr += 2
			word <<= 1
		print('addr='+hex(addr))
		break

if addr > 0x1000:
	addr += 4

if addr == 0 or addr + len(code) > 0x10000:
	print('No more space! Erasing sector...')
	bsl.flash_erase(ser, sector)
	sleep(7)
	flash_bootcode()
	addr = 0x1000
	bitaddr = 0x100

endaddr = addr + len(code)
lastbitaddr = 0x100 + (endaddr - 0x1000) // 32 * 2

print('Setting address bits...')
for i in range(bitaddr, lastbitaddr, 2):
	print('0x{:X} = '.format(i), end='', flush=True)
	print(bsl.tohex(bsl.readmem(ser, sector + i, 2)), end='', flush=True)
	bsl.flash_write(ser, sector + i, b'\0\0')
	print(' -> 00 00')
last = 0xFFFF
last >>= (endaddr % 32) // 2
if last < 0xFFFF:
	print('0x{:X} = {}'.format(lastbitaddr, bsl.tohex(struct.pack('<H', last))))
	bsl.flash_write(ser, sector + lastbitaddr, struct.pack('<H', last))

code += bytes([0xFA, sector >> 16]) + struct.pack('<H', addr)
endaddr += 4

print('Programming 0x{:X}-0x{:X} ({} bytes)...'.format(sector + addr, sector + endaddr - 1, len(code)))
bsl.flash_write(ser, sector + addr, code)

print('Rebooting panel...')
bsl.run(ser, bsl.fromhex('B748B7B7'), maxread=0)

print('Done.')
