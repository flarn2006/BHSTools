cmpb rl4, #1Bh
jmpr cc_Z, exit_callstat

cmp r4, #0Dh
jmpr cc_NZ, return_to_callstat

mov r9, #&^scratch_mem
mov r8, #&:scratch_mem+2

exts r9, #1
movb [r8], rh4
sub r8, #2
mov r4, #5441h
exts r9, #1
mov [r8], r4

%PGETSTR &+Str_ModemCommand, &+scratch_mem, #15

mov [-r0], r8
exts r9, #1
movb rh4, [r8]
jmpr cc_NZ, find_zero_loop

add r0, #2
jmpr cc_UC, return_to_callstat

find_zero_loop:
add r8, #1
exts r9, #1
movb rh4, [r8]
jmpr cc_NZ, find_zero_loop
movb rl4, #0Dh
exts r9, #1
movb [r8], rl4
add r8, #1
exts r9, #1
movb [r8], rh4

mov r8, [r0+]

%PPUTSTR #6, #42F1h, #1, #4

mov r4, #1
mov 9F18h, r4
calls #5, #0B3D4h
calls #4, #9Ah

return_to_callstat:
jmps #3, #848Ch

exit_callstat:
jmps #3, #8548h
