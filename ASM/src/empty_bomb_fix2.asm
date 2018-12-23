empty_bomb_fix2:
	lw       t6, 0x039C(s0) ;load bomb in hand pointer
	or       a0, s1, r0
	bnez     t6, @@return
	nop
	jal      0x8038B040
	or       a1, s0, r0

@@return:
	jr    ra
	nop