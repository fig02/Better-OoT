jabu_jabu:
	addiu	sp, sp, -0x10
	sw		t0, 0x00(sp)
	swc1	f2, 0x04(sp)
	swc1	f3, 0x08(sp)

	lui		t0, 0x801E
	addiu	t0, 0xAA30

	lwc1	f2, 0x28(t0) ; links y
	lui		t0, 0xC493 
	mtc1	t0, f3 ; f3 = -1176
	c.lt.s	f2, f3
	bc1t	@@bottom
	nop
	li		t5, 0x200
	b		@@return
	nop

@@bottom:
	li		t5, 0x100

@@return:
	
	lwc1	f3, 0x08(sp)
	lwc1	f2, 0x04(sp)
	lw		t0, 0x00(sp)
	jr		ra
	addiu	sp, sp, 0x10