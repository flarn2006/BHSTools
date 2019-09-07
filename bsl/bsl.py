import os
import os.path
from serial import Serial
import struct
import subprocess

def tohex(data):
	return ' '.join(['{:02X}'.format(b) for b in data])

def fromhex(text):
	text = text.replace(' ', '')
	if len(text) % 2 == 0:
		split = [text[i:i+2] for i in range(0, len(text), 2)]
		return bytes([int(h, 16) for h in split])
	else:
		raise ValueError('An even number of hex digits must be given.')

class BSLCommError(Exception):
	pass

class AssemblerError(Exception):
	def __init__(self, output=None):
		self.output = output

def assemble(code, base=0, header=''):
	with open('TEMP.A66', 'w') as f:
		print('$MOD167', file=f)
		print('$NODEBUG', file=f)
		print('$NOTYPE', file=f)
		print('$GEN', file=f)
		try:
			with open('REG167.INC', 'r') as inc:
				print(inc.read(), file=f)
		except OSError as ex:
			print('; ERROR OPENING REG167.INC:', file=f)
			print('; {}'.format(ex), file=f)
		print(header, file=f)
		print('BOOTSTRAP section code at 0{:04X}h'.format((base-12) % 0x10000), file=f)
		print('boot proc', file=f)
		print("db 'START_MARKER'", file=f)
		print(code, file=f)
		print("db 'END_MARKER'", file=f)
		print('boot endp', file=f)
		print('BOOTSTRAP ends', file=f)
		print('end', file=f)
	
	if os.path.isfile('TEMP.OBJ'): os.remove('TEMP.OBJ')
	if os.path.isfile('TEMP.LST'): os.remove('TEMP.LST')

	msg_if_error = 'An unknown error occurred during assembly.'
	try:
		output = subprocess.check_output(['wine', './A166.EXE', 'TEMP.A66'], stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as ex:
		if len(ex.output) > 0:
			try:
				with open('TEMP.LST', 'a') as f:
					print('\nA166 output:\n', file=f)
					print(ex.output.decode('windows-1252'), file=f)
				msg_if_error = 'An error occurred during assembly. Check the results in TEMP.LST.'
			except OSError:
				msg_if_error = ex.output

	if not os.path.isfile('TEMP.OBJ'):
		raise AssemblerError(msg_if_error)
	
	with open('TEMP.OBJ', 'rb') as f:
		try:
			obj = f.read()
			a = obj.index(b'START_MARKER') + 12
			b = obj.rindex(b'END_MARKER')
			return obj[a:b]
		except IndexError:
			raise AssemblerError('Unexpected error parsing assembler output. Check TEMP.LST and TEMP.OBJ.')


def load_bsl(ser:Serial, program:bytes, allow_overflow=False):
	if len(program) > 32 and not allow_overflow:
		raise ValueError('Maximum program size is 32 bytes')

	ser.reset_input_buffer()
	ser.write(b'\0')
	if ser.read(1)[0] != 0xD5:
		raise BSLCommError('Incorrect identification byte returned')
	
	program += b'\0' * (32 - len(program))
	ser.write(program)

def load_stg1(ser:Serial, program:bytes):
	maxlen = 0xFC00 - 0xFA60
	if len(program) > maxlen:
		raise IndexError('Maximum program size is {} bytes'.format(maxlen))
	
	pgmlen = tohex(struct.pack('<H', len(program)))
	
	stage1 = fromhex(''.join([
		'E6F160FA',    # mov r1, #0FA60h
		'E6F2'+pgmlen, # mov r2, len(program)
		# wait:
		'9AB7FE70',    # jnb S0RIR, wait
		'7EB7',        # bclr S0RIR
		'F2F3B2FE',    # mov r3, S0RBUF
		'B961',        # movb [r1], rl3
		'0811',        # add r1, #1
		'2821',        # sub r2, #1
		'3DF7',        # jmpr cc_NZ, wait
		'CC00',        # nop
		'CC00',        # nop
		'CC00'         # nop
	]))

	load_bsl(ser, stage1+program, allow_overflow=True)

def init(ser:Serial):
	pgm = fromhex(''.join([
		'D100',      # atomic #1
		'0A86FFAF',  # bfldl BUSCON0, #0FFh, #0AFh
		'D100',      # atomic #1
		'1A8604D6',  # bfldh BUSCON0, #0D6h, #4
		'E60C0540',  # mov ADDRSEL1, #4005h
		'E68A0F04',  # mov BUSCON1, #40Fh
		'E6F08080',  # mov r0, #8080h
		'0D14',      # jmpr cc_UC, start
		
		# readbyte:
		'9AB7FE70',  # jnb S0RIR, readbyte
		'7EB7',      # bclr S0RIR
		'6659FF00',  # and S0RBUF, #0FFh
		'E102',      # movb rl1, #0
		'72F1B2FE',  # or r1, S0RBUF
		'CB00',      # ret

		# readword:
		'BBF6',      # callr readbyte
		'5C81',      # shl r1, #8
		'BBF4',      # callr readbyte
		'1C81',      # rol r1, #8
		'CB00',      # ret

		# sendbyte:
		'C5F2B0FE',  # movbz S0TBUF, rl1
		# sendbyte_wait:
		'9AB6FE70',  # jnb S0TIR, sendbyte_wait
		'7EB6',      # bclr S0TIR
		'CB00',      # ret

		# start:
		'E7F23F00',  # movb rl1, #3Fh
		'BBF7',      # callr sendbyte
		'BBF1',      # callr readword
		'F021',      # mov r2, r1
		'BBEF',      # callr readword
		'5012',      # xor r1, r2
		'46F1CDAB',  # cmp r1, #0ABCDh
		'3DF6',      # jmpr cc_NZ, start
		'E003',      # mov r3, #0
		# loop:
		'BBE0',      # callr readbyte
		'D7004100',  # exts #41h, #1
		'B923',      # movb [r3], rl1
		'0831',      # add r3, #1
		'2821',      # sub r2, #1
		'3DF9',      # jmpr cc_NZ, loop
		'DA410000',  # calls #41h, #0
		'0DEB'       # jmpr cc_UC, start
	]))

	load_stg1(ser, pgm)
	if ser.read(1) != b'?':
		raise BSLCommError('Stage 2 bootloader execution was not detected.')

def run(ser:Serial, code:bytes, maxread=1):
	lc = len(code) + 2
	header = struct.pack('<HH', lc, lc^0xABCD)
	ser.reset_input_buffer()
	ser.write(header + code + b'\xdb\0')

	out = b''
	if maxread < 0:
		try:
			for _ in range(maxread):
				out += ser.read(1)
			return out
		except KeyboardInterrupt:
			return out
	else:
		for _ in range(maxread):
			out += ser.read(1)
		return out

def readmem(ser:Serial, addr, length):
	if addr % 2 != 0:
		raise IndexError('Address must be 16-bit aligned.')
	elif length % 2 != 0:
		raise ValueError('Length must be a multiple of two bytes.')
	
	return run(ser, fromhex(''.join([
		'E6F1'+tohex(struct.pack('<H', addr & 0xFFFF)),    # mov r1, addr&0xFFFF
		'E6F2{:02X}00'.format(addr>>16),                   # mov r2, addr>>16
		'E6F3'+tohex(struct.pack('<H', length & 0xFFFF)),  # mov r3, length&0xFFFF
		'E6F4'+tohex(struct.pack('<H', length>>16)),       # mov r4, length>>16
		# loop:
		'DC02',                                            # exts r2, #1
		'A851',                                            # mov r5, [r1]
		'C5FAB0FE',                                        # movbz S0TBUF, rl5
		# wait_tx1:
		'9AB6FE70',                                        # jnb S0TIR, wait_tx1
		'7EB6',                                            # bclr S0TIR
		'C5FBB0FE',                                        # movbz S0TBUF, rh5
		# wait_tx2:
		'9AB6FE70',                                        # jnb S0TIR, wait_tx2
		'7EB6',                                            # bclr S0TIR
		'0812',                                            # add r1, #2
		'1820',                                            # addc r2, #0
		'2832',                                            # sub r3, #2
		'3840',                                            # subc r4, #0
		'F053',                                            # mov r5, r3
		'7054',                                            # or r5, r4
		'3DED'                                             # jmpr cc_NZ, loop
	])), maxread=length+1)[:length]

def writemem(ser:Serial, addr, data):
	run(ser, fromhex(''.join([
		'E6F1'+tohex(struct.pack('<H', addr & 0xFFFF)),  # mov r1, addr&0xFFFF
		'E6F2{:02X}00'.format(addr>>16),                 # mov r2, addr>>16
		'E6F3'+tohex(struct.pack('<H', len(data))),      # mov r3, len(data)
		# wait:
		'9AB7FE70',                                      # jnb S0RIR, wait
		'7EB7',                                          # bclr S0RIR
		'F2F4B2FE',                                      # mov r4, S0RBUF
		'DC02',                                          # exts r2, #1
		'B981',                                          # movb [r1], rl4
		'0811',                                          # add r1, #1
		'1820',                                          # addc r2, #0
		'2831',                                          # sub r3, #1
		'3DF5'                                           # jmpr cc_NZ, wait
	])), maxread=0)
	ser.write(data)
	if ser.read(1) != b'?':
		raise BSLCommError('Did not receive expected response from panel.')

def flash_write(ser:Serial, addr, data):
	addr %= 0x200000
	addr += 0x200000

	if addr % 2 != 0:
		raise IndexError('Address must be 16-bit aligned.')
	elif len(data) % 2 != 0:
		raise ValueError('Data length must be a multiple of two bytes.')
	elif len(data) > min(0x10000 - (addr & 0xFFFF), 0xFFFF):
		raise ValueError('Maximum data length is 65535 bytes, and must not cross segment boundaries.')
	
	run(ser, fromhex(''.join([
		'E6F1'+tohex(struct.pack('<H', addr & 0xFFFF)),  # mov r1, addr&0xFFFF
		'E6F2{:02X}00'.format(addr>>16),                 # mov r2, addr>>16
		'E6F3'+tohex(struct.pack('<H', len(data))),      # mov r3, len(data)
		'E6F5AA00',                                      # mov r5, #0aah
		'E6F6A000',                                      # mov r6, #0a0h
		'E6F85500',                                      # mov r8, #55h
		'E6F9F000',                                      # mov r9, #0f0h
		# wait_rx1:
		'9AB7FE70',                                      # jnb S0RIR, wait_rx1
		'7EB7',                                          # bclr S0RIR
		'F2F4B2FE',                                      # mov r4, S0RBUF
		'9AB7FE70',                                      # jnb S0RIR, wait_rx2
		'7EB7',                                          # bclr S0RIR
		'F2F7B2FE',                                      # mov r7, S0RBUF
		'F19E',                                          # movb rh4, rl7
		'D7202000',                                      # exts #20h, #3
		'F6F5AA0A',                                      # mov 0aaah, r5
		'F6F85405',                                      # mov 0554h, r8
		'F6F6AA0A',                                      # mov 0aaah, r6
		'DC02',                                          # exts r2, #1
		'B841',                                          # mov [r1], r4
		# wait_flash:
		'DC02',                                          # exts r2, #1
		'A871',                                          # mov r8, [r1]
		'5074',                                          # xor r7, r4
		'8AF7FB70',                                      # jb r7.7, wait_flash
		'DC02',                                          # exts r2, #1
		'B891',                                          # mov [r1], r9
		'0812',                                          # add r1, #2
		'1820',                                          # addc r2, #0
		'2832',                                          # sub r3, #2
		'3DE0'                                           # jmpr cc_NZ, wait_rx1
	])), maxread=0)
	ser.write(data)
	if ser.read(1) != b'?':
		raise BSLCommError('Did not receive expected response from panel.')

def readbyte(ser:Serial, addr):
	return run(ser, fromhex(''.join([
		'E6F2'+tohex(struct.pack('<H', addr & 0xFFFF)),  # mov r2, addr&0xFFFF
		'D700{:02X}00'.format(addr>>16),                 # exts addr>>16, #1
		'A922',                                          # movb rl1, [r2]
		'C5F2B0FE',                                      # movbz S0TBUF, rl1
		# wait:
		'9AB6FE70',                                      # jnb S0TIR, wait
		'7EB6'                                           # bclr S0TIR
	])), maxread=2)[0]

def flash_erase(ser:Serial, sector_addr):
	sector_addr %= 0x200000
	sector_addr += 0x200000
	
	run(ser, fromhex(''.join([
		'E6F1AA55',                                            # mov r1, #55aah
		'E6F28030',                                            # mov r2, #3080h
		'D7202000',                                            # exts #20h, #3
		'F7F2AA0A',                                            # movb 0aaah, rl1
		'F7F35505',                                            # movb 0555h, rh1
		'F7F4AA0A',                                            # movb 0aaah, rl2
		'D7102000',                                            # exts #20h, #2
		'F7F2AA0A',                                            # movb 0aaah, rl1
		'F7F35505',                                            # movb 0555h, rh1
		'D700{:02X}00'.format(sector_addr>>16),                # exts sector_addr>>16, #1
		'F7F5'+tohex(struct.pack('<H', sector_addr & 0xFFFF)), # movb [sector_addr&0xFFFF], rh2
		# wait:
		'D700{:02X}00'.format(sector_addr>>16),                # exts sector_addr>>16, #1
		'F2F3'+tohex(struct.pack('<H', sector_addr & 0xFFFF)), # mov r3, [sector_addr&0xFFFF]
		'9AF3FA70'                                             # jnb r3.7, wait
	])))

def boot(ser:Serial):
	run(ser, fromhex('B748B7B7'), maxread=0)  # srst
