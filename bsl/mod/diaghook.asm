cmpb rl4, #0
jmpr cc_Z, diagbatt
subb rl4, #3
jmpr cc_Z, calladdr
subb rl4, #1
jmpr cc_Z, writemem
subb rl4, #1
jmpr cc_Z, dynexec
subb rl4, #1
jmpr cc_Z, reboot
jmps #3, #8546h

diagbatt:
jmps #3, #8408h

reboot:
srst

calladdr:
callr prompt_for_addr
shl r5, #8
movb rl5, #0DAh
mov r11, #&:scratch_mem
exts #&^scratch_mem, #1
mov [r11], r5
add r11, #2
exts #&^scratch_mem, #1
mov [r11], r4
add r11, #2
mov r5, #0DBh
exts #&^scratch_mem, #1
mov [r11], r5
calls &+scratch_mem
calls &+ShowDebugDump
jmps &+return_to_diag_menu

writemem:
callr prompt_for_addr
mov r8, r5
exts r8, #1
movb rl5, [r4]
movbz r5, rl5
%PGETNUM r5, &+Str_EnterNewByte, #0, #0FFh, #3, r5, #0
exts r8, #1
movb [r4], rl5
jmps &+return_to_diag_menu

dynexec:
calls #9, #0
jmps &+return_to_diag_menu

prompt_for_addr:
%PGETNUM r5, &+Str_EnterSegment, #0, #41h, #3, #0, #0
%PGETNUM r4, &+Str_EnterOffset, #0, #0FFFFh, #5, #0DC20h, #0
ret
