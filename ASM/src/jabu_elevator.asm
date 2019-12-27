jabu_elevator:
	addiu	sp, sp, -0x10
	sw		t0, 0x00(sp)
	swc1	f0, 0x04(sp)
	swc1	f2, 0x08(sp)
	lb      t0, JABU_ENABLE ;check user settings
	beqz    t0, @@return    ;return if unchecked
	nop

	lui		t0, 0x801E
	addiu	t0, 0xAA30

	lwc1	f0, 0x28(t0) ; links y
	lui		t0, 0xC496 
	mtc1	t0, f2 ; f2 = -1200
	nop
	c.lt.s	f0, f2
	nop
	bc1t	@@bottom
	nop
	li		t5, 0x200
	b		@@return
	nop

@@bottom:
	li		t5, 0xC0

@@return:
	
	lwc1	f2, 0x08(sp)
	lwc1	f0, 0x04(sp)
	lw		t0, 0x00(sp)
	jr		ra
	addiu	sp, sp, 0x10