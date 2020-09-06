- Str_MBMemHdr
	db 'MEMORY ', 0F9h, 'Goto ', 0C4h, 'Ed', 0

- Fmt_MBEditHdr
	db 'EDIT %1%03u %1%05u %1%c', 0

- Fmt_MBMemAsc
	db '%1%03X ............', 0

- Fmt_MBMemRow
	db '%1%03X:%1%04X%1%04X%1%04X', 0

- Fmt_MBExecPrompt
	db 'Call function at'
	db 'address %1%02X%1%04X? ', 0

- moveback2
	sub r14, #100h
	subc r15, #0
	ret
- movefwd2
	add r14, #100h
	addc r15, #0
	ret
- moveback3
	sub r14, #1000h
	subc r15, #0
	ret
- movefwd3
	add r14, #1000h
	addc r15, #0
	ret

- MemoryBrowser_GetSelAddr

	mov r5, r15
	mov r4, r13
	movbz r4, rl4
	shr r4, #1
	add r4, r14
	addc r5, #0
	ret

- MemoryBrowser_Start

	mov [-r0], r15
	mov [-r0], r14
	mov [-r0], r13
	mov r15, #41h
	mov r14, #0e562h
	mov [-r0], r15
	mov [-r0], r14
	mov r14, #0e800h
	mov r13, #0
	mov r4, #0

- MemoryBrowser_MainLoop

	jnb r13.8, hdr_noedit

	calla cc_UC, &:MemoryBrowser_GetSelAddr
	exts r5, #1
	movb rl7, [r4]
	movbz r12, rl7
	bclr r4.0
	exts r5, #1
	mov r7, [r4]
	mov r8, #0FEh
	jb r13.9, edithdr_shift
	mov r8, r13
	shr r8, #1
	add r8, r14
	and r8, #0Fh
	add r8, #30h
	cmp r8, #3Ah
	jmpr cc_C, edithdr_shift
	add r8, #7
	
edithdr_shift:
	mov [-r0], r8
	mov [-r0], r7

	mov r11, #&^Fmt_MBEditHdr
	mov r10, #&:Fmt_MBEditHdr
	mov r9, #40h
	mov r8, #0A91Eh
	calls #0, #3CC6h
	%PPUTSTR &+scratch_mem, #1, #1

	add r0, #4
	jmpr cc_UC, hdr_done

hdr_noedit:
	%PPUTSTR &+Str_MBMemHdr, #1, #1

hdr_done:
	mov r11, #&^Fmt_MBMemAsc
	mov r10, #&:Fmt_MBMemAsc
	mov r9, #40h
	mov r8, #0A91Eh
	mov r12, r15
	shl r12, #4
	mov r4, r14
	shr r4, #12
	or r12, r4
	calls #0, #3CC6h

	mov r6, #12
	mov r5, r15
	mov r4, r14
	mov r8, #0A922h

copy_asc_loop:
	exts r5, #1
	movb rl7, [r4]
	cmpb rl7, #20h
	jmpr cc_C, skip_nonprint
	exts #40h, #1
	movb [r8], rl7
skip_nonprint:
	add r8, #1
	add r4, #1
	addc r5, #0
	sub r6, #1
	jmpr cc_NZ, copy_asc_loop

	%PPUTSTR &+scratch_mem, #1, #2

	mov r6, #6
	mov r5, r15
	mov r4, r14
	add r4, #12
	addc r5, #0
loadstack_loop:
	sub r4, #2
	subc r5, #0
	exts r5, #1
	mov r7, [r4]
	rol r7, #8
	mov [-r0], r7
	sub r6, #1
	jmpr cc_NZ, loadstack_loop
	
	mov r12, r14
	and r12, #0FFFh
	mov r11, #&^Fmt_MBMemRow
	mov r10, #&:Fmt_MBMemRow
	mov r9, #40h
	mov r8, #0A91Eh
	calls #0, #3CC6h

	%PPUTSTR &+scratch_mem, #1, #3

	add r0, #6
	mov r12, r14
	add r12, #6
	and r12, #0FFFh
	mov r11, #&^Fmt_MBMemRow
	mov r10, #&:Fmt_MBMemRow
	mov r9, #40h
	mov r8, #0A91Eh
	calls #0, #3CC6h

	%PPUTSTR &+scratch_mem, #1, #4

	add r0, #6

	jnb r13.8, get_key
	mov r9, #83h
	mov r8, r13
	and r8, #0FFh
	cmp r8, #12
	jmpr cc_C, cursor_first_row
	add r9, #1
	sub r8, #12
cursor_first_row:
	add r8, #5
	calls #3, #4F4h

get_key:
	mov r8, #1
	calls #3, #7DCh

	cmpb rl4, #8Ah
	jmpr cc_Z, moveup
	cmpb rl4, #8Bh
	jmpr cc_Z, movedown
	cmpb rl4, #86h
	jmpr cc_Z, moveback
	cmpb rl4, #88h
	jmpr cc_Z, movefwd
	cmpb rl4, #31h
	calla cc_Z, &:moveback2
	cmpb rl4, #33h
	calla cc_Z, &:movefwd2
	cmpb rl4, #34h
	calla cc_Z, &:moveback3
	cmpb rl4, #36h
	calla cc_Z, &:movefwd3
	cmpb rl4, #89h
	jmpr cc_Z, shift_toggle
	cmpb rl4, #8
	jmpr cc_Z, gotoaddr
	cmpb rl4, #13
	jmpr cc_Z, edit_toggle
	jnb r13.8, not_a_digit_key
	cmpb rl4, #3Ah
	jmpr cc_NC, not_a_digit_key
	cmpb rl4, #30h
	jmpr cc_NC, digit_key_bridge
not_a_digit_key:
	cmpb rl4, #37h
	jmpa cc_Z, exec_prompt
	cmpb rl4, #39h
	jmpa cc_Z, swapaddr
	cmpb rl4, #1Bh
	jmpa cc_NZ, &:MemoryBrowser_MainLoop
	jb r13.8, edit_toggle

	add r0, #4
	mov r13, [r0+]
	mov r14, [r0+]
	mov r15, [r0+]
	rets

edit_toggle:
	bmovn r13.8, r13.8
	and r13, #0FD00h
	jmpa cc_UC, &:MemoryBrowser_MainLoop

moveup:
	jb r13.8, moveup_edit
	sub r14, #6
	subc r15, #0
	jmpa cc_UC, &:MemoryBrowser_MainLoop
moveup_edit:
	mov r5, r15
	mov r4, r13
	movbz r4, rl4
	shr r4, #1
	add r4, r14
	addc r5, #0
	exts r5, #1
	movb rl7, [r4]
	addb rl7, #1
	jb r13.0, moveup_edit_lsn
	addb rl7, #15
moveup_edit_lsn:
	exts r5, #1
	movb [r4], rl7
	jmpa cc_UC, &:MemoryBrowser_MainLoop

movedown:
	jb r13.8, movedown_edit
	add r14, #6
	addc r15, #0
	jmpa cc_UC, &:MemoryBrowser_MainLoop
movedown_edit:
	mov r5, r15
	mov r4, r13
	movbz r4, rl4
	shr r4, #1
	add r4, r14
	addc r5, #0
	exts r5, #1
	movb rl7, [r4]
	subb rl7, #1
	jb r13.0, movedown_edit_lsn
	subb rl7, #15
movedown_edit_lsn:
	exts r5, #1
	movb [r4], rl7
	jmpa cc_UC, &:MemoryBrowser_MainLoop

digit_key_bridge:
	jmpr cc_UC, digit_key
not_a_digit_key_bridge:
	jmpr cc_UC, not_a_digit_key

moveback:
	jb r13.8, moveback_edit
	sub r14, #2h
	subc r15, #0
	jmpa cc_UC, &:MemoryBrowser_MainLoop
moveback_edit:
	mov r4, r13
	subb rl4, #1
	jmpr cc_NC, moveback_edit_norollover
	movb rl4, #23
moveback_edit_norollover:
	mov r13, r4
	jmpa cc_UC, &:MemoryBrowser_MainLoop

movefwd:
	jb r13.8, movefwd_edit
	add r14, #2h
	addc r15, #0
	jmpa cc_UC, &:MemoryBrowser_MainLoop
movefwd_edit:
	mov r4, r13
	addb rl4, #1
	cmpb rl4, #24
	jmpr cc_C, movefwd_edit_nozero
	movb rl4, #0
movefwd_edit_nozero:
	mov r13, r4
	jmpa cc_UC, &:MemoryBrowser_MainLoop

shift_toggle:
	bmovn r13.9, r13.9
	band r13.9, r13.8
	jmpa cc_UC, &:MemoryBrowser_MainLoop

gotoaddr:
	jb r13.8, moveback_edit
	calls &+PromptForAddr
	jb r5.15, cancelgoto
	mov r15, r5
	mov r14, r4
	bclr r14.0
cancelgoto:
	%PPUTSTR &+Str_MBMemHdr, #1, #1
	jmpa cc_UC, &:MemoryBrowser_MainLoop

exec_prompt:
	bclr r13.9
	calla cc_UC, &:MemoryBrowser_GetSelAddr
	bclr r4.0
	mov r12, r5
	mov [-r0], r5
	mov [-r0], r4
	mov r11, #&^Fmt_MBExecPrompt
	mov r10, #&:Fmt_MBExecPrompt
	mov r9, #&^scratch_mem
	mov r8, #&:scratch_mem
	calls #0, #3CC6h
	mov r9, #&^scratch_mem
	mov r8, #&:scratch_mem
	calls &+pgmr_yesno
	mov r8, [r0+]
	mov r9, [r0+]
	jnb r4.0, back_to_main_loop
	push CSP
	callr jmp_r9r8
	calls &+ShowDebugDump
back_to_main_loop:
	jmpa cc_UC, &:MemoryBrowser_MainLoop
jmp_r9r8:
	push r9
	push r8
	rets

swapaddr:
	bclr r13.9
	mov r5, [r0+#2]
	mov r4, [r0]
	mov [r0+#2], r15
	mov [r0], r14
	mov r15, r5
	mov r14, r4
	jmpr cc_UC, back_to_main_loop

digit_key:
	jnb r13.9, nonshifted_digit
	cmp r4, #37h
	jmpr cc_NC, not_a_digit_key_bridge
	add r4, #9
	bclr r13.9
nonshifted_digit:
	and r4, #0Fh
	mov r7, r4
	calla cc_UC, &:MemoryBrowser_GetSelAddr
	jb r13.0, digit_lsn
	shl r7, #4
	exts r5, #1
	movb rh7, [r4]
	andb rh7, #0Fh
	orb rh7, rl7
	exts r5, #1
	movb [r4], rh7
	jmpr cc_UC, movefwd_edit
digit_lsn:
	exts r5, #1
	movb rh7, [r4]
	andb rh7, #0F0h
	orb rh7, rl7
	exts r5, #1
	movb [r4], rh7
	jmpr cc_UC, movefwd_edit
