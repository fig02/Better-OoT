#include "dungeon_info.h"
#include "gfx.h"
#include "text.h"
#include "util.h"
#include "quickboots.h"
#include "z64.h"

void c_init() {
    heap_init();
    gfx_init();
    quickboots_init();
}

void before_game_state_update() {
    handle_quickboots();
}

