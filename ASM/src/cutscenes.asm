override_great_fairy_cutscene:
    ; a0 = global context
    ; a2 = fairy actor
    lw      t0, 0x1D2C (a0) ; t0 = switch flags
    li      t1, 1
    sll     t1, t1, 0x18 ; t1 = ZL switch flag
    and     v0, t0, t1
    beqz    v0, @@return ; Do nothing until ZL is played
    nop

    lhu     t2, 0x02DC (a2) ; Load fairy index
    li      t3, SAVE_CONTEXT

    lhu     t4, 0xA4 (a0) ; Load scene number
    beq     t4, 0x3D, @@item_fairy
    nop

    ; Handle upgrade fairies
    addu    t4, a0, t2
    lbu     t5, 0x1D28 (t4) ; t5 = chest flag for this fairy
    bnez    t5, @@return ; Use default behavior if the item is already obtained
    nop
    li      t5, 1
    sb      t5, 0x1D28 (t4) ; Mark item as obtained
    addiu   t2, t2, 3 ; t2 = index of the item in FAIRY_ITEMS
    b       @@give_item
    nop

@@item_fairy:
    li      t4, 1
    sllv    t4, t4, t2 ; t4 = fairy item mask
    lbu     t5, 0x0EF2 (t3) ; t5 = fairy item flags
    and     t6, t5, t4
    bnez    t6, @@return ; Use default behavior if the item is already obtained
    nop
    or      t6, t5, t4
    sb      t6, 0x0EF2 (t3) ; Mark item as obtained

@@give_item:
    ; Unset ZL switch
    nor     t1, t1, t1
    and     t0, t0, t1
    sw      t0, 0x1D2C (a0)

    ; Load fairy item and mark it as pending
    li      t0, FAIRY_ITEMS
    addu    t0, t0, t2
    lb      t0, 0x00 (t0)
    li      t1, PENDING_SPECIAL_ITEM
    sb      t0, 0x00 (t1)

    li      v0, 0 ; Prevent fairy animation

@@return:
    jr      ra
    nop

;==================================================================================================

override_light_arrow_cutscene:
    li      t0, LIGHT_ARROW_ITEM
    lb      t0, 0x00 (t0)
    b       store_pending_special_item
    nop


override_fairy_ocarina_cutscene:
    li      t0, FAIRY_OCARINA_ITEM
    lb      t0, 0x00 (t0)
    b       store_pending_special_item
    nop

;a3 = item ID
override_ocarina_songs:
    li      v0, 0xFF
    addi    t0, a3, -0x5A
    addi    t0, t0, 0x61
    b       store_pending_special_item
    nop

override_requiem_song:
    li      t0, 0x64
    b       store_pending_special_item
    nop

override_epona_song:
    lui    at,0x8012       
    addiu  at,at,0xA5D0 ; v1 = 0x8012a5d0 # save context (sav)
    lb     t0,0x0EDE(at) ; check learned song from malon flag
    ori    t0,t0,0x01  ; t9 = "Invited to Sing With Child Malon"
    sb     t0,0x0EDE(at)

    li      t0, 0x68
    b       store_pending_special_item
    nop

override_suns_song:
    lui    at,0x8012       
    addiu  at,at,0xA5D0 ; v1 = 0x8012a5d0 # save context (sav)
    lb     t0,0x0EDE(at) ; learned song from sun's song
    ori    t0,t0,0x04  ;
    sb     t0,0x0EDE(at);

    li      t0, 0x6A
    b       store_pending_special_item
    nop

override_song_of_time:
    li      a1, 3
    li      t0, 0x6B
    b       store_pending_special_item
    nop

store_pending_special_item:
; Don't add item if it's already pending
    li      t1, PENDING_SPECIAL_ITEM
    li      t2, PENDING_SPECIAL_ITEM_END ; max number of entries
@@find_duplicate_loop:
    lb      t4, 0x00 (t1)
    beq     t4, t0, @@return ; item is already in list
    addi    t1, t1, 0x01
    bne     t1, t2, @@find_duplicate_loop ; end of list
    nop

; Find free index to add item
    li      t1, (PENDING_SPECIAL_ITEM - 1)
@@find_empty_loop:
    addi    t1, t1, 0x01
    beq     t1, t2, @@return ; end of list
    lb      t4, 0x00 (t1)
    bnez    t4, @@find_empty_loop ; next index
    nop

    sb      t0, 0x00 (t1) ; store in first free spot
@@return:
    jr      ra
    nop

override_saria_song_check:
    move    t7, v1
    lb      t4, 0x0EDF(t7)
    andi    t6, t4, 0x80  
    beqz    t6, @@get_item
    li      v1, 5

    jr      ra
    li      v0, 2

@@get_item:
    jr      ra
    move    v0, v1

set_saria_song_flag:
    lh      v0, 0xa4(t6)       ; v0 = scene
    li      t0, SAVE_CONTEXT
    lb      t1, 0x0EDF(t0)
    ori     t1, t1, 0x80
    sb      t1, 0x0EDF(t0)
    jr      ra
    nop

; Injection for talking to the Altar in the Temple of Time
; Should set flag in save that it has been spoken to.
set_dungeon_knowledge:
    addiu   sp, sp, -0x10
    sw      ra, 0x04(sp)

    ; displaced instruction
    jal     0xD6218
    nop

    li      t4, SAVE_CONTEXT
    lh      t5, 0x0F2E(t4) ; flags
    lw      t8, 0x0004(t4) ; age

    beqz    t8, @@set_flag
    li      t6, 0x0001 ; adult bit
    li      t6, 0x0002 ; child bit

@@set_flag:
    or      t5, t5, t6
    sh      t5, 0x0F2E(t4) ; set the flag

    lw      ra, 0x04(sp)
    addiu   sp, sp, 0x10

    jr      ra
    nop

;Injection for fixing the angle after the twinrova defeat scene so
;so that the initial angle is the same as vanilla

twinrova_cs_fix:
    ; displaced 
    addiu    t1,r0,0x0001

    addiu    sp, sp, -0x10
    sw        t0, 0x04(sp)
    sw        t1, 0x08(sp)
    li        t0, 0x7C7C
    lui        t1, 0x801E
    sh        t0, 0xAAE6(t1)
    lw        t1, 0x08(sp)
    lw        t0, 0x04(sp)
    jr        ra
    addiu    sp, sp, 0x10

;Breaking free of the talon cutscene after event flag is set

talon_break_free:

    ;displaced code
    addiu    t1, r0, 0x0041

    ;preserve registers (t0, t1, t2, t4)
    addiu    sp, sp, -0x20
    sw       t0, 0x04(sp)
    sw       t1, 0x08(sp)
    sw       t2, 0x0C(sp)
    sw       t4, 0x10(sp)

    lui    t2, 0xFFFF
    sra    t2, t2, 0x10   ;shift right 2 bytes
    lui    t0, 0x801D
    lh     t4, 0x894C(t0) ;load current value @z64_game.event_flag
    beq    t4, t2, @@msg  ;if in non-cs state, jump to next check
    nop
    sh     r0, 0x894C(t0) ;store 0 to z64_game.event_flag

@@msg:
    lui    t0, 0x801E
    lb     t2, 0x887C(t0)
    beqz   t2, @@return   ;return if msg_state_1 is 0
    nop
    lui    t1, 0x0036
    sra    t1, t1, 0x10   ;shift right 2 bytes
    sb     t1, 0x887C(t0) ;store 0x36 to msg_state_1
    lui    t1, 0x0002
    sra    t1, 0x10       ;shift right 2 bytes
    sb     t1, 0x895F(t0) ;store 0x02 to msg_state_3
    lui    t0, 0x801F
    sb     r0, 0x8D38(t0) ;store 0x00 to msg_state_2

@@return:
    lw       t4, 0x10(sp)
    lw       t2, 0x0C(sp)
    lw       t1, 0x08(sp)
    lw       t0, 0x04(sp)
    jr     ra
    addiu    sp, sp, 0x20


warp_speedup:

    la     t2, 0x800FE49C ;pointer to links overlay in RAM 
    lw     t2, 0(t2)
    beqz   t2, @@return
    nop
    la     t0, GLOBAL_CONTEXT
    lui    t3, 0x0001
    ori    t3, t3, 0x04C4 ;offset of warp song played
    add    t0, t0, t3
    lh     t1, 0x0(t0)
    lui    t3, 0x0002
    ori    t3, t3, 0x26CC
    add    t2, t2, t3     ;entrance Table of Warp songs
    sll    t1, t1, 1
    addu   t2, t1, t2 
    lh     t1, 0x0(t2) 
    sh     t1, 0x1956(t0) ;next entrance 
    li     t1, 0x14
    sb     t1, 0x1951(t0) ;scene load flag
    la     t0, SAVE_CONTEXT
    lh     t1, 0x13D2(t0) ; Timer 2 state
    beqz   t1, @@return
    nop

    li     t1, 0x01
    sh     t1, 0x13D4(t0) ; Timer 2 value
    
@@return: 
    la     t0, GLOBAL_CONTEXT
    la     t1, CS_POINTER     ;address of fake cs
    sw     t1, 0x1D68(t0)     ;set cs pointer to address of fake cs
    jr     ra
    nop


zelda_tod:
    ori     t7, t6, 0x0001

    addiu   sp, sp, -0x20
    sw      t0, 0x04(sp)
    sw      t1, 0x08(sp)

    la      t0, 0x8011A5D0 ;save context
    li      t1, 0x8000     ;value
    sh      t1, 0x0C(t0)   ;time1
    sh      t1, 0x141A(t0) ;time2

    lw      t1, 0x08(sp)
    lw      t0, 0x04(sp)
    jr      ra
    addiu   sp, sp, 0x20