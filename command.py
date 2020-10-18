#!/usr/bin/python3
import sys
import time
import struct
from intellibus import *

usage_examples = [
	("6 00000000", "Clear a panel ID that was loaded into configuration by the host. This will prevent CH Trouble from occurring."),
	("90 Supers.db 0", "Retrieve and display the configuration record which contains the installer's access code."),
	("308 1 96", "Retrieve and display the record for the master user in the primary account."),
	("1002", "Set the system clock to match that of this computer. ({})".format(time.ctime())),
	("2030 2 m", "Simulate an RF miss warning for the zone associated with input 2 (probably zone 2) even if it is not an RF zone.")
]

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
		return (int(args[0]) + offset).to_bytes(2, 'little') + (int(args[1]) + offset).to_bytes(2, 'little')
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
		dt = time.strptime(' '.join(args), '%Y-%m-%d %H:%M:%S')
	return struct.pack('<BBBBHH', dt.tm_sec, dt.tm_min, dt.tm_hour, dt.tm_mday, dt.tm_mon, dt.tm_year)

@arg_description('Acct# Zone# 0|1')
def arg_zone_bypass(args):
	if args[2] not in ('0', '1'):
		raise ValueError('You must specify either 0 (not bypassed) or 1 (bypassed).')
	return arg_two_words_le('', -1)(args[:2])[:3] + bytes([ord(args[2]) - ord('0')])

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

@arg_description('(Raw C166 byte code in hex)')
def arg_c166_bytes(args):
	raw = arg_hex_raw(args)
	prefix = fromhex(''.join([
		'D4F01400',  # mov r15, [r0+#14h]
		'D4E01200',  # mov r14, [r0+#12h]
		'E6F40401',  # mov r4, #(4+256)
		'E6F555A4',  # mov r5, #42069
		'DC1F',      # exts r15, #2
		'B84E',      # mov [r14], r4
		'C45E0200',  # mov [r14+#2], r5
		'08E4',      # add r14, #4
		'18F0',      # addc r15, #0
	]))
	return prefix + raw + b'\xDB\0' 

def fmt_hexdump(cmd, arg):
	return hexdump(arg)

def fmt_upload(cmd, arg):
	if cmd == 21:
		return 'No more records to download.'
	elif 200 <= cmd <= 299:
		return fmt_hexdump(cmd, arg)
	elif 500 <= cmd <= 599:
		return 'Record not found.'

def fmt_db_entry(cmd, arg):
	if arg == b'\xF9\0':
		return 'Database entry not found.'
	else:
		return fmt_hexdump(cmd, arg)

def fmt_datetime(cmd, arg):
	dt = struct.unpack('<BBBBBBH', arg)
	return '{6}-{4:02}-{3:02} {2:02}:{1:02}:{0:02}'.format(*dt)

cmd20_replies = [21, 200, 201, 202, 203, 204, 206, 207, 208, 209, 210, 211, 212, 213, 215, 217, 218]
command_info = {
	#:		(Name, Response#, ResponseFormatter, ArgParser)
	6:		('Set Host Panel ID', [7], None, arg_hex_le(4, 'ID')),
	16:		('Echo Test', [17], fmt_hexdump, arg_hex_raw),
	20:		('Request Next Config Record', cmd20_replies, fmt_upload, arg_empty),
	22:     ('Restart Upload', [22], None, arg_empty),
	90:		('Request Database Entry', [91], fmt_db_entry, arg_db_entry),
	300:	('Request Panel Config Upload', [200], fmt_upload, arg_hex_raw),
	301:	('Request Communicator Config Upload', [201, 501], fmt_upload, arg_num_le(2, 'Comm#', -1)),
	302:	('Request Account Config Upload', [202, 502], fmt_upload, arg_num_le(2, 'Acct#', -1)),
	303:	('Request Keypad Config Upload', [203, 503], fmt_upload, arg_num_le(2, 'Device#', 0)),
	304:	('Request Alarm Output Config Upload', [204, 504], fmt_upload, arg_num_le(2, 'AlarmOut#', -1)),
	307:	('Request Area Config Upload', [207, 507], fmt_upload, arg_num_le(2, 'Acct#', -1)),
	308:	('Request User Config Upload', [208, 508], fmt_upload, arg_two_words_le('Acct# User#', -1)),
	309:	('Request Zone Config Upload', [209, 509], fmt_upload, arg_two_words_le('Acct# Zone#', -1)),
	311:	('Request Device Config Upload', [211, 511], fmt_upload, arg_num_le(2, 'Device#', 0)),
	313:	('Request Input Config Upload', [213, 513], fmt_upload, arg_num_le(2, 'Input#', -1)),
	317:	('Request COM Port Config Upload', [217, 517], fmt_upload, arg_num_le(2, 'Port#', -1)),
	318:	('Request Script Config Upload', [318, 518], fmt_upload, arg_num_le(2, 'Script#', -1)),
	401:	('Delete Communicator', [601], None, arg_num_le(2, 'Comm#', -1)),
	402:	('Delete Account', [602], None, arg_num_le(2, 'Acct#', -1)),
	403:	('Delete Keypad Config', [603], None, arg_num_le(2, 'Keypad#', -1)),
	404:	('Delete Alarm Output Config', [604], None, arg_num_le(2, 'AlarmOut#', -1)),
	406:	('Delete Output Config', [606], None, arg_num_le(2, 'Output#', -1)),
	407:	('Delete Area', [607], None, arg_num_le(2, 'Acct#', -1)),
	408:	('Delete User', [608], None, arg_two_words_le('Acct# User#', -1)),
	409:	('Delete Zone', [609], None, arg_two_words_le('Acct# Zone#', -1)),
	411:	('Delete Device', [611], None, arg_num_le(2, 'Device#', 0)),
	413:	('Delete Input Config', [613], None, arg_num_le(2, 'Input#', -1)),
	417:	('Delete COM Port Config', [617], None, arg_num_le(2, 'Port#', -1)),
	418:	('Delete Script', [618], None, arg_num_le(2, 'Script#', -1)),
	700:	('Request Panel Status', [800], fmt_hexdump, arg_empty),
	702:	('Request Account Status', [802], fmt_hexdump, arg_num_le(2, 'Acct#', -1)),
	704:	('Request Alarm Output Status', [804], fmt_hexdump, arg_num_le(2, 'AlarmOut#', -1)),
	709:	('Request Zone Status', [809], fmt_hexdump, arg_two_words_le('Acct# Zone#', -1)),
	711:	('Request Device Status', [811], fmt_hexdump, arg_num_le(2, 'Device#', 0)),
	720:	('Request Unknown Status', [820], fmt_hexdump, arg_empty),
	1000:	('Arm System', [1100], None, arg_hex_raw),
	1001:	('Disarm System', [1101], None, arg_hex_raw),
	1002:	('Set Date/Time', [1102], None, arg_date_time),
	1003:	('Get Date/Time', [1103], fmt_datetime, arg_empty),
	1005:	('Set Zone Bypass', [1105], None, arg_zone_bypass),
	2030:	('Set Input Status', [], None, arg_input_status),
	4000:	('Read Analog Inputs', [4001], fmt_hexdump, arg_empty),
	4002:	('Test Panel Outputs', [], None, arg_hex_le(1, 'bitfield')),
	4011:	('Set Defaults (Brinks)', [], None, arg_yes),
	31337:	('Execute Code (requires FW patch)', [42069], fmt_hexdump, arg_c166_bytes)
}

class CommandSender(VirtDevice):
	def __init__(self, ibus, cmd, arg):
		super().__init__(ibus, 5, 3121, fromhex('00 00 FF FF FF FF'), 0, (7,1), 0x7FFE)
		self.cmd = cmd
		self.arg = arg
		self.response_cmds = command_info[cmd][1]
		self.response_out = command_info[cmd][2]
		self.last_tx = 0
		if len(self.response_cmds) == 0:
			self.send_count = 1
	
	def on_ping(self):
		t = time.time()
		if t - self.last_tx >= 0.5:
			self.last_tx = t
			self.send_now(self.cmd, self.arg)
			if len(self.response_cmds) == 0:
				self.send_count -= 1
				if self.send_count == 0:
					bus.stop()
	
	def handle_cmd_nosync(self, cmd, arg, synced):
		if cmd in self.response_cmds:
			if self.response_out is not None:
				print(file=sys.stderr)
				print(self.response_out(cmd, arg))
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
		print('{:.<40}{:.>4} {}'.format(info[0], n, info[3].help_text), file=sys.stderr)
	
	print('\nExamples:\n', file=sys.stderr)
	for (cmd, desc) in usage_examples:
		print('    {:.<36}{:.>4}'.format(cmd, desc), file=sys.stderr)

	exit(255)
except (KeyError, ValueError):
	print("{} is not a recognized command. If it's a valid one, try using testbed.py.".format(sys.argv[2]), file=sys.stderr)
	exit(255)

try:
	arg = arg_func(sys.argv[3:])
except ValueError as ex:
	print('Error parsing arguments: {}'.format(ex), file=sys.stderr)
	exit(255)

bus = Intellibus(port, debug='tx,rx', dbgout=sys.stderr)
dvc = CommandSender(bus, cmd, arg)
bus.run()
