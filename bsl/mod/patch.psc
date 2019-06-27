# Load header files
	< addrdefs.psc
	< macros.psc

# Skip firmware integrity check (required for mods to work)
@ 5DBDE
	nop
	nop
@ 5DBE8
	nop
	nop
@ 5DBEE
	nop

# Make hidden items selectable
@ 323EE
	db 0Dh
@ 3241A
	nop
@ 32462
	db 0Dh
@ 32490
	nop

# Make hidden parameters visible
@ 3297A
	nop
@ 3299A
	db 0Dh

# Use custom table for diagnostics menu
@ 80000
- Str_DiagItem4
	db '4 Exec Function ', 0
- Str_DiagItem5
	db '5 Write Memory  ', 0
- Str_DiagItem6
	db '6 System Reset  ', 0
- MnuTbl_Diag
	dw 481Fh, 6
	dw 480Eh, 6
	dw 47FDh, 6
	dw &:Str_DiagItem4, &^Str_DiagItem4
	dw &:Str_DiagItem5, &^Str_DiagItem5
	dw &:Str_DiagItem6, &^Str_DiagItem6
	dw 5E61h, 0

@ 383E0
	mov r10, #&:MnuTbl_Diag
	mov r11, #&^MnuTbl_Diag  ; The original instruction here is 4 bytes for some reason, but this one assembles to 2.
	nop                      ; So we need to compensate by putting a NOP here.

# Hook diagnostic menu selection
@ 80100
- Str_EnterSegment
	db 'Enter segment #:', 0
- Str_EnterOffset
	db 'Enter offset:   ', 0
- Str_EnterNewByte
	db 'Enter new byte: ', 0
- Code_DiagMenuHook
	< diaghook.asm

@ 38404
	jmps &+Code_DiagMenuHook
