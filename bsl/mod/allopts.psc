@ 8FF00
	< 0to255.psc

# Enable all account settings
@ 9F36
	mov r4, #37
@ 9F40
	nop
	nop
@ 9F3C
	mov r11, #&:Tbl_0To255 + 1
	mov r12, #&^Tbl_0To255

# Enable all zone settings
@ AFE6
	mov r4, #22
@ AFF0
	nop
	nop
@ AFEC
	mov r11, #&:Tbl_0To255
	mov r12, #&^Tbl_0To255
@ B00A
	mov r4, #22
@ B012
	nop
	nop
@ B00E
	mov r11, #&:Tbl_0To255
	mov r12, #&^Tbl_0To255

# Enable all panel settings
@ 9CFA
	mov r4, #52
@ 9D04
	nop
	nop
@ 9D00
	mov r11, #&:Tbl_0To255
	mov r12, #&^Tbl_0To255
@ 9D1E
	mov r4, #52
@ 9D26
	nop
	nop
@ 9D22
	mov r11, #&:Tbl_0To255
	mov r12, #&^Tbl_0To255

# Enable all area settings
@ A068
	mov r4, #5
@ A070
	nop
	nop
@ A06C
	mov r11, #&:Tbl_0To255 + 1
	mov r12, #&^Tbl_0To255
@ A08A
	mov r4, #5
@ A092
	nop
	nop
@ A08E
	mov r11, #&:Tbl_0To255 + 1
	mov r12, #&^Tbl_0To255

# Enable all user settings
@ A196
	mov r4, #6
@ A19E
	nop
	nop
@ A19A
	mov r11, #&:Tbl_0To255
	mov r12, #&^Tbl_0To255

# Enable all keypad settings
@ 15E9C
	mov r4, #14
@ 15EA4
	nop
	nop
@ 15EA0
	mov r11, #&:Tbl_0To255
	mov r12, #&^Tbl_0To255
