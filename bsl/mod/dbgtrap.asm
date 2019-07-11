; Post-SCXT stack:
; SP->[SP+0] (--) Previous CP
; CP->[SP+2] (R0)
;     [SP+4] (R1)
;     [SP+6] (R2)
;     [SP+8] (R3)
;    [SP+10] (R4)
;    [SP+12] (R5) RETI offset
;    [SP+14] (R6) RETI segment
;    [SP+16] (R7) Pre-trap PSW
;    [SP+18] (R8) Calling function's RETS offset
;    [SP+20] (R9) Calling function's RETS segment

sub SP, #10
scxt CP, SP
jmpr cc_UC, normal_reti
mov r1, r5
mov r2, r6
sub r1, #2
subc r2, #0
mov r3, #0FF00h
exts #41h, #2
mov r4, [r3+#2]
mov r3, [r3]

jnb r3.0, do_orig
cmpb rh3, rl2
jmpr cc_NZ, do_orig
cmp r1, r4
jmpr cc_NZ, do_orig
pop CP
add SP, #10

push r1
mov r1, SP
add r1, #4
mov r1, [r1]
mov PSW, r1
pop r1
calls #41h, #0FF04h

push r1
mov r1, #0FF00h
exts #41h, #1
mov r1, [r1]
bmov V, r1.1
pop r1
jmpr cc_V, do_orig_cpsetup
reti

do_orig_cpsetup:
sub SP, #10
scxt CP, SP
mov r1, r5
mov r2, r6
sub r1, #2
subc r2, #0

do_orig:
jmpr cc_UC, normal_reti
mov r4, r2
mov r3, r1
cmp r4, #0
jmpr cc_Z, orig_firstpage
sub r3, #2000h
subc r4, #0
orig_firstpage:
add r4, #0Ch
exts r4, #2
mov r4, [r3+#2]
mov r3, [r3]
cmpb rl3, #0DBh
jmpr cc_Z, inst_rets
cmpb rl3, #0DAh
jmpr cc_Z, inst_calls
cmpb rl3, #0FAh
jmpr cc_Z, inst_jmps

mov r4, r3
and r4, #0Fh
cmp r4, #0Dh
jmpr cc_Z, inst_jmpr

normal_reti:
pop CP
add SP, #10
reti

inst_rets:
; Discard our RETI stack frame, and construct a new one in place of the calling function's RETS frame, copying our PSW.
mov r1, r7
mov r7, r8
mov r8, r9
mov r9, r1
pop CP
add SP, #14
reti

inst_calls:
; Convert our RETI frame to a RETS frame, construct a RETI frame on top of that with the destination address, and RETI.
mov r1, r4
movbz r4, rh3
mov r3, r1
mov r1, r7
mov r7, r6
mov r6, r5
mov r5, r1
pop CP
add SP, #6
reti

inst_jmps:
; Just change the return address in our RETI frame.
movbz r6, rh3
mov r5, r4
jmpr cc_UC, normal_reti

inst_jmpr:
jmpr cc_UC, normal_reti
; Generate a JMPR and two JMPS's in the stack, and set our return address to go there.
mov r0, r3
movb rh1, rl6
movb rl1, #0FAh
mov r2, r5
movbz r3, rl6
movbz r4, rh0
shl r4, #1
add r4, r5
addc r3, #0
movb rh3, rl3
movb rl3, rl1
movb rh0, #2
mov r5, CP
mov r6, #0
jmpr cc_UC, normal_reti
