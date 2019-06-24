#!/usr/bin/python3

import sys
from os import chdir
import bsl

chdir('mod')

labels = {}

asmcode = ''
address = 0

try:
	with open('base.bin', 'rb') as f:
		rom = f.read()
except FileNotFoundError:
	print('Base firmware image not found.', file=sys.stderr)
	print('The default patchsrc.txt file is designed to be applied to BHS-4000 firmware version 015.021.000.', file=sys.stderr)
	print("If you have this version, dump your ROM, and place the image in the 'mod' directory with the name 'base.bin'.", file=sys.stderr)
	print('', file=sys.stderr)
	print('Note: To prevent the original firmware from being restored by the panel, you must change at least one byte in the backup image to invalidate the checksum.', file=sys.stderr)
	print('The backup image is located inside the ROM image. Search for "ENTER INSTALLER" (or any string in the FW) and change one byte in the SECOND copy of that string.', file=sys.stderr)
	print('If that string only appears once, there is no need to do anything.', file=sys.stderr)
	sys.exit(1)

def patchbytes(data, offset, replacement):
	patch_end = offset + len(replacement)
	return data[:offset] + replacement + data[patch_end:]

def preprocess_asm_line(line):
	def fmt_const(num):
		return '0{:X}h'.format(num)
	out = ''
	ampersand = 0
	while True:
		ampersand = line.find('&')
		if ampersand == -1:
			break

		out += line[:ampersand]
		try:
			mode = line[ampersand+1]
		except IndexError:
			return out + '&'

		line = line[ampersand+2:]

		n = 0
		if mode in ':^+':
			for c in line:
				if c.isalnum() or c == '_':
					n += 1
				else:
					break

			addr = labels[line[:n]]
			line = line[n:]
			ofs = fmt_const(addr & 0xFFFF)
			seg = fmt_const(addr >> 16)

			if mode == ':':
				# Lower address
				out += ofs
			elif mode == '^':
				# Segment number
				out += seg
			elif mode == '+':
				# Segment, Offset
				out += '#{}, #{}'.format(seg, ofs)
		else:
			out += '&' if mode == '&' else ('&' + mode)
	
	return out + line

def finish_asm_section():
	global asmcode, address, labels, rom
	if len(asmcode) > 0:
		code = bsl.assemble(asmcode)
		rom = patchbytes(rom, address, code)
		address += len(code)
		if address % 2 == 1:
			address += 1
		asmcode = ''

print('Applying patch...')
with open('patchsrc.txt', 'r') as srcfile:
	for line in srcfile:
		line = line.rstrip('\n').lstrip()
		if len(line) == 0:
			continue
		elif line[0] == '#':
			# Comment
			pass
		elif line[0] == '@':
			# Target address
			finish_asm_section()
			print(line)
			address = int(line[1:], base=16)
		elif line[0] == '-':
			# Section name
			finish_asm_section()
			print(line)
			labels[line[1:].lstrip()] = address
		elif line[0] == '<':
			# Include
			with open(line[1:].lstrip(), 'r') as f:
				for iline in f:
					asmcode += preprocess_asm_line(iline)
				asmcode += '\n'
		else:
			# Just a line of code
			asmcode += preprocess_asm_line(line) + '\n'

finish_asm_section()

with open('patched.bin', 'wb') as f:
	f.write(rom)
	print("Done. Patched firmware has been written to 'mod/patched.bin'.")
