; set the angle for the solution to the puzzle to 0x5555 (first try)

truth_spinner_fix:
	addiu  t5, r0, 0x5555     ;facing angle for first try
	jr     ra
	nop