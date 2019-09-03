; If this is an LED keypad, exit with an error beep.
mov r4, [r0+#44h] ;device class
cmp r4, #1
jmpr cc_Z, lcd_keypad
cmp r4, #1Ah
jmpr cc_Z, lcd_keypad
or r14, #6
jmps #2, #0F25Eh

lcd_keypad:
; Display "TIME" and "ENTER MASTER CODE" on the screen.
movb rl4, #86h ;ENTER MASTER CODE
movb [r0+#2Bh], rl4
movb rl4, #8   ;TIME
movb [r0+#2Ch], rl4
mov r10, #40h
mov r9, #24h
add r9, r0
bclr r9.15
mov r8, r13
calls #3, #35Ch ;kp_lcd_out

; Allow the user to enter a code.
mov r4, #30
mov [-r0], r4
mov r4, #0
mov [-r0], r4
mov r5, [r0+#40h]
mov r4, [r0+#3Eh]
exts r5, #1
movb rl4, [r4+#2Ah]
andb rl4, #0Fh
movbz r4, rl4
mov [-r0], r4
mov r12, #40h
mov r11, #34h
add r11, r0
bclr r11.15
mov r10, [r0+#16h]
mov r9, [r0+#14h]
mov r8, [r0+#4Eh]    ;entry flags
bset r8.5
calls #3, #0D34h     ;kp_entry
add r0, #6
movb [r0+#46h], rl4  ;set keycode var

; Did the user enter a valid code?
mov r7, [r0+#30h]
mov r6, [r0+#2Eh]
or r6, r7
jmpr cc_NZ, valid_code

; No, they did not. Was an invalid code entered? Or nothing at all?
mov r9, [r0+#10h]
mov r8, [r0+#0Eh]
calls #5, #0E4F6h  ;strlen
cmp r4, #0
jmpr cc_NZ, bad_code_or_cancel

; Nothing was entered. Did the user press either the Cancel key or no key at all (timeout)?
movb rl4, [r0+#46h]
jmpr cc_Z, bad_code_or_cancel
cmp r4, #18h
jmpr cc_Z, bad_code_or_cancel

; No, so just go to the next Options item.
jmps #2, #0F25Eh

bad_code_or_cancel:
movb rl4, [r0+#46h]
movb rl4, #18h
movb [r0+#46h], rl4
or r14, #6
jmps #2, #0F25Eh

valid_code:
; But was it the master code?
mov r5, [r0+#30h]
mov r4, [r0+#2Eh]
exts r5, #1
movb rl4, [r4+#2]
cmpb rl4, #95
jmpr cc_NZ, bad_code_or_cancel

; Prompt for first digit
movb rl4, #5
movb [r0+#25h], rl4
mov r4, #4040h
mov [r0+#26h], r4
bclr r4.14
mov [r0+#28h], r4
mov r4, #4200h  ;ENTER NEW
mov [r0+#2Ah], r4
movb rl4, #8    ;TIME
movb [r0+#2Ch], rl4

mov r10, #40h
mov r9, #24h
add r9, r0
bclr r9.15
mov r8, r13
calls #3, #35Ch ;kp_lcd_out

mov [-r0], r15

movb rl4, #1
movb [r0+#27h], rl4

mov r8, #30
calls #3, #7DCh ;kp_getkey
sub r4, #30h
jmpr cc_C, bad_digit
cmp r4, #1
jmpr cc_UGT, bad_digit
jmpr cc_NZ, first_digit_not_1
movb rl5, #7
movb [r0+#27h], rl5
first_digit_not_1:

; multiply r4 by 10
mov r5, r4
shl r4, #3
shl r5, #1
add r4, r5

mov r15, r4

; Prompt for second digit
movb rl4, #8
movb [r0+#28h], rl4
mov r10, #40h
mov r9, #26h
add r9, r0
bclr r9.15
mov r8, r13
calls #3, #35Ch ;kp_lcd_out

mov r8, #30
calls #3, #7DCh ;kp_getkey
sub r4, #30h
jmpr cc_C, bad_digit
cmp r4, #10
jmpr cc_NC, bad_digit

add r15, r4

cmp r15, #12
jmpr cc_UGT, bad_digit
jmpr cc_Z, hour_is_12
cmp r15, #0
jmpr cc_NZ, continue_after_hour_check

bad_digit:
mov r15, [r0+]
or r14, #6
jmps #2, #0F25Eh

hour_is_12:
mov r15, #0

continue_after_hour_check:

; Get its 7-segment representation
exts #6, #1
movb rl4, [r4+#87E4h]
movb [r0+#28h], rl4

; Prompt for third digit
movb rl4, #8
movb [r0+#29h], rl4
mov r10, #40h
mov r9, #26h
add r9, r0
bclr r9.15
mov r8, r13
calls #3, #35Ch ;kp_lcd_out

mov r8, #30
calls #3, #7DCh ;kp_getkey
sub r4, #30h
jmpr cc_C, bad_digit
cmp r4, #6
jmpr cc_NC, bad_digit

; Get its 7-segment representation
exts #6, #1
movb rl5, [r4+#87E4h]
movb [r0+#29h], rl5

; Multiply it by 10
mov r5, r4
shl r4, #3
shl r5, #1
add r4, r5

shl r15, #8
add r15, r4

; Prompt for fourth digit
movb rl4, #8
movb [r0+#2Ah], rl4
mov r10, #40h
mov r9, #26h
add r9, r0
bclr r9.15
mov r8, r13
calls #3, #35Ch ;kp_lcd_out

mov r8, #30
calls #3, #7DCh ;kp_getkey
sub r4, #30h
jmpr cc_C, bad_digit
cmp r4, #10
jmpr cc_NC, bad_digit

add r15, r4

; Get its 7-segment representation
exts #6, #1
movb rl5, [r4+#87E4h]
movb [r0+#2Ah], rl5

; Prompt for AM/PM
movb rl4, [r0+#27h]
orb rl4, #10h
movb [r0+#27h], rl4
movb rl4, #2
movb [r0+#2Dh], rl4
movb [r0+#2Eh], rl4

ampm_loop:
movb rl4, [r0+#27h]
xorb rl4, #18h
movb [r0+#27h], rl4
mov r10, #40h
mov r9, #26h
add r9, r0
bclr r9.15
mov r8, r13
calls #3, #35Ch ;kp_lcd_out

mov r8, #1
calls #3, #7DCh ;kp_getkey
cmp r4, #0
jmpr cc_Z, ampm_loop

sub r4, #31h
jmpr cc_Z, selection_done
jmpr cc_C, bad_digit
cmp r4, #2
jmpr cc_NC, bad_digit

add r15, #3072 ;12<<8

selection_done:
mov r4, r15
mov r5, r4
shl r5, #8
exts #41h, #2
movb 0E55Ch, rh4 ;Set the hour
mov 0E55Ah, r5   ;Set the minute (and second)

mov r15, [r0+]
bclr r14.1
bset r14.2
jmps #2, #0F25Eh
