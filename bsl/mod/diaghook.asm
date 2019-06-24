cmpb rl4, #0
jmpr cc_Z, diagbatt
subb rl4, #3
jmpr cc_Z, calladdr
subb rl4, #1
jmpr cc_Z, writemem
subb rl4, #1
jmpr cc_Z, reboot
jmpr cc_UC, done

diagbatt:
jmps #3, #8408h

reboot:
srst

calladdr:
callr prompt_for_addr
shl r5, #8
movb rl5, #0DAh
mov r11, #0A91Eh
exts #40h, #1
mov [r11], r5
add r11, #2
exts #40h, #1
mov [r11], r4
add r11, #2
mov r5, #0DBh
exts #40h, #1
mov [r11], r5
jmps #40h, #0A91Eh

writemem:
callr prompt_for_addr
mov [-r0], r5
mov [-r0], r4
mov r10, #0
mov r8, #&:Str_EnterNewByte
mov r4, #0FFh
callr prompt_for_num
mov r5, r4
mov r4, [r0+]
mov r8, [r0+]
exts r8, #1
movb [r4], rl5

done:
jmps #3, #8546h

prompt_for_num:
mov [-r0], r4
mov r4, #0
mov [-r0], r4
mov [-r0], r4
mov r4, #0Eh
add r4, r0
mov r5, #0
add r4, #8000h
addc r5, #3Fh
mov [-r0], r5
mov [-r0], r4
mov r4, #5
mov [-r0], r4
mov r11, #0A91Eh
mov r12, #40h
mov r9, #8 ;segment of prompt text
calls &+pgmr_getnum
add r0, #12
ret

prompt_for_addr:
mov r10, #0
mov r8, #&:Str_EnterSegment
mov r4, #41h
callr prompt_for_num
mov [-r0], r4
mov r10, #0DC20h
mov r8, #&:Str_EnterOffset
mov r4, #0FFFFh
callr prompt_for_num
mov r5, [r0+]
ret
