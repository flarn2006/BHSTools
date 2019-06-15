#!/bin/bash

if [ ! -f C166V???.EXE ]; then
	url='https://www.keil.com/demo/eval/c166.htm'
	echo "C166 SDK installer executable (C166V???.EXE) not found."
	echo "Please download this from the Keil website at:"
	echo
	echo "	$url"
	echo
	echo "Place it in the current directory ($PWD) and then run this script again."
	echo
	echo "Sorry it's not a direct download link; they auto-generate them. :/"
	xdg-open "$url" >&/dev/null & disown
	exit 1
fi

set -e
unzip -j C166V???.EXE c166/{asm/REG167.INC,bin/A166.EXE}
chmod +x A166.EXE

if ! which wine >&/dev/null; then
	echo
	echo "A Wine installation was not detected on your computer."
	echo "If you are actually running Windows, this is okay, but if not, you must install Wine before using the assembler."
fi
echo
echo "Done."
