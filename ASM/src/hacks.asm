;==================================================================================================
; Time Travel
;==================================================================================================

; After time travel
; Replaces:
;   jr      ra
.org 0xAE59E0 ; In memory: 0x8006FA80
    j       after_time_travel
    

;==================================================================================================
; Item Overrides
;==================================================================================================

; Prevent Silver Gauntlets warp
; Replaces:
;   addiu   at, r0, 0x0035
.org 0xBE9BDC ; In memory: 0x803A4BCC
    addiu   at, r0, 0x8383 ; Make branch impossible

;==================================================================================================
; Every frame hooks
;==================================================================================================

; Runs before the game state update function
; Replaces:
;   lw      t6, 0x0018 (sp)
;   lui     at, 0x8010
.org 0xB12A34 ; In memory: 0x8009CAD4
    jal     before_game_state_update_hook
    nop

;==================================================================================================
; Song Fixes
;==================================================================================================

; Replaces:
;	addu	at, at, s3
.org 0xB54B38 ; In memory: 800DEBD8
	jal		warp_song_fix

;==================================================================================================
; Initial save
;==================================================================================================

; Replaces:
;   sb      t0, 32(s1)
;   sb      a1, 33(s1)
.org 0xB06C2C ; In memory: ???
    jal     write_initial_save
    sb      t0, 32(s1)

;==================================================================================================
; Ocarina Song Cutscene Overrides
;==================================================================================================

; a3 = item ID
; Replaces
; li v0,0xFF
.org 0xAE5DF8
    jal     override_ocarina_songs
; sw $t7, 0xa4($t0)
.org 0xAE5E04
    nop

; Replaces
;lui  at,0x1
;addu at,at,s0
.org 0xAC9ABC
    jal     override_requiem_song
    nop

; lw $t7, 0xa4($s0)
; lui $t3, 0x8010
; addiu $t3, $t3, -0x70cc
; and $t8, $t6, $t7
.org 0xB06400
    lb  t7,0x0EDE(s0) ; check learned song from ZL
.skip 4
.skip 4
    andi t8, t7, 0x02

; Impa does not despawn from Zelda Escape CS
.org 0xD12F78
    li  t7, 0

;li v1, 5
.org 0xE29388
    j   override_saria_song_check

;lh v0, 0xa4(t6)       ; v0 = scene
.org 0xE2A044
    jal  set_saria_song_flag

; li a1, 3
.org 0xDB532C
    jal override_song_of_time

;==================================================================================================
; Shop Injections
;==================================================================================================

; Check sold out override
.org 0xC004EC
    j        Shop_Check_Sold_Out

; Allow Shop Item ID up to 100 instead of 50
; slti at, v1, 0x32
.org 0xC0067C
    slti     at, v1, 100

; Set sold out override
; lh t6, 0x1c(a1)
.org 0xC018A0
    jal      Shop_Set_Sold_Out

; Only run init function if ID is in normal range
; jr t9
.org 0xC6C7A8
    jal      Shop_Keeper_Init_ID
.org 0xC6C920
    jal      Shop_Keeper_Init_ID

; Override Deku Salescrub sold out check
; addiu at, zero, 2
; lui v1, 0x8012
; bne v0, at, 0xd8
; addiu v1, v1, -0x5a30
; lhu t9, 0xef0(v1)
.org 0xEBB85C
    jal     Deku_Check_Sold_Out
    .skip 4
    bnez    v0, @Deku_Check_True
    .skip 4
    b       @Deku_Check_False
.org 0xEBB8B0
@Deku_Check_True:
.org 0xEBB8C0
@Deku_Check_False:

; Ovveride Deku Scrub set sold out
; sh t7, 0xef0(v0)
.org 0xDF7CB0
    jal     Deku_Set_Sold_Out

;==================================================================================================
; V1.0 Scarecrow Song Bug
;==================================================================================================

; Replaces:
;	jal		0x80057030 ; copies Scarecrow Song from active space to save context
.org 0xB55A64 ; In memory 800DFB04
    jal		save_scarecrow_song


;==================================================================================================
; Twinrova position fix
;==================================================================================================
;
; Replaces:     lh  t0, 0x0142(s2) overlay+0x7698

.org 0xD68978
    jal    twinrova_cs_fix
    lh     t0, 0x142(s2)


;==================================================================================================
; Empty bomb fix
;==================================================================================================
;
; Replaces:  lw a1, 0x0018($sp) bomb ovl+134
;
.org 0xC0E404
    jal    empty_bomb_fix
    lw     a1, 0x0018($sp)

;==================================================================================================
; Talon cs skip
;==================================================================================================
;
; Replaces: 

.org 0xCC0038
    jal    talon_break_free
    lw     a0, 0x0018(sp)

;==================================================================================================
; First try Truth Spinner
;==================================================================================================
;
;Replaces: lw   a0, 0x003C(sp)
;          addu t5, t4, at

.org 0xDB9E78 
    jal    truth_spinner_fix
    lw     a0, 0x003C(sp)

;==================================================================================================
; Big Goron Fix
;==================================================================================================
;
;Replaces: beq     $zero, $zero, lbl_80B5AD64 

.org 0xED645C
    jal     bgs_fix
    nop

;==================================================================================================
; Warp song speedup
;==================================================================================================
;
; Replaces: 
;
.org 0xBEA044
   jal      warp_speedup
   nop

;==================================================================================================
; Quick Boots Display
;==================================================================================================
;
; Replaces lw    s4, 0x0000(s6)
;          lw    s1, 0x02B0(s4)
.org 0xAEB68C ; In Memory: 0x8007572C
    jal     qb_draw
    nop

;==================================================================================================
; ZL Time of Day
;==================================================================================================
;
; Replaces: lui a3, 0x3F80
;
.org 0xEFC7B8
    jal     zelda_tod
    lui     a3, 0x3F80

;==================================================================================================
; Jabu Jabu Elevator
;==================================================================================================

;Replaces: addiu t5, r0, 0x0200
.org 0xD4BE6C
    jal     jabu_elevator
