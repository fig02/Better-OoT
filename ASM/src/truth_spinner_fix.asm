; set the angle for the solution to the puzzle to 0x5555 (first try)

truth_spinner_fix:
	lui    at, 0x801F
	lui    t5, 0x5555     ;facing angle for first try
	sra    t5, t5, 0x10   ;shift right 2 bytes
	jr     ra
	nop