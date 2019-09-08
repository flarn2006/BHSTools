from time import sleep
import queue
from Crypto.Cipher import DES
from intellibus import *

class ModemInterface(BasicInterface):
	# Work in progress
	def __init__(self, port, baudrate=38400, answer=True, msg_callback=None):
		self.serial = Serial(port=port, baudrate=baudrate)
		self.connected = False
		self.so_far = b''
		self.answer = answer
		self.hangup_in_progress = False
		self.msg_callback = msg_callback
	
	def _msg_out(self, msg):
		if self.msg_callback is not None:
			self.msg_callback(msg)
	
	def _get_byte_from_modem(self):
		b = self.serial.read()
		if self.connected:
			self.so_far += b
			if self.so_far.startswith(b'NO CARRIER'):
				self._msg_out('Connection lost.')
				self.connected = False
				self.so_far = b''
			elif not b'NO CARRIER'.startswith(self.so_far):
				self.so_far = b''
			return b
		elif len(self.so_far) > 0 and self.so_far[-1] in b'\n\r':
			if self.so_far[:-1] == b'RING':
				if self.answer:
					self._msg_out('Ring! (Hello?)')
					self.serial.write(b'ATA\r\n')
				else:
					self._msg_out('Ring!')
			elif self.so_far.startswith(b'CONNECT '):
				self._msg_out('Connection established.')
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
		if not self.hangup_in_progress:
			self.serial.write(data)
	
	def dial(self, number):
		self.serial.write('ATDT{}\r\n'.format(number).encode('ascii'))
	
	def hangup(self):
		self.hangup_in_progress = True
		self.serial.write(b'+++')
		sleep(1.5)
		self.serial.write(b'ATH0\r\n')
		self.hangup_in_progress = False

class VivaldiPacket(Packet):
	def __init__(self, body=b'', panel_id=0xFFFFFFFF, sync=(0, 0)):
		self.panel_id = panel_id
		self.body = body
		self.sync_byte = (sync[0] << 5) | (sync[1] << 2) | (2 if len(body) == 0 else 0)
		self.sync = sync
	
	def __repr__(self):
		prefix = '({:02o}) {:08X}'.format(self.sync_byte>>2, self.panel_id)
		if len(self.body) > 0:
			return '<{} [ {} ] >'.format(prefix, tohex(self.body))
		else:
			return '<{}>'.format(prefix)
	
	def gen_data(self):
		return struct.pack('<IBB', self.panel_id, self.sync_byte, 0) + self.body

class VivaldiMessage(VivaldiPacket):
	def __init__(self, msg, des_key=None, panel_id=0xFFFFFFFF, sync=(0, 0)):
		if type(msg) is tuple:
			self.msg = struct.pack('<HH', len(msg[1])+4, msg[0]) + msg[1]
			encrypt_msg_if_needed = True
		else:
			self.msg = msg
			encrypt_msg_if_needed = False
		self.des_key = des_key
		
		if des_key is None:
			self.flags = 4
			self.cleartext = self.msg
		else:
			self.flags = 0x84
			self.cipher = DES.new(fromhex(des_key), DES.MODE_ECB)
			if encrypt_msg_if_needed:
				self.cleartext = self.msg
				if len(self.msg) % 8 > 0:
					self.msg += b'\0' * (8 - len(self.msg) % 8)
				self.msg = self.cipher.encrypt(self.msg)
			else:
				if len(self.msg) % 8 > 0:
					self.msg += b'\0' * (8 - len(self.msg) % 8)
				self.cleartext = self.cipher.decrypt(self.msg)

		body = bytes([self.flags]) + self.msg
		super().__init__(body, panel_id=panel_id, sync=sync)
	
	def __repr__(self):
		return '<({:02o}) {:08X}:{:5} [ {} ] >'.format(self.sync_byte>>2, self.panel_id, self.getcmd(), tohex(self.getarg()))
		
	def getcmd(self):
		return struct.unpack('<H', self.cleartext[2:4])[0]
	
	def getarg(self):
		msg_length = struct.unpack('<H', self.cleartext[:2])[0]
		return self.cleartext[4:msg_length]  # msg_length includes the 4 header bytes

class VivaldiSession(Connection):
	def __init__(self, iface, panel_id=None, **kwargs):
		super().__init__(iface, **kwargs)
		self.bus = iface
		self.reset(new_panel_id=0xFFFFFFFF if panel_id is None else panel_id)
	
	def reset_key(self):
		self.des_key = '62803B4919AB1CBC'
	
	def reset(self, new_panel_id=None):
		if new_panel_id is not None:
			self.panel_id = new_panel_id
			self.is_server = (new_panel_id == 0xFFFFFFFF)
		self.reset_key()
		self.next_sync = (0, 0)
		self.txqueue = queue.Queue()
		self.last_message_by_me = not self.is_server
		self.waiting_for_sync = not self.is_server

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
	
	def is_synced(self, pkt):
		#TODO: add actual check
		return True
	
	def offset_next_sync(self, a, b):
		self.next_sync = ((self.next_sync[0] + a) & 7, (self.next_sync[1] + b) & 7)
	
	def read(self):
		pkt, _ = super().read()
		if type(pkt) is VivaldiMessage:
			self.last_message_by_me = False
			if self.is_server:
				if self.panel_id == 0xFFFFFFFF:
					self.panel_id = pkt.panel_id
			else:
				if pkt.getcmd() == 4:
					self.des_key = pkt.getarg().rstrip(b'\0').decode('ascii')
			if self.is_server:
				self.offset_next_sync(1, 0)
			else:
				self.offset_next_sync(0, 1)
			sleep(.5)
			self.send_sync()
			self.waiting_for_sync = True
		else:
			if not self.is_server:
				self.next_sync = (self.next_sync[0], pkt.sync[0])

			if self.last_message_by_me:
				sleep(.5)
				#self.send_sync(min(pkt.sync[1] + 1, 2))
				self.send_raw(VivaldiPacket(panel_id=self.panel_id, sync=(self.next_sync[1], (pkt.sync[1]+1)%3)))
				sleep(.5)
				self.send_next()
			self.waiting_for_sync = False

		return pkt, True
	
	def send_sync(self, status=2):
		s = self.next_sync[0 if self.is_server else 1]
		self.send_raw(VivaldiPacket(panel_id=self.panel_id, sync=(s, status)))

	def send_next(self):
		if not self.txqueue.empty():
			msg, enc = self.txqueue.get()
			key = self.des_key if enc else None
			self.last_message_by_me = True
			self.waiting_for_sync = True
			self.send_raw(VivaldiMessage(msg, des_key=key, panel_id=self.panel_id, sync=self.next_sync))

	def send(self, msg, encrypt=True):
		self.txqueue.put((msg, encrypt))
		if not self.waiting_for_sync:
			self.send_next()
