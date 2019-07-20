def tohex(data):
	return ' '.join(['{:02X}'.format(b) for b in data])

def fromhex(text):
	text = text.replace(' ', '')
	if len(text) % 2 == 0:
		split = [text[i:i+2] for i in range(0, len(text), 2)]
		return bytes([int(h, 16) for h in split])
	else:
		raise ValueError('An even number of hex digits must be given.')

def hexdump(data):
	out = ''
	for i in range(0, len(data), 16):
		row = data[i:i+16]
		asc = ''.join([chr(b) if chr(b).isprintable() else '.' for b in row])
		out += '{:04X}:  {:47s}  |{:16s}|\n'.format(i, tohex(row), asc)
	return out
