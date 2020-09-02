#!/usr/bin/python3
import sys
import time
import struct
from intellibus import *

def arg_description(text):
	def wrapper(func):
		func.help_text = text
		return func
	return wrapper

@arg_description('')
def arg_empty(args):
	return b''

@arg_description('[byte(s)]')
def arg_hex_raw(args):
	return b''.join([fromhex(a) for a in args])

def arg_hex_le(size, description):
	@arg_description(description)
	def func(args):
		raw = arg_hex_raw(args)
		if len(raw) > size:
			raise ValueError('Argument too long; must fit within {} bytes.'.format(size))
		return raw[::-1].ljust(size, b'\0')
	return func

def arg_num_le(size, description, offset=0):
	@arg_description(description)
	def func(args):
		return (int(args[0]) + offset).to_bytes(size, 'little')
	return func

def arg_two_words_le(description, offset=0):
	@arg_description(description)
	def func(args):
		return (int(args[0]) + offset).to_bytes(size, 'little') + (int(args[1]) + offset).to_bytes(size, 'little')
	return func

@arg_description('db_filename record#')
def arg_db_entry(args):
	if len(args[0]) > 16:
		raise ValueError('Database filename must be 16 bytes or less.')
	return args[0].encode('ascii').ljust(16, b'\0') + int(args[1]).to_bytes(2, 'little')

@arg_description('[YYYY-MM-DD hh:mm:ss]')
def arg_date_time(args):
	if len(args) == 0:
		dt = time.localtime(time.time())
	else:
		dt = strptime(' '.join(args), '%Y-%m-%d %H:%M:%S')
	return struct.pack('<BBBBHH', dt.tm_sec, dt.tm_min, dt.tm_hour, dt.tm_mday, dt.tm_mon, dt.tm_year)

@arg_description('Acct# Zone# 0|1')
def arg_zone_bypass(args):
	if args[3] not in ('0', '1'):
		raise ValueError('You must specify either 0 (not bypassed) or 1 (bypassed).')
	return arg_two_words_le('', -1)(args[:2])[:3] + (ord(args[3]) - ord('0'))

@arg_description('Input# [fjlmst]  (F)ault (J)am (L)owBatt (M)iss (S)upervisory (T)amper')
def arg_input_status(args):
	inputnum = int(args[0]) - 1
	status = 0
	for ch in ''.join(args[1:]).lower():
		if ch == 'f':	status |= 0b0000000000000001
		elif ch == 'j':	status |= 0b0001000000000000
		elif ch == 'l': status |= 0b0000000100000000
		elif ch == 'm': status |= 0b0000000010000000
		elif ch == 's': status |= 0b0000000000000010
		elif ch == 't': status |= 0b0000000000001000
		else:
			raise ValueError("Unknown status character '{}' given.".format(ch))
	return struct.pack('<HH', inputnum, status)

@arg_description('"Yes"')
def arg_yes(args):
	if len(args) == 1 and args[1] == 'Yes':
		return b'Yes'
	else:
		raise ValueError('To confirm resetting all programming to defaults, you must type a literal "Yes" as the only argument to this command. It is case-sensitive, but quotes are not necessary.')

cmd20_replies = [21, 200, 201, 202, 203, 204, 206, 207, 208, 209, 210, 211, 212, 213, 215, 217, 218]
command_info = {
	#:		(Name, Response#, Output?, ArgParser)
	6:		('Set Host Panel ID', [7], False, arg_hex_le(4, 'ID')),
	16:		('Echo Test', [17], True, arg_hex_raw),
	20:		('Request Next Config Record', cmd20_replies, True, arg_empty),
	22:     ('Restart Upload', [22], False, arg_empty),
	90:		('Request Database Entry', [91], True, arg_db_entry),
	300:	('Request Panel Config Upload', [200], True, arg_hex_raw),
	301:	('Request Communicator Config Upload', [201, 501], True, arg_num_le(2, 'Comm#', -1)),
	302:	('Request Account Config Upload', [202, 502], True, arg_num_le(2, 'Acct#', -1)),
	303:	('Request Keypad Config Upload', [203, 503], True, arg_num_le(2, 'Keypad#', -1)),
	304:	('Request Alarm Output Config Upload', [204, 504], True, arg_num_le(2, 'AlarmOut#', -1)),
	307:	('Request Area Config Upload', [207, 507], True, arg_num_le(2, 'Acct#', -1)),
	308:	('Request User Config Upload', [208, 508], True, arg_two_words_le('Acct# User#', -1)),
	309:	('Request Zone Config Upload', [209, 509], True, arg_two_words_le('Acct# Zone#', -1)),
	311:	('Request Device Config Upload', [211, 511], True, arg_num_le(2, 'Device#', -1)),
	313:	('Request Input Config Upload', [213, 513], True, arg_num_le(2, 'Input#', -1)),
	317:	('Request COM Port Config Upload', [217, 517], True, arg_num_le(2, 'Port#', -1)),
	318:	('Request Script Config Upload', [318, 518], True, arg_num_le(2, 'Script#', -1)),
	401:	('Delete Communicator', [601], False, arg_num_le('Comm#', -1)),
	402:	('Delete Account', [602], False, arg_num_le('Acct#', -1)),
	403:	('Delete Keypad Config', [603], False, arg_num_le(2, 'Keypad#', -1)),
	404:	('Delete Alarm Output Config', [604], False, arg_num_le(2, 'AlarmOut#', -1)),
	406:	('Delete Output Config', [606], False, arg_num_le(2, 'Output#', -1)),
	407:	('Delete Area', [607], False, arg_num_le(2, 'Acct#', -1)),
	408:	('Delete User', [608], False, arg_two_words_le('Acct# User#', -1)),
	409:	('Delete Zone', [609], False, arg_two_words_le('Acct# Zone#', -1)),
	411:	('Delete Device', [611], False, arg_num_le(2, 'Device#', -1)),
	413:	('Delete Input Config', [613], False, arg_num_le(2, 'Input#', -1)),
	417:	('Delete COM Port Config', [617], False, arg_num_le(2, 'Port#', -1)),
	418:	('Delete Script', [618], False, arg_num_le(2, 'Script#', -1)),
	700:	('Request Panel Status', [800], False, arg_empty),
	702:	('Request Account Status', [802], False, arg_num_le(2, 'Acct#', -1)),
	704:	('Request Alarm Output Status', [804], False, arg_num_le(2, 'AlarmOut#', -1)),
	709:	('Request Zone Status', [809], False, arg_two_words_le('Acct# Zone#', -1)),
	711:	('Request Device Status', [811], False, arg_num_le(2, 'Device#', 1)),
	720:	('Request Unknown Status', [820], False, arg_empty),
	1000:	('Arm System', [1100], False, arg_hex_raw),
	1001:	('Disarm System', [1101], False, arg_hex_raw),
	1002:	('Set Date/Time', [1102], False, arg_date_time),
	1003:	('Get Date/Time', [1103], True, arg_empty),
	1005:	('Set Zone Bypass', [1105], False, arg_zone_bypass),
	2030:	('Set Input Status', [], False, arg_input_status),
	4000:	('Read Analog Inputs', [4001], True, arg_empty),
	4002:	('Test Panel Outputs', [], False, arg_hex_le(1, 'bitfield')),
	4011:	('Set Defaults (Brinks)', [], False, arg_yes)
}

class CommandSender(VirtDevice):
	def __init__(self, ibus, cmd, arg):
		super().__init__(ibus, 5, 3121, fromhex('00 00 FF FF FF FF'), 0, (7,1), 0x7FF7)
		self.cmd = cmd
		self.arg = arg
		self.response_cmds = command_info[cmd][1]
		self.response_out = command_info[cmd][2]
		self.last_tx = 0
		if len(self.response_cmds) == 0:
			self.send_count = 4
	
	def on_ping(self):
		t = time.time()
		if t - self.last_tx >= 0.5:
			self.last_tx = t
			self.send_now(self.cmd, self.arg)
			if len(self.response_cmds) == 0:
				self.send_count -= 1
				if self.send_count == 0:
					bus.stop()
	
	def handle_cmd(self, cmd, arg):
		if cmd in self.response_cmds:
			if self.response_out:
				print()
				print(hexdump(arg))
			bus.stop()

try:
	port = sys.argv[1]
	cmd = int(sys.argv[2])
	arg_func = command_info[cmd][3]
except IndexError:
	print('Usage: {} port command# [arguments]'.format(sys.argv[0]), file=sys.stderr)
	print('\nRecognized commands are:', file=sys.stderr)
	nums = list(command_info)
	nums.sort()
	for n in nums:
		info = command_info[n]
		print('{:.<40}{:.>4} {}'.format(info[0], n, info[3].help_text))
	exit(255)
except (KeyError, ValueError):
	print("{} is not a recognized command. If it's a valid one, try using testbed.py.".format(sys.argv[2]), file=sys.stderr)
	exit(255)

try:
	arg = arg_func(sys.argv[3:])
except ValueError as ex:
	print('Error parsing arguments: {}'.format(ex), sys.stderr)
	exit(255)

bus = Intellibus(port, debug='tx,rx', dbgout=sys.stderr)
dvc = CommandSender(bus, cmd, arg)
bus.run()
