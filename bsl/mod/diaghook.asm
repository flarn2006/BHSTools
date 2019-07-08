cmpb rl4, #0
jmpr cc_Z, diagbatt
subb rl4, #3
jmpr cc_Z, calladdr
subb rl4, #1
jmpr cc_Z, writemem
subb rl4, #1
jmpr cc_Z, acexec
subb rl4, #1
jmpr cc_Z, dynexec
subb rl4, #1
jmpr cc_Z, reboot
subb rl4, #1
jmpr cc_Z, mem_browser
jmps #3, #8546h

diagbatt:
jmps #3, #8408h

reboot:
srst

calladdr:
calls &+PromptForAddr
jb r5.15, return_to_diag_menu
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
calls &+PromptForAddr
jb r5.15, return_to_diag_menu
mov r8, r5
exts r8, #1
movb rl5, [r4]
movbz r5, rl5
%PGETNUM r5, &+Str_EnterNewByte, #0, #0FFh, #3, r5, #0
exts r8, #1
movb [r4], rl5
return_to_diag_menu:
jmps &+return_to_diag_menu

acexec:
callr arbitrary_code_exec
jmps &+return_to_diag_menu

dynexec:
calls #9, #0
jmps &+return_to_diag_menu

mem_browser:
calls &+MemoryBrowser
jmps &+return_to_diag_menu

arbitrary_code_exec:
sub r0, #34
mov r11, #40h
mov r10, r0
bclr r10.15

mov r9, #0
exts r11, #1
mov [r10], r9

try_again:
%PGETSTR &+Str_ArbCodeExec, r11, r10, #32
cmp r4, #1Bh
jmpr cc_NZ, not_escape
add r0, #34
ret
not_escape:
mov r9, r11
mov r8, r10
calls &+strlen
jb r4.0, try_again
mov r8, r10
mov [-r0], r11
mov [-r0], r10
mov [-r0], r4
calls &+fromhex
mov r4, [r0]
mov r10, [r0+#2]
mov r11, [r0+#4]
cmp r4, #16
jmpr cc_ULE, append_rets_and_exec
add r10, #8
mov r8, r10
add r8, #8
sub r4, #16
calls &+fromhex

append_rets_and_exec:
mov r4, [r0+]
mov r10, [r0+]
mov r11, [r0+]
shr r4, #1
add r10, r4
mov r5, #0DBh
exts r11, #2
movb [r10], rl5
movb [r10+#1], rh5
sub r10, r4
mov r4, #&:scratch_mem
mov r5, #40FAh
exts r11, #2
mov [r4], r5
mov [r4+#2], r10
calls &+scratch_mem
add r0, #34
calls &+ShowDebugDump
ret
