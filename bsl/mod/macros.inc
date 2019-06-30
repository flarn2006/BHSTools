%*DEFINE (CONMOV reg, value) (
	%IF (%NES (%reg, %value)) THEN (
		mov %reg, %value
	) FI
)

%*DEFINE (PUSHVIA reg, value) (
	%CONMOV %reg, %value
	mov [-r0], %reg
)

%*DEFINE (PGETSTR pseg, pofs, bseg, bofs, maxlen) (
	mov [-r0], r12
	mov [-r0], r11
	mov [-r0], r10
	mov [-r0], r9
	mov [-r0], r8
	
	%CONMOV r12, %maxlen
	%CONMOV r11, %bseg
	%CONMOV r10, %bofs
	%CONMOV r9, %pseg
	%CONMOV r8, %pofs

	calls &+pgmr_getstr

	mov r8, [r0+]
	mov r9, [r0+]
	mov r10, [r0+]
	mov r11, [r0+]
	mov r12, [r0+]
)

%*DEFINE (PPUTSTR sseg, sofs, x, y) (
	mov [-r0], r11
	mov [-r0], r10
	mov [-r0], r9
	mov [-r0], r8

	%CONMOV r11, %y
	%CONMOV r10, %x
	%CONMOV r9, %sseg
	%CONMOV r8, %sofs
	
	calls &+pgmr_putstr

	mov r8, [r0+]
	mov r9, [r0+]
	mov r10, [r0+]
	mov r11, [r0+]
)

%*DEFINE (PGETKEY reg) (
	%IF (%NES (%reg, r4)) THEN (
		mov [-r0], r4
	) FI

	calls &+pgmr_getkey

	%IF (%NES (%reg, r4)) THEN (
		mov %reg, r4
		mov r4, [r0+]
	) FI
)

%*DEFINE (PGETNUM reg, pseg, pofs, min, max, digits, initial, unk) (
	%IF (%NES (%reg, r4)) THEN (
		mov [-r0], r4
	) FI
	mov [-r0], r5
	mov [-r0], r8
	mov [-r0], r9
	mov [-r0], r10
	mov [-r0], r11
	mov [-r0], r12
	
	%CONMOV r10, %initial
	%CONMOV r9, %pseg
	%CONMOV r8, %pofs
	%PUSHVIA r4, %max
	%PUSHVIA r4, %min
	%PUSHVIA r4, %unk
	mov r5, #40h
	mov r4, #0A937h
	mov [-r0], r5
	mov [-r0], r4
	%PUSHVIA r4, %digits
	mov r12, #&^scratch_mem
	mov r11, #&:scratch_mem
	
	calls &+pgmr_getnum

	add r0, #12
	mov r12, [r0+]
	mov r11, [r0+]
	mov r10, [r0+]
	mov r9, [r0+]
	mov r8, [r0+]
	mov r5, [r0+]
	%IF (%NES (%reg, r4)) THEN (
		mov %reg, r4
		mov r4, [r0+]
	) FI
)
