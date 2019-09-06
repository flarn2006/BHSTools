import mido
import sys

notes = set()
curnote = None

mf = mido.MidiFile(sys.argv[1])

timesofar = 0

def freq(n):
	if n is None:
		return 0
	else:
		return int(2**((n-69)/12) * 440)

for msg in mf:
	time = msg.time + timesofar
	timesofar += msg.time

	if msg.type == 'note_off':
		isreallyoff = True
	else:
		isreallyoff = False
		try:
			if msg.velocity == 0:
				isreallyoff = True
		except AttributeError:
			pass
	
	if isreallyoff:
		if msg.note in notes:
			notes.remove(msg.note)
	elif msg.type == 'note_on':
		notes.add(msg.note)

	try:
		highest = max(notes)
	except ValueError:
		highest = None

	if curnote is None or highest != curnote[0]:
		if curnote is not None:
			duration = int(1000*(time - curnote[1]))
			if duration > 0:
				print('dw {:d}, {:d}'.format(freq(curnote[0]), duration))
		curnote = (highest, time)

print('dw 0FFFFh')
print('endjump:')
