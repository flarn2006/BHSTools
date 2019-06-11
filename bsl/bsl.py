from serial import Serial

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

def load_bsl(ser:Serial, program:bytes):
	if len(program) > 32:
		raise IndexError('Maximum program size is 32 bytes')

	ser.write(b'\0')
	if ser.read(1)[0] != 0xD5:
		raise BSLCommError('Incorrect identification byte returned')
	
	program += b'\0' * (32 - len(program))
	ser.write(program)
