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
	mov r12, [r0+#1Ch]
	mov [-r0], r12
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
