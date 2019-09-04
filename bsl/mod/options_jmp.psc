	add r4, #table
	jmpi cc_UC, [r4]

table:
	jmps #2, #0DE0Ch ;Bypass
	jmps #2, #0E130h ;Door Chime
	jmps #2, #0E2F2h ;Auxiliary Codes
	jmps #2, #0E75Ah ;Alarm Memory
	jmps #&^Code_OptionsJumpTable, #set_time
	jmps #2, #0EAAAh ;Test
	jmps #2, #0ECE8h ;Area #
	jmps #2, #0EECAh ;Sensors
	jmps #2, #0EEFAh ;Ready
	jmps #2, #0F258h ;(Unused slot, error beep)
	jmps #2, #0F0A6h ;Trouble

set_time:
	< lcd_keypad_time_set.asm
