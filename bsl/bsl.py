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

def assemble(code, base=0):
	with open('TEMP.A66', 'w') as f:
		print('$MOD167', file=f)
		print('$NODEBUG', file=f)
		print('$NOTYPE', file=f)
		try:
			with open('REG167.INC', 'r') as inc:
				print(inc.read(), file=f)
		except OSError as ex:
			print('; ERROR OPENING REG167.INC:', file=f)
			print('; {}'.format(ex), file=f)
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
		output = subprocess.check_output(['./A166.EXE', 'TEMP.A66'], stderr=subprocess.STDOUT)
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
		raise IndexError('Maximum program size is 32 bytes')

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
		'0A86FFAF',  # bfldl BUSCON0, #0FFh, #0AFh
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

def run(ser:Serial, code:bytes):
	lc = len(code) + 2
	header = struct.pack('<HH', lc, lc^0xABCD)
	ser.write(header + code + b'\xdb\0')

def readb(ser:Serial, addr):
	ser.reset_input_buffer()
	run(ser, fromhex(''.join([
		'E6F2'+tohex(struct.pack('<H', addr & 0xFFFF)),  # mov r2, addr&0xFFFF
		'D700{:02X}00'.format(addr>>16),                 # exts addr>>16, #1
		'A922',                                          # movb rl1, [r2]
		'C5F2B0FE',                                      # movbz S0TBUF, rl1
		# wait:
		'9AB6FE70',                                      # jnb S0TIR, wait
		'7EB6'                                           # bclr S0TIR
	])))
	return ser.read(2)[0]
