The files in this directory will assist you in making your alarm system
play music through its siren.

Why would you need to do this? Well...you wouldn't, really. I can't
think of any practical use this would have. But I made it as a fun lit-
tle exercise, just because I could. And so I could make a video for You-
Tube. (https://www.youtube.com/watch?v=5Lzl2odc-ck)

So here's the code I used, in case anyone wants to play around with it!

Make a copy of music.asm, and run midiconv.py with a MIDI file as an ar-
gument, redirecting its output to your copy of music.asm in append mode.
Then, upload it to the panel using dynload.py.

For example:

	cp music/music.asm mario_song.asm
	music/midiconv.py mario.mid >> mario_song.asm
	./dynload.py /dev/ttyUSB0 mario_song.asm

Or, on Windows:

	copy music\music.asm mario_song.asm
	music\midiconv.py mario.mid >> mario_song.asm
	dynload.py com3 mario_song.asm

(Note: dynload.py relies on a third-party assembler executable that is
       only designed for Windows, but ironically, I have not actually
	   tested it on Windows, only Linux via Wine. Since this is what
	   my script is designed for, I cannot say for sure that it will
	   work on Windows.)

Have fun! :)
