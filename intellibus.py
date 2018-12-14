import struct
from crcmod.predefined import PredefinedCrc
from serial import Serial
from random import randint

class Packet:
	def __init__(self, data):
		self.data = data
	
	def gen_data(self):
		return self.data
	
	def __bytes__(self):
		data = self.gen_data()
		crc = PredefinedCrc('crc-16-mcrf4xx')
		crc.update(data)
		digest = crc.digest()
		return data + bytes([digest[1], digest[0]])
	
	def __repr__(self):
		return '<{}: {}>'.format(type(self).__name__, tohex(self.gen_data()))

	def decode(self):
		data = self.gen_data()
		if len(data) == 2:
			(addr,) = struct.unpack('<H', data)
			return SyncReply(addr & 0x7FFF, 1 if addr & 0x8000 else 0)
		elif len(data) == 3:
			addr, n = struct.unpack('<HB', data)
			return SyncPing(addr & 0x7FFF, 1 if addr & 0x8000 else 0, n)
		elif len(data) >= 7:
			dest, src, n, size = struct.unpack('<HHBH', data[:7])
			if size + 5 == len(data):
				flags = 0
				if dest & 0x8000:
					dest &= 0x7FFF
					flags |= 1
				if src & 0x8000:
					src &= 0x7FFF
					flags |= 2
				return Message(dest, src, data[7:], flags, n)
			else:
				return self
		else:
			return self

class SyncPing(Packet):
	def __init__(self, addr, flag=False, n=None):
		self.addr = addr
		self.flag = flag
		if n is None:
			self.n = randint(0,255)
		else:
			self.n = n
	
	def gen_data(self):
		return struct.pack('<HB', self.addr | (0x8000 if self.flag else 0), self.n)

class SyncReply(Packet):
	def __init__(self, addr, flag=False):
		self.addr = addr
		self.flag = flag
	
	def gen_data(self):
		return struct.pack('<H', self.addr | (0x8000 if self.flag else 0))

class Message(Packet):
	def __init__(self, dest, src, payload, flags=0, n=4):
		self.dest = dest
		self.src = src
		if type(payload) is tuple:
			cmd, data = payload
			self.payload = struct.pack('<H', cmd) + data
		else:
			self.payload = payload
		self.flags = flags
		self.n = n
	
	def gen_data(self):
		dest_field = (self.dest | 0x8000) if (self.flags & 1) else self.dest
		src_field = (self.src | 0x8000) if (self.flags & 2) else self.src
		return struct.pack('<HHBH', dest_field, src_field, self.n, len(self.payload)+2) + self.payload
	
	def getcmd(self):
		return struct.unpack('<H', self.payload[:2])[0]
	
	def getarg(self):
		return self.payload[2:]

class Interface:
	def __init__(self, port, **kwargs):
		if 'baudrate' in kwargs:
			baudrate = kwargs['baudrate']
		else:
			baudrate = 38400

		self.serial = Serial(port=port, baudrate=baudrate)
	
	def read(self):
		while True:
			while self.serial.read() != b'\x1e': pass
			data = b''
			found_non_1e = False
			while True:
				b = self.serial.read()
				if b == b'\x1e':
					if found_non_1e:
						break
				else:
					found_non_1e = True
					data += b
			
			data = data.replace(b'\x7d\x3e', b'\x1e').replace(b'\x7d\x5d', b'\x7d')
			check = data[-2:]
			data = data[:-2]

			#crc = PredefinedCrc('crc-16-mcrf4xx')
			#crc.update(data)
			#digest = crc.digest()
			
			#if check[0] == digest[1] and check[1] == digest[0]:
			return Packet(data).decode()
			#else:
			#	print('crc fail: ' + tohex(data + check))
	
	def write(self, packet):
		self.serial.write(b'\x1e' + bytes(packet).replace(b'\x7d', b'\x7d\x5d').replace(b'\x1e', b'\x7d\x3e'))

class SyncState:
	def __init__(self, myaddr, master=False, slave=False):
		self.flags = 0
		self.myaddr = myaddr
		self.counter = 0
		if master:
			self.flags |= 2
		if slave:
			self.flags |= 1
	
	def receive(self, pkt):
		if type(pkt) is SyncPing:
			if pkt.addr == self.myaddr:
				if pkt.flag:
					if not self.flags & 1:
						print('setting flag by ping')
					self.flags |= 1
				else:
					if self.flags & 1:
						print('clearing flag by ping')
					self.flags &= 2
				self.counter = pkt.n
			return True
		elif type(pkt) is SyncReply:
			if pkt.addr == self.myaddr:
				if pkt.flag:
					self.flags |= 2
				else:
					self.flags &= 1
			return True
		elif type(pkt) is Message:
			accept = True
			if pkt.src == self.myaddr:
				accept = (self.flags ^ pkt.flags == 1)
			elif pkt.dest == self.myaddr:
				accept = (self.flags ^ pkt.flags == 2)
			if accept:
				self.flags = pkt.flags
			return accept
	
	def next(self, as_master):
		self.flags ^= (2 if as_master else 1)
		return self.flags
	
	def ping(self):
		self.counter += 1
		self.counter &= 0x7F
		return SyncPing(self.myaddr, self.flags & 1, self.counter)
	
	def reply(self):
		return SyncReply(self.myaddr, self.flags & 2)

class DummySyncState(SyncState):
	def __init__(self):
		super().__init__(0x7FFF)

	def receive(self, pkt):
		return True
	
	def next(self, as_master):
		return 0

class VirtDevice:
	def __init__(self, kind, model, serial_no, hdw_conf=0, fw_ver=0):
		self.addr = None
		self.sync = DummySyncState()
		self.kind = kind
		self.model = model
		self.serial_no = serial_no
		self.xmitters = []
		self.hdw_conf = hdw_conf
		self.fw_ver = fw_ver
	
	def send(self, msg, **kwargs):
		if type(msg) is Message:
			msg = msg.payload
		if 'flags' in kwargs:
			flags = kwargs['flags']
		else:
			flags = self.sync.next(False)
		pkt = Message(0, self.addr or 0, msg, flags)
		for _ in range(kwargs['count'] if 'count' in kwargs else 6):
			for x in self.xmitters:
				x(pkt)
	
	def receive(self, pkt):
		if self.sync.receive(pkt):
			if type(pkt) is SyncPing:
				if pkt.addr == self.addr:
					for x in self.xmitters:
						x(self.sync.reply())
			elif type(pkt) is Message:
				cmd = pkt.getcmd()
				arg = pkt.getarg()
				if cmd == 0xBBC:
					self.send((0xBB9, self.serial_no + struct.pack('<HHHHH', 0x100, self.model, self.kind, self.hdw_conf, self.fw_ver)))
				elif cmd == 0xBBA:
					self.send((0xBBB, arg))
					self.addr = struct.unpack('<H', arg[-2:])[0]
					self.sync = SyncState(self.addr)
				elif pkt.dest == self.addr:
					self.handle_cmd(cmd, arg)

	def handle_cmd(cmd, arg):
		pass

def tohex(data):
	return ' '.join(['{:02X}'.format(b) for b in data])

def fromhex(text):
	text = text.replace(' ', '')
	if len(text) % 2 == 0:
		split = [text[i:i+2] for i in range(0, len(text), 2)]
		return bytes([int(h, 16) for h in split])
	else:
		raise ValueError('An even number of hex digits must be given.')
