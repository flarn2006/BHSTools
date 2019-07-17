	sub r1, #31337
	jmpr cc_Z, ibus_31337

	add r1, #31331
	jmpr cc_Z, ibus_6
	jmps #2, #1B94h
ibus_6:
	jmps #2, #1EAEh

ibus_31337:
	mov r5, [r0+#8]
	mov r4, [r0+#6]
	add r4, #4
	calls #0, #3BFEh  ; indirect call to r5:r4
	jmps #2, #4488h
