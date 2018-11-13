after_time_travel:

    lui     t1, 0x801E
    lb      t0, 0xA288(t1)  ;load age
    bnez    t0, @@return    ;return if becoming child
    nop
    lb      t0, 0xA7(a1)
    andi    t0, t0, 0x20   ;check for light medallion in inventory
    bnez    t0, @@return   ;return if light medallion in inventory
    nop
    li      t0, 0x8000     ;set init time of day to 0x8000
    sh      t0, 0x0C(a1)
    sh      t0, 0x141A(a1)
    lb      t0, 0xA7(a1)   ;give light medallion
    ori     t0, t0, 0x20
    sb      t0, 0xA7(a1)

@@return:

    jr      ra
    nop