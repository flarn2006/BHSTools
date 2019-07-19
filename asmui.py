#!/usr/bin/python3

import tkinter as tk
from tkinter import N,E,W,S
import bsl
import intellibus as ib
from threading import Thread
import os
import struct

bus = ib.Intellibus('/dev/ttyUSB2', debug='tx,rx')
thr = Thread(target=bus.run)
thr.start()
os.chdir('bsl')

class ReplyListener:
	def __init__(self, data_callback, opcode=0):
		self.data_callback = data_callback
		self.opcode = opcode
	
	def receive(self, pkt, synced):
		if type(pkt) is ib.Message and pkt.getcmd() == self.opcode:
			self.data_callback(pkt.getarg())

top = tk.Tk()
top.title('ASM Execution')

pw = tk.PanedWindow(orient=tk.VERTICAL)

tbCode = tk.Text()
tbOutput = tk.Text()

head = tk.Frame(relief=tk.SUNKEN, borderwidth=1)
tk.Label(head, text='Reply opcode: ').pack(side=tk.LEFT)
numReply = tk.Entry(head, width=5)
numReply.insert(tk.END, '1337')
numReply.pack(side=tk.LEFT)
tk.Label(head, text=' Body: r15:r14 → ').pack(side=tk.LEFT)
numSize = tk.Entry(head, width=3)
numSize.insert(tk.END, '64')
numSize.pack(side=tk.LEFT)
tk.Label(head, text=' byte(s)').pack(side=tk.LEFT)

def on_rx(data):
	global tbOutput
	tbOutput.set(ib.hexdump(data))

reply_listener = ReplyListener(on_rx)
bus.add_listener(reply_listener)

def process_code(code, opcode, datasize):
	prefix = ib.fromhex(''.join([
		'D4F01400',                                        # mov r15, [r0+#14h]
		'D4E01200',                                        # mov r14, [r0+#12h]
		'E6F4'+ib.tohex(struct.pack('<H', datasize + 4)),  # mov r4, #(size+4)
		'E6F5'+ib.tohex(struct.pack('<H', opcode)),        # mov r5, #(opcode)
		'DC1F',                                            # exts r15, #2
		'B84E',                                            # mov [r14], r4
		'C45E0200',                                        # mov [r14+#2], r5
		'08E4',                                            # add r14, #4
		'18F0'                                             # addc r15, #0
	]))
	suffix = b'\xDB\0'  # rets
	return prefix + bsl.assemble(code) + suffix

def btnExec_click():
	global reply_listener
	code = tbCode.get('1.0', 'end')
	datasize = int(numSize.get())
	reply_listener.opcode = int(numReply.get())
	code = process_code(code, reply_listener.opcode, datasize)
	bus.send(0, 0x7FFE, (31337, code))

def btnReset_click():
	bus.send(0, 0x7FFE, (32, b''))

btnExec = tk.Button(text='Execute', command=btnExec_click)
btnReset = tk.Button(text='Reset', command=btnReset_click)

head.grid(row=0, column=0, columnspan=2, sticky=W+E)
pw.add(tbCode)
pw.add(tbOutput)
pw.grid(row=1, column=0, columnspan=2, sticky=N+E+W+S)
btnReset.grid(row=2, column=0, sticky=W+E)
btnExec.grid(row=2, column=1, sticky=W+E)

top.grid_rowconfigure(1, weight=1)
top.grid_columnconfigure(0, weight=1)
top.grid_columnconfigure(1, weight=2)

try:
	top.mainloop()
except KeyboardInterrupt:
	pass
finally:
	bus.stop()
	thr.join()
