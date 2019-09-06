mov [-r0], r13
mov [-r0], r14

mov r13, #song-endjump
add r13, r4
mov r14, #9

loop:
exts r14, #3
mov r8, [r13]
mov r9, [r13+#2]
cmp r8, #0FFFFh
jmpr cc_Z, done
mov 09EB4h, r8
jmpr cc_Z, rest
calls #5, #91D0h

delay:
mov r8, r9
calls #5, #0AD98h
add r13, #4
jmpr cc_UC, loop

rest:
bclr T3CON.6
bclr T3CON.10
jmpr cc_UC, delay

done:
bclr T3CON.6
bclr T3CON.10
mov r14, [r0+]
mov r13, [r0+]
rets

song:
