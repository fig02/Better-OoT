;hook into what i think is the bomb deconstructor and set the model in hand value correctly
empty_bomb_fix:
	;displaced
	lw	a0, 0x001C($sp)
	
	addiu    sp, sp, -0x10    ;move sp back 16 bytes
	sw       t0, 0x04(sp)     ;save values at t0 and t1 to retrieve later
   	sw       t1, 0x08(sp)
   	li		 t0, 0x0100FE00   ;load word for value after bomb is gone
   	lui		 t1, 0x801E		  ;one byte more cause the following offset is signed
   	sw		 t0, 0xAB70(t1)   ;save word to 801DAB70
   	li       t0, 0x00 		  ;load byte for value after bomb is gone
   	sb	 	 t0, 0xAB74(t1)   ;store byte to 801DAB74
   	lw		 t1, 0x08(sp)	  ;load old values back to t0 and t1
   	lw		 t0, 0x04(sp)
   	jr		 ra 			  ;jump back
   	addiu    sp, sp, 0x10     ;increase stack pointer back to where it was
