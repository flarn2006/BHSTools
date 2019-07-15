@ 88000

- ShowDebugDump

	mov [-r0], r15
	mov [-r0], r14
	mov [-r0], r13
	mov [-r0], r12
	mov [-r0], r11
	mov [-r0], r10
	mov [-r0], r9
	mov [-r0], r8
	mov [-r0], r7
	mov [-r0], r6
	mov [-r0], r5
	mov [-r0], r4
	mov [-r0], r3
	mov [-r0], r2
	mov [-r0], r1
	mov r13, r0
	add r13, #1Eh
	mov [-r0], r13
	mov r13, #16
	loop:
	mov r12, [r0+]
	mov r11, #6
	mov r10, #7BADh
	mov r9, #40h
	mov r8, #0A937h
	calls #0, #3CC6h
	mov r10, #16
	sub r10, r13
	mov r11, r10
	and r10, #3
	shl r10, #2
	add r10, #1
	shr r11, #2
	add r11, #1
	%PPUTSTR #40h, #0A937h, r10, r11
	sub r13, #1
	jmpr cc_NZ, loop
	mov r8, #60
	%PGETKEY r4
	rets

- Str_EnterAddress
	db 'Address (in hex)'
	db 'Enter 6 digits: ', 0
- PromptForAddr
	mov r4, #30h
	mov r11, #&^scratch_mem
	mov r10, #&:scratch_mem
	exts r11, #1
	mov [r10], r4
	addr_getstr:
	%PGETSTR &+Str_EnterAddress, r11, r10, #6
	cmp r4, #1Bh
	jmpr cc_NZ, addr_prompt_not_canceled
	bset r5.15
	rets
	addr_prompt_not_canceled:
	mov r9, r11
	mov r8, r10
	mov r12, r8
	calls #5, #0E4F6h  ;strlen(r9:r8) -> r4 - also leaves r8 pointing to byte after 0 terminator
	cmp r4, #6
	jmpr cc_NZ, addr_getstr
	mov r10, r8
	mov r8, r12
	mov [-r0], r11
	mov [-r0], r10
	calls &+fromhex
	mov r4, [r0+]
	mov r11, [r0+]
	exts r11, #2
	movb rl5, [r4+]
	mov r4, [r4]
	rol r4, #8
	movbz r5, rl5
	rets

< membrowser.psc
