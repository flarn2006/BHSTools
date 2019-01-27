from intellibus import tohex

def fmt_16bit_hex(n):
	return '{:04X}'.format(n)

def make_hexdump(data, width=32):
	row_count = len(data) // width
	if len(data) % width > 1:
		row_count += 1
	
	rows = []

	for i in range(row_count):
		addr = width*i
		row_bytes = data[addr:addr+width]
		addr_str = fmt_16bit_hex(addr)
		data_row_str = tohex(row_bytes)
		ascii_str = ''.join([chr(n) if 32 <= n <= 126 else '.' for n in row_bytes])
		rows.append((addr_str, data_row_str, ascii_str))
	
	return rows

if __name__ == '__main__':
	print('This Python script is designed to be imported as a library, not run directly.')
