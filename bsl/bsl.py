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

def assemble(code, base=0xFA60):
	with open('TEMP.A66', 'w') as f:
		print('$MOD167', file=f)
		print('$NODEBUG', file=f)
		print('$NOTYPE', file=f)
		print('BOOTSTRAP section code at 0{:04X}h'.format(base-12), file=f)
		print('boot proc', file=f)
		print("db 'START_MARKER'", file=f)
		print(code, file=f)
		print("db 'END_MARKER'", file=f)
		print('boot endp', file=f)
		print('BOOTSTRAP ends', file=f)
		print('end', file=f)
	
	try:
		subprocess.check_output(['./A166.EXE', 'TEMP.A66'])
		error_output = None
	except subprocess.CalledProcessError as ex:
		error_output = ex.output
		if len(ex.output) > 0:
			try:
				with open('TEMP.LST', 'a') as f:
					print('\nA166 output:\n', file=f)
					print(ex.output.decode('windows-1252'), file=f)
			except:
				pass

	if error_output is not None:
		raise AssemblerError('An error occurred during assembly. Check the results in TEMP.LST.', output=error_output)
	
	with open('TEMP.OBJ', 'rb') as f:
		obj = f.read()
		a = obj.index(b'START_MARKER') + 12
		b = obj.rindex(b'END_MARKER')
		return obj[a:b]

def load_bsl(ser:Serial, program:bytes, allow_overflow=False):
	if len(program) > 32 and not allow_overflow:
		raise IndexError('Maximum program size is 32 bytes')

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
		'F2F160FA',    # mov r1, #0FA60h
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
