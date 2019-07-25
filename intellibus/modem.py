from intellibus import *

class ModemInterface(BasicInterface):
	# Work in progress
	def __init__(self, port, baudrate=38400):
		self.serial = Serial(port=port, baudrate=baudrate)
		self.connected = False
		self.so_far = b''
	
	def _get_byte_from_modem(self):
		b = self.serial.read()
		if self.connected:
			self.so_far += b
			if self.so_far.starts_with('NO CARRIER'):
				self.connected = False
				self.so_far = ''
			elif not 'NO CARRIER'.starts_with(self.so_far):
				self.so_far = ''
			return b
		elif len(self.so_far) > 0 and self.so_far[-1] in b'\n\r':
			if self.so_far[:-1] == b'RING':
				self.serial.write(b'ATA\r\n')
			elif self.so_far.startswith(b'CONNECT '):
				self.connected = True
			self.so_far = b''
		self.so_far += b
		return None
	
	def get_byte(self):
		while True:
			b = self._get_byte_from_modem()
			if b is not None:
				return b
	
	def send_bytes(self, data):
		while not self.connected:
			self._get_byte_from_modem()
		self.serial.write(data)
	
	def dial(self, number):
		self.serial.write('ATDT{}\r\n'.format(number).encode('ascii'))

class VivaldiPacket(Packet):
	def __init__(self, body, panel_id=0xFFFFFFFF, sync=(0, 0)):
		self.panel_id = panel_id
		self.body = body
		self.sync_byte = (sync[0] << 5) | (sync[1] << 2) | (2 if len(body) == 0 else 0)
	
	def gen_data(self):
		return struct.pack('<IBB', panel_id, sync_byte, 0) + self.body

class VivaldiMessage(VivaldiPacket):
	def __init__(self, msg, des_key=None, panel_id=0xFFFFFFFF, sync=(0, 0)):
		if type(msg) is tuple:
			self.msg = struct.pack('<HH', len(msg[1])+4, msg[0]) + msg[1]
		else:
			self.msg = msg
		self.des_key = des_key
		self.flags = 4 if des_key is None else 0x84
		body = bytes([self.flags]) + self.msg
		super().__init__(self, body, panel_id=panel_id, sync=sync)
	
	def __repr__(self):
		return '<({:02o}) {:08X}:{:5} [ {} ] >'.format(self.sync_byte>>2, self.panel_id, self.getcmd(), tohex(self.getarg()))
		
	def getcmd(self):
		return self.cmd
	
	def getarg(self):
		#TODO: Decrypt DES-ECB if necessary
		return self.arg

class VivaldiSession(Connection):
	def __init__(self, iface, panel_id=None, **kwargs):
		super().__init__(iface, **kwargs)
		self.is_server = (panel_id is None)
		if self.is_server:
			self.panel_id = 0xFFFFFFFF
		else:
			self.panel_id = panel_id

		self.des_key = '62803B4919AB1CBC'
		
		self.svsync = 0
		self.clsync = 0

	def packet_type(self, pkt):
		try:
			if type(pkt) is VivaldiMessage:
				return 'msg'
			elif (pkt.sync_byte & 2) > 0:
				return 'sync'
			else:
				return None
		except KeyError:
			return None
	
	def decode_packet(self, pkt):
		data = bytes(pkt)[:-2]
		if len(data) >= 6:
			panel_id, sync_byte = struct.unpack('<IB', data[:5])
			sync = (sync_byte >> 5, sync_byte >> 2 & 7)

			if len(data) >= 11:
				return VivaldiMessage(data[7:], des_key=(self.des_key if data[6]&0x80 else None), panel_id=panel_id, sync=sync)
			else:
				return VivaldiPacket(data[6:], panel_id=panel_id, sync=sync)
		else:
			return pkt
