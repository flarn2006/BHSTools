#!/usr/bin/python3

from serial import Serial
import bsl
import sys

if len(sys.argv) < 2:
	print('Usage: {} port'.format(sys.argv[0]), file=sys.stderr)
	sys.exit(255)

with Serial(sys.argv[1], 9600) as s:
	bsl.init(s)
	bsl.boot(s)
