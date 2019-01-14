; set the angle for the solution to the puzzle to 0x5555 (first try)

truth_spinner_fix:
	lui    t5, 0x5555     ;facing angle for first try
	jr     ra
	sra    t5, t5, 0x10   ;shift right 2 bytes