import struct
from crcmod.predefined import PredefinedCrc
from serial import Serial
from sys import stdout
from queue import Queue

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


class SyncPing(Packet):
	def __init__(self, addr, flag, counter):
		self.addr = addr
		self.flag = flag
		self.counter = counter
	
	def __repr__(self):
		return '<({}*) PING->{:04X}: {:02X}>'.format('1' if self.flag else '0', self.addr, self.counter)
	
	def gen_data(self):
		return struct.pack('<HB', self.addr | (0x8000 if self.flag else 0), self.counter)

class SyncReply(Packet):
	def __init__(self, addr, flag=False):
		self.addr = addr
		self.flag = flag
	
	def __repr__(self):
		return '<(*{}) {:04X}->PONG>'.format('1' if self.flag else '0', self.addr)
	
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
	
	def __repr__(self):
		return '<({:02b}) {:04X}->{:04X}:{:5} [ {} ] >'.format(self.flags, self.src, self.dest, self.getcmd(), tohex(self.getarg()))
	
	def gen_data(self):
		dest_field = (self.dest | 0x8000) if (self.flags & 1) else self.dest
		src_field = (self.src | 0x8000) if (self.flags & 2) else self.src
		return struct.pack('<HHBH', dest_field, src_field, self.n, len(self.payload)+2) + self.payload
	
	def getcmd(self):
		return struct.unpack('<H', self.payload[:2])[0]
	
	def getarg(self):
		return self.payload[2:]

class BasicInterface:
	def get_byte(self):
		raise NotImplementedError(type(self).__name__ + ' does not implement get_byte')
	
	def send_bytes(self, data):
		raise NotImplementedError(type(self).__name__ + ' does not implement send_bytes')

	def read(self):
		while True:
			while self.get_byte() != b'\x1e': pass
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
			return Packet(data)
			#else:
			#	print('crc fail: ' + tohex(data + check))
	
	def write(self, packet):
		self.send_bytes(b'\x1e' + bytes(packet).replace(b'\x7d', b'\x7d\x5d').replace(b'\x1e', b'\x7d\x3e'))

class Interface(BasicInterface):
	def __init__(self, port, baudrate=38400):
		self.serial = Serial(port=port, baudrate=baudrate)
	
	def get_byte(self):
		return self.serial.read()
	
	def send_bytes(self, data):
		return self.serial.write(data)

class SyncState:
	def __init__(self, myaddr, master=False, slave=False):
		self.flags = 0
		self.myaddr = myaddr
		if master:
			self.flags |= 2
		if slave:
			self.flags |= 1
	
	def check(self, pkt):
		if type(pkt) is Message:
			if pkt.src == self.myaddr:
				return self.flags ^ pkt.flags == 1
			elif pkt.dest == self.myaddr:
				return self.flags ^ pkt.flags == 2
		else:
			return True
	
	def receive(self, pkt):
		if type(pkt) is SyncPing:
			if pkt.addr == self.myaddr:
				if pkt.flag:
					self.flags |= 1
				else:
					self.flags &= 2
			return True
		elif type(pkt) is SyncReply:
			if pkt.addr == self.myaddr:
				if pkt.flag:
					self.flags |= 2
				else:
					self.flags &= 1
			return True
		elif type(pkt) is Message:
			accept = self.check(pkt)
			if accept:
				self.flags = pkt.flags
			return accept
	
	def next(self, as_master):
		self.flags ^= (2 if as_master else 1)
		return self.flags
	
	def reply(self):
		return SyncReply(self.myaddr, self.flags & 2)

class Connection:
	def __init__(self, iface, debug=None, dbgout=stdout):
		self.dbgout = dbgout
		if debug is not None:
			if type(debug) is dict:
				self.debug = debug
			elif type(debug) is tuple or type(debug) is list:
				self.debug = dict([(k,None) for k in debug])
			elif type(debug) is str:
				self.debug = {}
				for item in debug.split(','):
					kv = item.split('=')
					if len(kv) > 1:
						self.debug[kv[0]] = kv[1]
					else:
						self.debug[kv[0]] = None
			else:
				raise TypeError('debug must be a dict, tuple/list, or a string in the format "key[=value],key2[=value2],..."')
		else:
			self.debug = {}
	
	def should_output_debug(self, pkt, outgoing):
		ptype = self.packet_type(pkt)
		if ptype == 'msg':
			if outgoing:
				return 'tx' in self.debug
			else:
				return 'rx' in self.debug
		elif ptype == 'sync':
			return 'sync' in self.debug
		else:
			return False
	
	def packet_type(self, pkt) -> ('msg', 'sync', None):
		return None
	
	def output_debug(self, pkt, outgoing):
		if self.should_output_debug(pkt, outgoing):
			print('{}: {}'.format('TX' if outgoing else 'RX', pkt), file=self.dbgout)
			self.dbgout.flush()
	
	def is_synced(self, pkt):
		return True
	
	def decode_packet(self, pkt):
		return pkt
	
	def read(self):
		pkt = self.decode_packet(self.bus.read())
		self.output_debug(pkt, False)
		return pkt, self.is_synced(pkt)

	def send_raw(self, pkt):
		self.output_debug(pkt, True)
		self.bus.write(pkt)

	def run(self):
		self.stop_flag = False
		while not self.stop_flag:
			pkt, synced = self.read()
			for l in self.listeners:
				try:
					l.receive(pkt, synced)
				except Exception as ex:
					print('{} threw {}'.format(l, ex))
	
	def stop(self):
		self.stop_flag = True


class Intellibus(Connection):
	def __init__(self, iface, **kwargs):
		super().__init__(iface, **kwargs)
		self.counter = 1
		self.syncs = {}
		if type(iface) is str:
			self.bus = Interface(iface)
		else:
			self.bus = iface
		self.listeners = []
	
	def sync(self, addr):
		if addr not in self.syncs:
			self.syncs[addr] = SyncState(addr)
		return self.syncs[addr]

	def should_output_debug(self, pkt, outgoing):
		if not super().should_output_debug(pkt, outgoing):
			return False
		elif outgoing:
			return True
		else:
			return self.debug['rx'] is None or int(self.debug['rx']) in (pkt.src, pkt.dest)
	
	def send(self, dest, src, msg, **kwargs):
		if type(msg) is Message:
			msg = msg.payload
		if 'flags' in kwargs:
			flags = kwargs['flags']
		else:
			flags = self.sync(dest if src == 0 else src).next(src == 0)
		pkt = Message(dest, src, msg, flags)
		for _ in range(kwargs['count'] if 'count' in kwargs else 6):
			self.send_raw(pkt)

	def decode_packet(self, pkt):
		data = bytes(pkt)[:-2]
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
				return pkt
		else:
			return pkt
	
	def packet_type(self, pkt):
		if type(pkt) is Message:
			return 'msg'
		elif type(pkt) in (SyncPing, SyncReply):
			return 'sync'
		else:
			return None
	
	def is_synced(self, pkt):
		if type(pkt) is Message:
			if pkt.dest == 0x7FFF:
				return True
			elif pkt.dest == 0:
				return self.sync(pkt.src).check(pkt)
			elif 0x7001 <= pkt.dest <= 0x707F:
				return pkt.dest & 0xFF == self.counter
			else:
				return self.sync(pkt.dest).check(pkt)
		else:
			return True
	
	def read(self):
		pkt, _ = super().read()
		self.output_debug(pkt, False)
		isSynced = True
		if type(pkt) is SyncPing:
			self.sync(pkt.addr).receive(pkt)
			self.counter = pkt.counter % 0x7F + 1
		elif type(pkt) is SyncReply:
			self.sync(pkt.addr).receive(pkt)
		elif type(pkt) is Message:
			if 0x7001 <= pkt.dest <= 0x707F:
				if pkt.dest & 0xFF == self.counter:
					self.counter = self.counter % 0x7F + 1
				else:
					isSynced = False
			elif pkt.dest == 0:
				isSynced = self.sync(pkt.src).receive(pkt)
			elif pkt.dest != 0x7FFF:
				isSynced = self.sync(pkt.dest).receive(pkt)

		return pkt, isSynced

	def broadcast(self, msg, **kwargs):
		if type(msg) is Message:
			msg = msg.payload
		pkt = Message(0x7000+self.counter, 0, msg, 0)
		self.counter = self.counter % 0x7F + 1
		for _ in range(kwargs['count'] if 'count' in kwargs else 1):
			self.send_raw(pkt)
	
	def add_listener(self, listener):
		self.listeners.append(listener)
	
	def sync_reply(self, addr):
		self.send_raw(self.sync(addr).reply())

class Listener:
	def __init__(self, callback, ibus:Intellibus=None):
		self.callback = callback
		if ibus is not None:
			ibus.add_listener(self)
	
	def __call__(self, *args):
		self.callback(*args)
	
	def receive(self, pkt, synced):
		self.callback(pkt, synced)

def add_listener(ibus:Intellibus) -> Listener:
	def wrapper(f):
		return Listener(f, ibus)
	return wrapper

class VirtDevice:
	def __init__(self, ibus:Intellibus, kind:int, model:int, serial_no:bytes, hdw_conf:int=0, fw_ver:(int,int)=0, addr:int=None):
		self.addr = addr
		self.ibus = ibus
		self.kind = kind
		self.model = model
		self.serial_no = serial_no.rjust(6, b'\0')
		self.hdw_conf = hdw_conf
		self.fw_ver = bytes(fw_ver)
		self.outqueue = Queue()
		self.active = True
		ibus.add_listener(self)
	
	def receive(self, pkt, synced):
		if self.active:
			if type(pkt) is SyncPing:
				if pkt.addr == self.addr:
					self.ibus.sync_reply(pkt.addr)
					self.on_ping()
			elif type(pkt) is Message:
				cmd = pkt.getcmd()
				arg = pkt.getarg()
				if (cmd == 0xBB8 and self.addr == pkt.dest) or (cmd == 0xBBC and self.addr is None):
					self.ibus.send(0, self.addr or 0, (0xBB9, self.serial_no + struct.pack('<HHHH', 0x100, self.model, self.kind, self.hdw_conf) + self.fw_ver), count=3)
				elif cmd == 0xBBA:
					if arg[:6] == self.serial_no:
						self.addr = struct.unpack('<H', arg[-2:])[0]
						self.send_now(0xBBB, arg, count=3)
				elif pkt.dest == self.addr or 0x7000 <= pkt.dest <= 0x70FF:
					if cmd == 0xBBF:
						self.send(0xBC0, b'')
					elif synced:
						self.handle_cmd(cmd, arg)
	
	def send_now(self, cmd, arg=b'', **kwargs):
		self.ibus.send(0, self.addr, (cmd, arg), **kwargs)
	
	def send(self, cmd, arg=b'', **kwargs):
		self.outqueue.put((cmd, arg, kwargs))

	def handle_cmd(self, cmd, arg):
		pass
	
	def on_ping(self):
		while not self.outqueue.empty():
			cmd, arg, kwargs = self.outqueue.get()
			self.send_now(cmd, arg, **kwargs)

def tohex(data):
	return ' '.join(['{:02X}'.format(b) for b in data])

def fromhex(text):
	text = text.replace(' ', '')
	if len(text) % 2 == 0:
		split = [text[i:i+2] for i in range(0, len(text), 2)]
		return bytes([int(h, 16) for h in split])
	else:
		raise ValueError('An even number of hex digits must be given.')
