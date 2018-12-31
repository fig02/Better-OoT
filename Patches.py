import io
import json
import logging
import os
import platform
import struct
import subprocess
import random
import copy

from Utils import local_path, default_output_path
from Messages import *
from MQ import patch_files, File, update_dmadata, insert_space, add_relocations

TunicColors = {
    "Custom Color": [0, 0, 0], 
    "Kokiri Green": [0x1E, 0x69, 0x1B],
    "Goron Red": [0x64, 0x14, 0x00],
    "Zora Blue": [0x00, 0x3C, 0x64],
    "Black": [0x30, 0x30, 0x30],
    "White": [0xF0, 0xF0, 0xFF],
    "Azure Blue": [0x13, 0x9E, 0xD8],
    "Vivid Cyan": [0x13, 0xE9, 0xD8],
    "Light Red": [0xF8, 0x7C, 0x6D],
    "Fuchsia":[0xFF, 0x00, 0xFF],
    "Purple": [0x95, 0x30, 0x80],
    "MM Purple": [0x50, 0x52, 0x9A],
    "Twitch Purple": [0x64, 0x41, 0xA5],
    "Purple Heart": [0x8A, 0x2B, 0xE2],
    "Persian Rose": [0xFF, 0x14, 0x93],
    "Dirty Yellow": [0xE0, 0xD8, 0x60],
    "Blush Pink": [0xF8, 0x6C, 0xF8],
    "Hot Pink": [0xFF, 0x69, 0xB4],
    "Rose Pink": [0xFF, 0x90, 0xB3],
    "Orange": [0xE0, 0x79, 0x40],
    "Gray": [0xA0, 0xA0, 0xB0],
    "Gold": [0xD8, 0xB0, 0x60],
    "Silver": [0xD0, 0xF0, 0xFF],
    "Beige": [0xC0, 0xA0, 0xA0],
    "Teal": [0x30, 0xD0, 0xB0],
    "Blood Red": [0x83, 0x03, 0x03],
    "Blood Orange": [0xFE, 0x4B, 0x03],
    "Royal Blue": [0x40, 0x00, 0x90],
    "Sonic Blue": [0x50, 0x90, 0xE0],
    "NES Green": [0x00, 0xD0, 0x00],
    "Dark Green": [0x00, 0x25, 0x18],
    "Lumen": [80, 140, 240],
}

NaviColors = {
    "Custom Color": [0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00], 
    "Gold": [0xFE, 0xCC, 0x3C, 0xFF, 0xFE, 0xC0, 0x07, 0x00],
    "White": [0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0xFF, 0x00],
    "Green": [0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0x00],
    "Light Blue": [0x96, 0x96, 0xFF, 0xFF, 0x96, 0x96, 0xFF, 0x00],
    "Yellow": [0xFF, 0xFF, 0x00, 0xFF, 0xC8, 0x9B, 0x00, 0x00],
    "Red": [0xFF, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0x00],
    "Magenta": [0xFF, 0x00, 0xFF, 0xFF, 0xC8, 0x00, 0x9B, 0x00],
    "Black": [0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00],
    "Tatl": [0xFF, 0xFF, 0xFF, 0xFF, 0xC8, 0x98, 0x00, 0x00],
    "Tael": [0x49, 0x14, 0x6C, 0xFF, 0xFF, 0x00, 0x00, 0x00],
    "Fi": [0x2C, 0x9E, 0xC4, 0xFF, 0x2C, 0x19, 0x83, 0x00],
    "Ciela": [0xE6, 0xDE, 0x83, 0xFF, 0xC6, 0xBE, 0x5B, 0x00],
    "Epona": [0xD1, 0x49, 0x02, 0xFF, 0x55, 0x1F, 0x08, 0x00],
    "Ezlo": [0x62, 0x9C, 0x5F, 0xFF, 0x3F, 0x5D, 0x37, 0x00],
    "King of Red Lions": [0xA8, 0x33, 0x17, 0xFF, 0xDE, 0xD7, 0xC5, 0x00],
    "Linebeck": [0x03, 0x26, 0x60, 0xFF, 0xEF, 0xFF, 0xFF, 0x00],
    "Loftwing": [0xD6, 0x2E, 0x31, 0xFF, 0xFD, 0xE6, 0xCC, 0x00],
    "Midna": [0x19, 0x24, 0x26, 0xFF, 0xD2, 0x83, 0x30, 0x00],
    "Phantom Zelda": [0x97, 0x7A, 0x6C, 0xFF, 0x6F, 0x46, 0x67, 0x00],
}

def get_tunic_colors():
    return list(TunicColors.keys())

def get_tunic_color_options():
    return ["Random Choice", "Completely Random"] + get_tunic_colors()

def get_navi_colors():
    return list(NaviColors.keys())

def get_navi_color_options():
    return ["Random Choice", "Completely Random"] + get_navi_colors()

def patch_rom(world, rom):
    with open(local_path('data/rom_patch.txt'), 'r') as stream:
        for line in stream:
            address, value = [int(x, 16) for x in line.split(',')]
            rom.write_byte(address, value)

    #Boots on D-Pad
    if world.quickboots:
        symbol = rom.sym('QUICKBOOTS_ENABLE')
        rom.write_byte(symbol, 0x01)

    # Can always return to youth
    rom.write_byte(0xCB6844, 0x35)
    rom.write_byte(0x253C0E2, 0x03) # Moves sheik from pedestal

    if world.skip_intro:
        # Remove intro cutscene
        rom.write_bytes(0xB06BBA, [0x00, 0x00])

    # Fix 1.0 graves
    rom.write_byte(0x0202039D, 0x20)
    rom.write_byte(0x0202043C, 0x24)

    # Fix Castle Courtyard to check for meeting Zelda, not Zelda fleeing, to block you
    rom.write_bytes(0xCD5E76, [0x0E, 0xDC])
    rom.write_bytes(0xCD5E12, [0x0E, 0xDC])

    # Cutscene for all medallions never triggers when leaving shadow or spirit temples
    rom.write_byte(0xACA409, 0xAD)
    rom.write_byte(0xACA49D, 0xCE)

    # Speed Zelda's Letter scene
    rom.write_bytes(0x290E08E, [0x05, 0xF0])
    rom.write_byte(0xEFCBA7, 0x08)
    rom.write_byte(0xEFE7C7, 0x05)
    rom.write_bytes(0xEFE938, [0x00, 0x00, 0x00, 0x00])
    rom.write_bytes(0xEFE948, [0x00, 0x00, 0x00, 0x00])
    rom.write_bytes(0xEFE950, [0x00, 0x00, 0x00, 0x00])

    # Speed Zelda escaping from Hyrule Castle
    Block_code = [0x00, 0x00, 0x00, 0x01, 0x00, 0x21, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02]
    rom.write_bytes(0x1FC0CF8, Block_code)

    if world.song_speedup:
        # Speed learning Zelda's Lullaby
        rom.write_int32s(0x02E8E90C, [0x000003E8, 0x00000001])                   # Terminator Execution
        rom.write_int16s(None, [0x0073, 0x003B, 0x003C, 0x003C])                 # ID, start, end, end  
        rom.write_int32s(0x02E8E91C, [0x00000013, 0x0000000C])                   # Textbox, Count
        rom.write_int16s(None, [0x0017, 0x0000, 0x0010, 0x0002, 0x088B, 0xFFFF]) # ID, start, end, type, alt1, alt2        
        rom.write_int16s(None, [0x00D4, 0x0011, 0x0020, 0x0000, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
    
        # Speed learning Saria's Song
        rom.write_int32(0x020B1734, 0x0000003C)                                  # Header: frame_count
        rom.write_int32s(0x20B1DA8, [0x00000013, 0x0000000C])                    # Textbox, Count
        rom.write_int16s(None, [0x0015, 0x0000, 0x0010, 0x0002, 0x088B, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int16s(None, [0x00D1, 0x0011, 0x0020, 0x0000, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int32s(0x020B19C0, [0x0000000A, 0x00000006])                   # Link, Count
        rom.write_int16s(0x020B19C8, [0x0011, 0x0000, 0x0010, 0x0000])           # Action, start, end, ????
        rom.write_int16s(0x020B19F8, [0x003E, 0x0011, 0x0020, 0x0000])           # Action, start, end, ????
        rom.write_int32s(None,         [0x80000000,                              # ???
                                         0x00000000, 0x000001D4, 0xFFFFF731,     # start_XYZ
                                         0x00000000, 0x000001D4, 0xFFFFF712])    # end_XYZ
    
        # Speed learning Epona's Song
        rom.write_int32s(0x029BEF60, [0x000003E8, 0x00000001])                   # Terminator Execution
        rom.write_int16s(None, [0x005E, 0x000A, 0x000B, 0x000B])                 # ID, start, end, end         
        rom.write_int32s(0x029BECB0, [0x00000013, 0x00000002])                   # Textbox, Count
        rom.write_int16s(None, [0x00D2, 0x0000, 0x0009, 0x0000, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int16s(None, [0xFFFF, 0x000A, 0x003C, 0xFFFF, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
    
        # Speed learning Song of Time
        rom.write_int32s(0x0252FB98, [0x000003E8, 0x00000001])                   # Terminator Execution
        rom.write_int16s(None, [0x0035, 0x003B, 0x003C, 0x003C])                 # ID, start, end, end          
        rom.write_int32s(0x0252FC80, [0x00000013, 0x0000000C])                   # Textbox, Count
        rom.write_int16s(None, [0x0019, 0x0000, 0x0010, 0x0002, 0x088B, 0xFFFF]) # ID, start, end, type, alt1, alt2        
        rom.write_int16s(None, [0x00D5, 0x0011, 0x0020, 0x0000, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int32(0x01FC3B84, 0xFFFFFFFF) # Other Header?: frame_count
    
        # Speed learning Song of Storms
        rom.write_int32(0x03041084, 0x0000000A)                                  # Header: frame_count
        rom.write_int32s(0x03041088, [0x00000013, 0x00000002])                   # Textbox, Count
        rom.write_int16s(None, [0x00D6, 0x0000, 0x0009, 0x0000, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int16s(None, [0xFFFF, 0x00BE, 0x00C8, 0xFFFF, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
    
        # Speed learning Minuet of Forest
        rom.write_int32(0x020AFF84, 0x0000003C)                                  # Header: frame_count
        rom.write_int32s(0x020B0800, [0x00000013, 0x0000000A])                   # Textbox, Count
        rom.write_int16s(None, [0x000F, 0x0000, 0x0010, 0x0002, 0x088B, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int16s(None, [0x0073, 0x0011, 0x0020, 0x0000, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int32s(0x020AFF88, [0x0000000A, 0x00000005])                   # Link, Count
        rom.write_int16s(0x020AFF90, [0x0011, 0x0000, 0x0010, 0x0000])           # Action, start, end, ????
        rom.write_int16s(0x020AFFC1, [0x003E, 0x0011, 0x0020, 0x0000])           # Action, start, end, ????
        rom.write_int32s(0x020B0488, [0x00000056, 0x00000001])                   # Music Change, Count
        rom.write_int16s(None, [0x003F, 0x0021, 0x0022, 0x0000])                 # Action, start, end, ????
        rom.write_int32s(0x020B04C0, [0x0000007C, 0x00000001])                   # Music Fade Out, Count
        rom.write_int16s(None, [0x0004, 0x0000, 0x0000, 0x0000])                 # Action, start, end, ????
    
        # Speed learning Bolero of Fire
        rom.write_int32(0x0224B5D4, 0x0000003C)                                  # Header: frame_count
        rom.write_int32s(0x0224D7E8, [0x00000013, 0x0000000A])                   # Textbox, Count
        rom.write_int16s(None, [0x0010, 0x0000, 0x0010, 0x0002, 0x088B, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int16s(None, [0x0074, 0x0011, 0x0020, 0x0000, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int32s(0x0224B5D8, [0x0000000A, 0x0000000B])                   # Link, Count
        rom.write_int16s(0x0224B5E0, [0x0011, 0x0000, 0x0010, 0x0000])           # Action, start, end, ????
        rom.write_int16s(0x0224B610, [0x003E, 0x0011, 0x0020, 0x0000])           # Action, start, end, ????
        rom.write_int32s(0x0224B7F0, [0x0000002F, 0x0000000E])                   # Sheik, Count
        rom.write_int16s(0x0224B7F8, [0x0000])                                   # Action
        rom.write_int16s(0x0224B828, [0x0000])                                   # Action
        rom.write_int16s(0x0224B858, [0x0000])                                   # Action
        rom.write_int16s(0x0224B888, [0x0000])                                   # Action
    
        # Speed learning Serenade of Water
        rom.write_int32(0x02BEB254, 0x0000003C)                                  # Header: frame_count
        rom.write_int32s(0x02BEC880, [0x00000013, 0x00000010])                   # Textbox, Count
        rom.write_int16s(None, [0x0011, 0x0000, 0x0010, 0x0002, 0x088B, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int16s(None, [0x0075, 0x0011, 0x0020, 0x0000, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int32s(0x02BEB258, [0x0000000A, 0x0000000F])                   # Link, Count
        rom.write_int16s(0x02BEB260, [0x0011, 0x0000, 0x0010, 0x0000])           # Action, start, end, ????
        rom.write_int16s(0x02BEB290, [0x003E, 0x0011, 0x0020, 0x0000])           # Action, start, end, ????
        rom.write_int32s(0x02BEB530, [0x0000002F, 0x00000006])                   # Sheik, Count
        rom.write_int16s(0x02BEB538, [0x0000, 0x0000, 0x018A, 0x0000])           # Action, start, end, ????
        rom.write_int32s(None,         [0x1BBB0000,                              # ???
                                         0xFFFFFB10, 0x8000011A, 0x00000330,     # start_XYZ
                                         0xFFFFFB10, 0x8000011A, 0x00000330])    # end_XYZ
        rom.write_int32s(0x02BEC848, [0x00000056, 0x00000001])                   # Music Change, Count
        rom.write_int16s(None, [0x0059, 0x0021, 0x0022, 0x0000])                 # Action, start, end, ????
    
        # Speed learning Nocturne of Shadow
        rom.write_int32s(0x01FFE458, [0x000003E8, 0x00000001])                   # Other Scene? Terminator Execution
        rom.write_int16s(None, [0x002F, 0x0001, 0x0002, 0x0002])                 # ID, start, end, end  
        rom.write_int32(0x01FFFDF4, 0x0000003C)                                  # Header: frame_count
        rom.write_int32s(0x02000FD8, [0x00000013, 0x0000000E])                   # Textbox, Count
        rom.write_int16s(None, [0x0013, 0x0000, 0x0010, 0x0002, 0x088B, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int16s(None, [0x0077, 0x0011, 0x0020, 0x0000, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int32s(0x02000128, [0x000003E8, 0x00000001])                   # Terminator Execution
        rom.write_int16s(None, [0x0032, 0x003A, 0x003B, 0x003B])                 # ID, start, end, end  
    
        # Speed learning Requiem of Spirit
        rom.write_bytes(0x021A072C, [0x0F, 0x22])                                # Change time of day to A60C instead of 8000
        rom.write_int32(0x0218AF14, 0x0000003C)                                  # Header: frame_count
        rom.write_int32s(0x0218C574, [0x00000013, 0x00000008])                   # Textbox, Count
        rom.write_int16s(None, [0x0012, 0x0000, 0x0010, 0x0002, 0x088B, 0xFFFF]) # ID, start, end, type, alt1, alt2       
        rom.write_int16s(None, [0x0076, 0x0011, 0x0020, 0x0000, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int32s(0x0218B478, [0x000003E8, 0x00000001])                   # Terminator Execution
        rom.write_int16s(None, [0x0030, 0x003A, 0x003B, 0x003B])                 # ID, start, end, end  
        rom.write_int32s(0x0218AF18, [0x0000000A, 0x0000000B])                   # Link, Count
        rom.write_int16s(0x0218AF20, [0x0011, 0x0000, 0x0010, 0x0000])           # Action, start, end, ????
        rom.write_int32s(None,         [0x40000000,                              # ???
                                         0xFFFFFAF9, 0x00000008, 0x00000001,     # start_XYZ
                                         0xFFFFFAF9, 0x00000008, 0x00000001,     # end_XYZ
                                         0x0F671408, 0x00000000, 0x00000001])    # normal_XYZ
        rom.write_int16s(0x0218AF50, [0x003E, 0x0011, 0x0020, 0x0000])           # Action, start, end, ????
    
        # Speed learning Prelude of Light
        rom.write_int32(0x0252FD24, 0x0000003C)                                  # Header: frame_count
        rom.write_int32s(0x02531320, [0x00000013, 0x0000000E])                   # Textbox, Count
        rom.write_int16s(None, [0x0014, 0x0000, 0x0010, 0x0002, 0x088B, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int16s(None, [0x0078, 0x0011, 0x0020, 0x0000, 0xFFFF, 0xFFFF]) # ID, start, end, type, alt1, alt2
        rom.write_int32s(0x0252FF10, [0x0000002F, 0x00000009])                   # Sheik, Count
        rom.write_int16s(0x0252FF18, [0x0006, 0x0000, 0x0000, 0x0000])           # Action, start, end, ????
        rom.write_int32s(0x025313D0, [0x00000056, 0x00000001])                   # Music Change, Count
        rom.write_int16s(None, [0x003B, 0x0021, 0x0022, 0x0000])                 # Action, start, end, ????
    
    #Fix backwalk issue for Fairy Fountains
    rom.write_bytes(0xC8A5C4, [0x10, 0x00, 0x00, 0x2F]) # Branch to end of funtion
    rom.write_bytes(0xC8A5C8, [0xAE, 0x00, 0x00, 0x28]) # Keep fairy still
    rom.write_bytes(0xC8A684, [0xA2, 0x0C, 0x00, 0xB4]) # Rotate fairy under the floor
    rom.write_bytes(0xC8BE84, [0x00, 0x00, 0x00, 0x00]) # 0 out relocation table for jump

    # Speed Magic Meter Great Fairy
    rom.write_bytes(0x2CF7136, [0x00, 0x70])
    rom.write_bytes(0x2CF7144, [0x00, 0x56])
    rom.write_bytes(0x2CF7171, [0x13, 0x00, 0x57])
    rom.write_bytes(0x2CF7299, [0x02, 0x00, 0x00, 0x00, 0x50])
    rom.write_bytes(0x2CF72C9, [0x03, 0x00, 0x51, 0x00, 0x52])
    rom.write_bytes(0x2CF72F9, [0x04, 0x00, 0x53, 0x00, 0x54])
    rom.write_bytes(0x2CF7329, [0x13, 0x00, 0x55, 0x00, 0x56])
    rom.write_bytes(0x2CF7359, [0x0A, 0x00, 0x57, 0x00, 0x59])
    rom.write_bytes(0x2CF7389, [0x07, 0x00, 0x5A, 0x00, 0x5B])
    rom.write_bytes(0x2CF73B9, [0x0D, 0x00, 0x5C, 0x00, 0x5D])
    rom.write_bytes(0x2CF8344, [0x00, 0x56])
    rom.write_bytes(0x2CF834C, [0x00, 0xDD, 0x00, 0x57, 0x00, 0x59])
    rom.write_bytes(0x2CF83AA, [0x00, 0x56, 0x00, 0x57])
    
    # Speed Double Magic Meter Great Fairy
    rom.write_bytes(0x2CF83E6, [0x00, 0x70])
    rom.write_bytes(0x2CF83F4, [0x00, 0x56])
    rom.write_bytes(0x2CF8421, [0x13, 0x00, 0x57])
    rom.write_bytes(0x2CF8549, [0x02, 0x00, 0x00, 0x00, 0x50])
    rom.write_bytes(0x2CF8579, [0x03, 0x00, 0x51, 0x00, 0x52])
    rom.write_bytes(0x2CF85A9, [0x05, 0x00, 0x53, 0x00, 0x54])
    rom.write_bytes(0x2CF85D9, [0x14, 0x00, 0x55, 0x00, 0x56])
    rom.write_bytes(0x2CF8609, [0x0B, 0x00, 0x57, 0x00, 0x59])
    rom.write_bytes(0x2CF8639, [0x07, 0x00, 0x5A, 0x00, 0x5B])
    rom.write_bytes(0x2CF8669, [0x0D, 0x00, 0x5C, 0x00, 0x5D])
    rom.write_bytes(0x2CF877C, [0x00, 0x56])
    rom.write_bytes(0x2CF8784, [0x00, 0xE4, 0x00, 0x57, 0x00, 0x59])
    rom.write_bytes(0x2CF87E2, [0x00, 0x56, 0x00, 0x57])

    # Speed Double Defense Great Fairy
    rom.write_bytes(0x2CF95D6, [0x00, 0x60])
    rom.write_bytes(0x2CF95E4, [0x00, 0x4A])
    rom.write_bytes(0x2CF9611, [0x13, 0x00, 0x4B])
    rom.write_bytes(0x2CF9739, [0x02, 0x00, 0x00, 0x00, 0x40])
    rom.write_bytes(0x2CF9769, [0x03, 0x00, 0x41, 0x00, 0x42])
    rom.write_bytes(0x2CF9799, [0x06, 0x00, 0x43, 0x00, 0x44])
    rom.write_bytes(0x2CF97C9, [0x15, 0x00, 0x45, 0x00, 0x46])
    rom.write_bytes(0x2CF97F9, [0x0C, 0x00, 0x47, 0x00, 0x49])
    rom.write_bytes(0x2CF9829, [0x12, 0x00, 0x4A, 0x00, 0x54])
    rom.write_bytes(0x2CF9859, [0x07, 0x00, 0x55, 0x00, 0x56])
    rom.write_bytes(0x2CF9889, [0x0D, 0x00, 0x57, 0x00, 0x58])
    rom.write_bytes(0x2CF999C, [0x00, 0x4A])
    rom.write_bytes(0x2CF99A4, [0x00, 0xE5, 0x00, 0x4B, 0x00, 0x53])
    rom.write_bytes(0x2CF9A02, [0x00, 0x4A, 0x00, 0x4B])

    # Speed Zora Fountain Great Fairy
    rom.write_bytes(0x2D20166, [0x00, 0x50])
    rom.write_bytes(0x2D20174, [0x00, 0x45])
    rom.write_bytes(0x2D201A1, [0x13, 0x00, 0x46])
    rom.write_bytes(0x2D20299, [0x02, 0x00, 0x00, 0x00, 0x40])
    rom.write_bytes(0x2D202C9, [0x03, 0x00, 0x41, 0x00, 0x42])
    rom.write_bytes(0x2D202F9, [0x04, 0x00, 0x43, 0x00, 0x44])
    rom.write_bytes(0x2D20329, [0x0E, 0x00, 0x45, 0x00, 0x46])
    rom.write_bytes(0x2D20359, [0x11, 0x00, 0x47, 0x00, 0x4A])
    rom.write_bytes(0x2D20389, [0x0D, 0x00, 0x4B, 0x00, 0x4C])
    rom.write_bytes(0x2D20552, [0x00, 0x45, 0x00, 0x46])
    rom.write_bytes(0x2D2058C, [0x00, 0x45])
    rom.write_bytes(0x2D20595, [0xAE, 0x00, 0x46, 0x00, 0x48])

    # Speed Castle Great Fairy
    rom.write_bytes(0x2D21026, [0x00, 0x50])
    rom.write_bytes(0x2D21034, [0x00, 0x45])
    rom.write_bytes(0x2D21061, [0x13, 0x00, 0x46])
    rom.write_bytes(0x2D21159, [0x02, 0x00, 0x00, 0x00, 0x40])
    rom.write_bytes(0x2D21189, [0x03, 0x00, 0x41, 0x00, 0x42])
    rom.write_bytes(0x2D211B9, [0x05, 0x00, 0x43, 0x00, 0x44])
    rom.write_bytes(0x2D211E9, [0x0F, 0x00, 0x45, 0x00, 0x46])
    rom.write_bytes(0x2D21219, [0x11, 0x00, 0x47, 0x00, 0x4A])
    rom.write_bytes(0x2D21249, [0x0D, 0x00, 0x4B, 0x00, 0x4C])
    rom.write_bytes(0x2D21E3A, [0x00, 0x45, 0x00, 0x46])
    rom.write_bytes(0x2D21E74, [0x00, 0x45])
    rom.write_bytes(0x2D21E7D, [0xAD, 0x00, 0x46, 0x00, 0x48])

    # Speed Colossus Great Fairy
    rom.write_bytes(0x2D21F46, [0x00, 0x50])
    rom.write_bytes(0x2D21F54, [0x00, 0x45])
    rom.write_bytes(0x2D21F81, [0x13, 0x00, 0x46])
    rom.write_bytes(0x2D22079, [0x02, 0x00, 0x00, 0x00, 0x40])
    rom.write_bytes(0x2D220A9, [0x03, 0x00, 0x41, 0x00, 0x42])
    rom.write_bytes(0x2D220D9, [0x06, 0x00, 0x43, 0x00, 0x44])
    rom.write_bytes(0x2D22109, [0x10, 0x00, 0x45, 0x00, 0x46])
    rom.write_bytes(0x2D22139, [0x11, 0x00, 0x47, 0x00, 0x4A])
    rom.write_bytes(0x2D22169, [0x0D, 0x00, 0x4B, 0x00, 0x4C])
    rom.write_bytes(0x2D22332, [0x00, 0x45, 0x00, 0x46])
    rom.write_bytes(0x2D2236C, [0x00, 0x45])
    rom.write_bytes(0x2D22375, [0xAF, 0x00, 0x46, 0x00, 0x48])

    if world.dungeon_speedup:
        # Speed scene after Deku Tree
        rom.write_bytes(0x2077E20, [0x00, 0x07, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02])
        rom.write_bytes(0x2078A10, [0x00, 0x0E, 0x00, 0x1F, 0x00, 0x20, 0x00, 0x20])
        Block_code = [0x00, 0x80, 0x00, 0x00, 0x00, 0x1E, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 
                      0xFF, 0xFF, 0x00, 0x1E, 0x00, 0x28, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        rom.write_bytes(0x2079570, Block_code)
    
        # Speed scene after Dodongo's Cavern
        rom.write_bytes(0x2221E88, [0x00, 0x0C, 0x00, 0x3B, 0x00, 0x3C, 0x00, 0x3C])
        rom.write_bytes(0x2223308, [0x00, 0x81, 0x00, 0x00, 0x00, 0x3A, 0x00, 0x00])
    
        # Speed scene after Jabu Jabu's Belly
        rom.write_bytes(0x2113340, [0x00, 0x0D, 0x00, 0x3B, 0x00, 0x3C, 0x00, 0x3C])
        rom.write_bytes(0x2113C18, [0x00, 0x82, 0x00, 0x00, 0x00, 0x3A, 0x00, 0x00])
        rom.write_bytes(0x21131D0, [0x00, 0x01, 0x00, 0x00, 0x00, 0x3C, 0x00, 0x3C])
    
        # Speed scene after Forest Temple
        rom.write_bytes(0xD4ED68, [0x00, 0x45, 0x00, 0x3B, 0x00, 0x3C, 0x00, 0x3C])
        rom.write_bytes(0xD4ED78, [0x00, 0x3E, 0x00, 0x00, 0x00, 0x3A, 0x00, 0x00])
        rom.write_bytes(0x207B9D4, [0xFF, 0xFF, 0xFF, 0xFF])
    
        # Speed scene after Fire Temple
        rom.write_bytes(0x2001848, [0x00, 0x1E, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02])
        rom.write_bytes(0xD100B4, [0x00, 0x62, 0x00, 0x3B, 0x00, 0x3C, 0x00, 0x3C])
        rom.write_bytes(0xD10134, [0x00, 0x3C, 0x00, 0x00, 0x00, 0x3A, 0x00, 0x00])
    
        # Speed scene after Water Temple
        rom.write_bytes(0xD5A458, [0x00, 0x15, 0x00, 0x3B, 0x00, 0x3C, 0x00, 0x3C])
        rom.write_bytes(0xD5A3A8, [0x00, 0x3D, 0x00, 0x00, 0x00, 0x3A, 0x00, 0x00])
        rom.write_bytes(0x20D0D20, [0x00, 0x29, 0x00, 0xC7, 0x00, 0xC8, 0x00, 0xC8])
    
        # Speed scene after Shadow Temple
        rom.write_bytes(0xD13EC8, [0x00, 0x61, 0x00, 0x3B, 0x00, 0x3C, 0x00, 0x3C])
        rom.write_bytes(0xD13E18, [0x00, 0x41, 0x00, 0x00, 0x00, 0x3A, 0x00, 0x00])
    
        # Speed scene after Spirit Temple
        rom.write_bytes(0xD3A0A8, [0x00, 0x60, 0x00, 0x3B, 0x00, 0x3C, 0x00, 0x3C])
        rom.write_bytes(0xD39FF0, [0x00, 0x3F, 0x00, 0x00, 0x00, 0x3A, 0x00, 0x00])

    if world.knuckle_cs:
        # Speed Nabooru defeat scene
        rom.write_bytes(0x2F5AF84, [0x00, 0x00, 0x00, 0x05])
        rom.write_bytes(0x2F5C7DA, [0x00, 0x01, 0x00, 0x02])
        rom.write_bytes(0x2F5C7A2, [0x00, 0x03, 0x00, 0x04])
        rom.write_byte(0x2F5B369, 0x09)
        rom.write_byte(0x2F5B491, 0x04)
        rom.write_byte(0x2F5B559, 0x04)
        rom.write_byte(0x2F5B621, 0x04)
        rom.write_byte(0x2F5B761, 0x07)

    # Speed scene with all medallions
    rom.write_bytes(0x2512680, [0x00, 0x74, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02])

    # Speed collapse of Ganon's Tower
    rom.write_bytes(0x33FB328, [0x00, 0x76, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02])

    # Speed Phantom Ganon defeat scene
    rom.write_bytes(0xC944D8, [0x00, 0x00, 0x00, 0x00])
    rom.write_bytes(0xC94548, [0x00, 0x00, 0x00, 0x00])
    rom.write_bytes(0xC94730, [0x00, 0x00, 0x00, 0x00])
    rom.write_bytes(0xC945A8, [0x00, 0x00, 0x00, 0x00])
    rom.write_bytes(0xC94594, [0x00, 0x00, 0x00, 0x00])

    # Speed Twinrova defeat scene
    rom.write_bytes(0xD678CC, [0x24, 0x01, 0x03, 0xA2, 0xA6, 0x01, 0x01, 0x42])
    rom.write_bytes(0xD67BA4, [0x10, 0x00])
    
    # Ganondorf battle end
    rom.write_byte(0xD82047, 0x09)

    # Zelda descends
    rom.write_byte(0xD82AB3, 0x66)
    rom.write_byte(0xD82FAF, 0x65)
    rom.write_bytes(0xD82D2E, [0x04, 0x1F])
    rom.write_bytes(0xD83142, [0x00, 0x6B])
    rom.write_bytes(0xD82DD8, [0x00, 0x00, 0x00, 0x00])
    rom.write_bytes(0xD82ED4, [0x00, 0x00, 0x00, 0x00])
    rom.write_byte(0xD82FDF, 0x33)

    # After tower collapse
    rom.write_byte(0xE82E0F, 0x04)

    # Ganon intro
    rom.write_bytes(0xE83D28, [0x00, 0x00, 0x00, 0x00])
    rom.write_bytes(0xE83B5C, [0x00, 0x00, 0x00, 0x00])
    rom.write_bytes(0xE84C80, [0x10, 0x00])
    
    # Speed completion of the trials in Ganon's Castle
    rom.write_bytes(0x31A8090, [0x00, 0x6B, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02]) #Forest
    rom.write_bytes(0x31A9E00, [0x00, 0x6E, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02]) #Fire
    rom.write_bytes(0x31A8B18, [0x00, 0x6C, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02]) #Water
    rom.write_bytes(0x31A9430, [0x00, 0x6D, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02]) #Shadow
    rom.write_bytes(0x31AB200, [0x00, 0x70, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02]) #Spirit
    rom.write_bytes(0x31AA830, [0x00, 0x6F, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02]) #Light

    #Speed Silver Gaunts cs to avoid crash
    rom.write_bytes(0x0218D51A, [0x00, 0x00, 0x00, 0x00]) #Set start and end frame of terminate command to beginning of cs

    # Speed obtaining Fairy Ocarina
    rom.write_bytes(0x2151230, [0x00, 0x72, 0x00, 0x3C, 0x00, 0x3D, 0x00, 0x3D])
    Block_code = [0x00, 0x4A, 0x00, 0x00, 0x00, 0x3A, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF,
                  0xFF, 0xFF, 0x00, 0x3C, 0x00, 0x81, 0xFF, 0xFF]
    rom.write_bytes(0x2151240, Block_code)
    rom.write_bytes(0x2150E20, [0xFF, 0xFF, 0xFA, 0x4C])

    # Speed Zelda Light Arrow cutscene
    rom.write_bytes(0x2531B40, [0x00, 0x20, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02]) # Load into flashback ASAP
    rom.write_bytes(0x01FC28C8, [0x00, 0x00, 0x03, 0xE8, 0x00, 0x00, 0x00, 0x01, 0x00, 0x28, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) # Load into tot ASAP
    rom.write_bytes(0x2532FBC, [0x00, 0x75])
    rom.write_bytes(0x2532FEA, [0x00, 0x75, 0x00, 0x80])  
    rom.write_byte(0x2533115, 0x05)
    rom.write_bytes(0x2533141, [0x06, 0x00, 0x06, 0x00, 0x10])
    rom.write_bytes(0x2533171, [0x0F, 0x00, 0x11, 0x00, 0x40])
    rom.write_bytes(0x25331A1, [0x07, 0x00, 0x41, 0x00, 0x65])
    rom.write_bytes(0x2533642, [0x00, 0x50])
    rom.write_byte(0x253389D, 0x74)
    rom.write_bytes(0x25338A4, [0x00, 0x72, 0x00, 0x75, 0x00, 0x79])
    rom.write_bytes(0x25338BC, [0xFF, 0xFF])
    rom.write_bytes(0x25338C2, [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
    rom.write_bytes(0x25339C2, [0x00, 0x75, 0x00, 0x76])
    rom.write_bytes(0x2533830, [0x00, 0x31, 0x00, 0x81, 0x00, 0x82, 0x00, 0x82])
    
    # Speed Bridge of Light cutscene
    rom.write_bytes(0x292D644, [0x00, 0x00, 0x00, 0xA0])
    rom.write_bytes(0x292D680, [0x00, 0x02, 0x00, 0x0A, 0x00, 0x6C, 0x00, 0x00])
    rom.write_bytes(0x292D6E8, [0x00, 0x27])
    rom.write_bytes(0x292D718, [0x00, 0x32])
    rom.write_bytes(0x292D810, [0x00, 0x02, 0x00, 0x3C])
    rom.write_bytes(0x292D924, [0xFF, 0xFF, 0x00, 0x14, 0x00, 0x96, 0xFF, 0xFF])

    #Speed Pushing of All Pushable Objects
    rom.write_bytes(0xDD2B86, [0x40, 0x80])             #block speed
    rom.write_bytes(0xDD2D26, [0x00, 0x03])             #block delay
    rom.write_bytes(0xDD9682, [0x40, 0x80])             #milk crate speed
    rom.write_bytes(0xDD981E, [0x00, 0x03])             #milk crate delay
    rom.write_bytes(0xCE1BD0, [0x40, 0x80, 0x00, 0x00]) #amy puzzle speed
    rom.write_bytes(0xCE0F0E, [0x00, 0x03])             #amy puzzle delay
    rom.write_bytes(0xC77CA8, [0x40, 0x80, 0x00, 0x00]) #fire block speed
    rom.write_bytes(0xC770C2, [0x00, 0x01])             #fire block delay
    rom.write_bytes(0xCC5DBC, [0x29, 0xE1, 0x00, 0x01]) #forest basement puzzle delay
    rom.write_bytes(0xDBCF70, [0x2B, 0x01, 0x00, 0x00]) #spirit cobra mirror startup
    rom.write_bytes(0xDBCF70, [0x2B, 0x01, 0x00, 0x01]) #spirit cobra mirror delay
    rom.write_bytes(0xDBA230, [0x28, 0x41, 0x00, 0x19]) #truth spinner speed
    rom.write_bytes(0xDBA3A4, [0x24, 0x18, 0x00, 0x00]) #truth spinner delay

    #Speed Deku Seed Upgrade Scrub Cutscene
    rom.write_bytes(0xECA900, [0x24, 0x03, 0xC0, 0x00]) #scrub angle
    rom.write_bytes(0xECAE90, [0x27, 0x18, 0xFD, 0x04]) #skip straight to giving item
    rom.write_bytes(0xECB618, [0x25, 0x6B, 0x00, 0xD4]) #skip straight to digging back in
    rom.write_bytes(0xECAE70, [0x00, 0x00, 0x00, 0x00]) #never initialize cs camera
    rom.write_bytes(0xE5972C, [0x24, 0x08, 0x00, 0x01]) #timer set to 1 frame for giving item

    if world.no_owls:
        # Remove remaining owls
        rom.write_bytes(0x1FE30CE, [0x01, 0x4B])
        rom.write_bytes(0x1FE30DE, [0x01, 0x4B])
        rom.write_bytes(0x1FE30EE, [0x01, 0x4B])
        rom.write_bytes(0x205909E, [0x00, 0x3F])
        rom.write_byte(0x2059094, 0x80)

    # Darunia won't dance
    rom.write_bytes(0x22769E4, [0xFF, 0xFF, 0xFF, 0xFF])

    # King Zora moves quickly
    rom.write_bytes(0xE56924, [0x00, 0x00, 0x00, 0x00])

    # Speed Jabu Jabu swallowing Link
    rom.write_bytes(0xCA0784, [0x00, 0x18, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02])

    # Ruto no longer points to Zora Sapphire
    rom.write_bytes(0xD03BAC, [0xFF, 0xFF, 0xFF, 0xFF])

    # Ruto never disappears from Jabu Jabu's Belly
    rom.write_byte(0xD01EA3, 0x00)

    #Move fire/forest temple switches down 1 unit to make it easier to press
    rom.write_bytes(0x24860A8, [0xFC, 0xF4]) #forest basement 1
    rom.write_bytes(0x24860C8, [0xFC, 0xF4]) #forest basement 2
    rom.write_bytes(0x24860E8, [0xFC, 0xF4]) #forest basement 3
    rom.write_bytes(0x236C148, [0x11, 0x93]) #fire hammer room

    # Speed up Epona race start
    rom.write_bytes(0x29BE984, [0x00, 0x00, 0x00, 0x02])
    rom.write_bytes(0x29BE9CA, [0x00, 0x01, 0x00, 0x02])

    # Speed up Epona escape
    rom.write_bytes(0x1FC8B36, [0x00, 0x2A])

    # Speed up draining the well
    rom.write_bytes(0xE0A010, [0x00, 0x2A, 0x00, 0x01, 0x00, 0x02, 0x00, 0x02])
    rom.write_bytes(0x2001110, [0x00, 0x2B, 0x00, 0xB7, 0x00, 0xB8, 0x00, 0xB8])

    # Speed up opening the royal tomb for both child and adult
    rom.write_bytes(0x2025026, [0x00, 0x01])
    rom.write_bytes(0x2023C86, [0x00, 0x01])
    rom.write_byte(0x2025159, 0x02)
    rom.write_byte(0x2023E19, 0x02)

    #Speed opening of Door of Time
    rom.write_bytes(0xE0A176, [0x00, 0x02])
    rom.write_bytes(0xE0A35A, [0x00, 0x01, 0x00, 0x02])

    # Darunia sets an event flag and checks for it
    Block_code = [0x24, 0x19, 0x00, 0x40, 0x8F, 0x09, 0xB4, 0xA8, 0x01, 0x39, 0x40, 0x24,
                  0x01, 0x39, 0xC8, 0x25, 0xAF, 0x19, 0xB4, 0xA8, 0x24, 0x09, 0x00, 0x06]
    rom.write_bytes(0xCF1AB8, Block_code)

    # Fix Shadow Temple to check for different rewards for scene
    rom.write_bytes(0xCA3F32, [0x00, 0x00, 0x25, 0x4A, 0x00, 0x10])

    # Fix Spirit Temple to check for different rewards for scene
    rom.write_bytes(0xCA3EA2, [0x00, 0x00, 0x25, 0x4A, 0x00, 0x08])

    # Make the check for BGS 1 full day
    rom.write_bytes(0xED446C, [0x28, 0x41, 0x00, 0x01]) #day check for claim check
    rom.write_bytes(0xED4494, [0x28, 0x41, 0x00, 0x01]) #day check for dialogue
    
    # Fixed reward order for Bombchu Bowling
    rom.write_bytes(0xE2E694, [0x80, 0xAA, 0xE2, 0x64]) #item 1 = hp
    rom.write_bytes(0xE2E698, [0x80, 0xAA, 0xE2, 0x88]) #item 2 = bombs
    rom.write_bytes(0xE2E69C, [0x80, 0xAA, 0xE2, 0x28]) #item 3 = bombbag
    rom.write_bytes(0xE2E6A0, [0x80, 0xAA, 0xE2, 0x4C]) #item 4 = rupee
    rom.write_bytes(0xE2E6A4, [0x80, 0xAA, 0xE2, 0x58]) #item 5 = chus
    rom.write_bytes(0xE2D440, [0x24, 0x19, 0x00, 0x00]) #start at item 1
   
    # Speed Dampe digging
    rom.write_bytes(0x9532F8, [0x08, 0x08, 0x08, 0x59]) #text
    rom.write_bytes(0xCC4024, [0x00, 0x00, 0x00, 0x00]) #first try

    #Give hp after first ocarina minigame round
    rom.write_bytes(0xDF2204, [0x24, 0x03, 0x00, 0x02]) 
    rom.write_byte(0xDF2647, 0x3E)
    
    # Make item descriptions into a single box
    Short_item_descriptions = [0x92EC84, 0x92F9E3, 0x92F2B4, 0x92F37A, 0x92F513, 0x92F5C6, 0x92E93B, 0x92EA12]
    for address in Short_item_descriptions:
        rom.write_byte(address,0x02)

    # will be populated with data to be written to initial save
    # see initial_save.asm and config.asm for more details on specifics
    # or just use the following functions to add an entry to the table
    initial_save_table = []

    # will set the bits of value to the offset in the save (or'ing them with what is already there)
    def write_bits_to_save(offset, value, filter=None):
        nonlocal initial_save_table

        if filter and not filter(value):
            return

        initial_save_table += [(offset & 0xFF00) >> 8, offset & 0xFF, 0x00, value]
        
    # will overwrite the byte at offset with the given value
    def write_byte_to_save(offset, value, filter=None):
        nonlocal initial_save_table

        if filter and not filter(value):
            return

        initial_save_table += [(offset & 0xFF00) >> 8, offset & 0xFF, 0x01, value]

    # will overwrite the byte at offset with the given value
    def write_bytes_to_save(offset, bytes, filter=None):
        for i, value in enumerate(bytes):
            write_byte_to_save(offset + i, value, filter)

    # will overwrite the byte at offset with the given value
    def write_save_table(rom):
        nonlocal initial_save_table

        table_len = len(initial_save_table)
        if table_len > 0x400:
            raise Exception("The Initial Save Table has exceeded it's maximum capacity: 0x%03X/0x400" % table_len)
        rom.write_bytes(0x3481800, initial_save_table)

    # Initial Save Data

    #set initial time of day dynamically according to intro cs
    tod = 0x6AAB

    if world.skip_intro:
        tod += 0x1555
    if world.skip_field:
        tod += 0xC94
    if world.skip_castle:
        tod += 0x492

    byte1 = (tod & 0xFF00) >> 8
    byte2 = (tod & 0xFF)
    timeofday = [byte1, byte2]

    write_bytes_to_save(0x0C, timeofday) #write sum to time of day

    if world.forest_elevator:
        write_bits_to_save(0x00D4 + 0x03 * 0x1C + 0x04 + 0x0, 0x08) # Forest Temple switch flag (Poe Sisters cutscene)

    if world.no_owls:
        write_bits_to_save(0x00D4 + 0x51 * 0x1C + 0x04 + 0x2, 0x08) # Hyrule Field switch flag (Owl)
        write_bits_to_save(0x00D4 + 0x56 * 0x1C + 0x04 + 0x2, 0x40) # Sacred Forest Meadow switch flag (Owl)
        write_bits_to_save(0x00D4 + 0x5B * 0x1C + 0x04 + 0x2, 0x01) # Lost Woods switch flag (Owl)
        write_bits_to_save(0x00D4 + 0x5B * 0x1C + 0x04 + 0x3, 0x80) # Lost Woods switch flag (Owl)
        write_bits_to_save(0x00D4 + 0x5C * 0x1C + 0x04 + 0x0, 0x80) # Desert Colossus switch flag (Owl)
        write_bits_to_save(0x00D4 + 0x5F * 0x1C + 0x04 + 0x3, 0x20) # Hyrule Castle switch flag (Owl)
        write_bits_to_save(0x0EE0, 0x80) # "Spoke to Kaepora Gaebora by Lost Woods"

    write_bits_to_save(0x0ED4, 0x10) # "Met Deku Tree"
    write_bits_to_save(0x0ED5, 0x20) # "Deku Tree Opened Mouth"
    write_bits_to_save(0x0ED6, 0x08) # "Rented Horse From Ingo"
    write_bits_to_save(0x0EDA, 0x08) # "Began Nabooru Battle"
    write_bits_to_save(0x0EDC, 0x80) # "Entered the Master Sword Chamber"
    write_bits_to_save(0x0EDD, 0x20) # "Pulled Master Sword from Pedestal"
    write_bits_to_save(0x00D4 + 0x05 * 0x1C + 0x04 + 0x1, 0x01) # Water temple switch flag (Ruto)

    write_bits_to_save(0x0EE7, 0x20) # "Nabooru Captured by Twinrova"
    write_bits_to_save(0x0EE7, 0x10) # "Spoke to Nabooru in Spirit Temple"
    write_bits_to_save(0x0EED, 0x20) # "Sheik, Spawned at Master Sword Pedestal as Adult"
    write_bits_to_save(0x0EED, 0x80) # "Watched Ganon's Tower Collapse / Caught by Gerudo"
    write_bits_to_save(0x0EED, 0x01) # "Nabooru Ordered to Fight by Twinrova"
    write_bits_to_save(0x0EF9, 0x01) # "Greeted by Saria"
    write_bits_to_save(0x0F0A, 0x04) # "Spoke to Ingo Once as Adult"

    write_bits_to_save(0x0ED7, 0x01) # "Spoke to Child Malon at Castle or Market"
    write_bits_to_save(0x0ED7, 0x20) # "Spoke to Child Malon at Ranch"
    write_bits_to_save(0x0ED7, 0x40) # "Invited to Sing With Child Malon"
    write_bits_to_save(0x0F09, 0x10) # "Met Child Malon at Castle or Market"
    write_bits_to_save(0x0F09, 0x20) # "Child Malon Said Epona Was Scared of You"

    write_bits_to_save(0x0F21, 0x04) # "Ruto in JJ (M3) Talk First Time"
    write_bits_to_save(0x0F21, 0x02) # "Ruto in JJ (M2) Meet Ruto"

    write_bits_to_save(0x0EE2, 0x01) # "Began Ganondorf Battle"
    #write_bits_to_save(0x0EE3, 0x80) # "Began Bongo Bongo Battle"
    write_bits_to_save(0x0EE3, 0x40) # "Began Barinade Battle"
    write_bits_to_save(0x0EE3, 0x20) # "Began Twinrova Battle"
    write_bits_to_save(0x0EE3, 0x10) # "Began Morpha Battle"
    write_bits_to_save(0x0EE3, 0x08) # "Began Volvagia Battle"
    write_bits_to_save(0x0EE3, 0x04) # "Began Phantom Ganon Battle"
    write_bits_to_save(0x0EE3, 0x02) # "Began King Dodongo Battle"
    write_bits_to_save(0x0EE3, 0x01) # "Began Gohma Battle"

    #Static Intro CS
    write_bits_to_save(0x0EE9, 0x80) # "Entered Temple of Time"
    write_bits_to_save(0x0EEA, 0x04) # "Entered Ganon's Castle (Exterior)"
    write_bits_to_save(0x0EEB, 0x10) # "Entered Lon Lon Ranch"
    write_bits_to_save(0x0F08, 0x08) # "Entered Hyrule Castle"

    if world.skip_field:
        write_bits_to_save(0x0EE9, 0x01) # "Entered Hyrule Field"

    if world.skip_castle:
        write_bits_to_save(0x0EE9, 0x20) # "Entered Hyrule Castle"

    if world.skip_kak:
        write_bits_to_save(0x0EE9, 0x08) # "Entered Kakariko Village"

    if world.skip_gy:
        write_bits_to_save(0x0EEB, 0x40) # "Entered Graveyard"

    if world.skip_dmt:
        write_bits_to_save(0x0EE9, 0x02) # "Entered Death Mountain Trail"

    if world.skip_gc:
        write_bits_to_save(0x0EE9, 0x40) # "Entered Goron City"

    if world.skip_dmc:
        write_bits_to_save(0x0EEA, 0x02) # "Entered Death Mountain Crater"

    if world.skip_domain:
        write_bits_to_save(0x0EE9, 0x10) # "Entered Zora's Domain"

    if world.skip_fountain:
        write_bits_to_save(0x0EEB, 0x80) # "Entered Zora's Fountain"

    if world.skip_lh:
        write_bits_to_save(0x0EEB, 0x02) # "Entered Lake Hylia"

    if world.skip_gv:
        write_bits_to_save(0x0EEB, 0x04) # "Entered Gerudo Valley"

    if world.skip_gf:
        write_bits_to_save(0x0EEB, 0x08) # "Entered Gerudo's Fortress"

    if world.skip_colossus:
        write_bits_to_save(0x0EEA, 0x01) # "Entered Desert Colossus"

    if world.skip_deku:
        write_bits_to_save(0x0EE8, 0x01) # "Entered Deku Tree"

    if world.skip_dc:
        write_bits_to_save(0x0EEB, 0x01) # "Entered Dodongo's Cavern"

    if world.skip_jabu:
        write_bits_to_save(0x0EEB, 0x20) # "Entered Jabu-Jabu's Belly"


    # Make the Kakariko Gate not open with the MS - not sure if i wanna keep it like this
    rom.write_int32(0xDD3538, 0x34190000)
    if not world.open_kakariko:
        rom.write_int32(0xDD3538, 0x34190000) # li t9, 0

    # Move carpenter starting position
    rom.write_bytes(0x1FF93A4, [0x01, 0x8D, 0x00, 0x11, 0x01, 0x6C, 0xFF, 0x92, 0x00, 0x00, 0x01, 0x78, 0xFF, 0x2E, 0x00, 0x00, 0x00, 0x03, 0xFD, 0x2B, 0x00, 0xC8, 0xFF, 0xF9, 0xFD, 0x03, 0x00, 0xC8, 0xFF, 0xA9, 0xFD, 0x5D, 0x00, 0xC8, 0xFE, 0x5F]) # re order the carpenter's path
    rom.write_byte(0x1FF93D0, 0x06) # set the path points to 6
    rom.write_bytes(0x20160B6, [0x01, 0x8D, 0x00, 0x11, 0x01, 0x6C]) # set the carpenter's start position
    
    # Make all chest opening animations fast
    if world.fast_chests:
        rom.write_int32(0xBDA2E8, 0x240AFFFF) # addiu   t2, r0, -1
                               # replaces # lb      t2, 0x0002 (t1)

    if world.quest == 'master':
        for i in world.dungeon_mq:
            world.dungeon_mq[i] = True

    # patch mq scenes
    mq_scenes = []
    if world.dungeon_mq['DT']:
        mq_scenes.append(0)
    if world.dungeon_mq['DC']:
        mq_scenes.append(1)
    if world.dungeon_mq['JB']:
        mq_scenes.append(2)
    if world.dungeon_mq['FoT']:
        mq_scenes.append(3)
    if world.dungeon_mq['FiT']:
        mq_scenes.append(4)
    if world.dungeon_mq['WT']:
        mq_scenes.append(5)
    if world.dungeon_mq['SpT']:
        mq_scenes.append(6)
    if world.dungeon_mq['ShT']:
        mq_scenes.append(7)
    if world.dungeon_mq['BW']:
        mq_scenes.append(8)
    if world.dungeon_mq['IC']:
        mq_scenes.append(9)
    # Scene 10 has no layout changes, so it doesn't need to be patched
    if world.dungeon_mq['GTG']:
        mq_scenes.append(11)
    if world.dungeon_mq['GC']:
        mq_scenes.append(13)

    patch_files(rom, mq_scenes)

    ### Load Shop File
    # Move shop actor file to free space
    shop_item_file = File({
            'Name':'En_GirlA',
            'Start':'00C004E0',
            'End':'00C02E00',
            'RemapStart':'03485000',
        })
    shop_item_file.relocate(rom)

    # Increase the shop item table size
    shop_item_vram_start = rom.read_int32(0x00B5E490 + (0x20 * 4) + 0x08)
    insert_space(rom, shop_item_file, shop_item_vram_start, 1, 0x3C + (0x20 * 50), 0x20 * 50)

    # Add relocation entries for shop item table
    new_relocations = []
    for i in range(50, 100):
        new_relocations.append(shop_item_file.start + 0x1DEC + (i * 0x20) + 0x04)
        new_relocations.append(shop_item_file.start + 0x1DEC + (i * 0x20) + 0x14)
        new_relocations.append(shop_item_file.start + 0x1DEC + (i * 0x20) + 0x1C)
    add_relocations(rom, shop_item_file, new_relocations)

    # update actor table
    rom.write_int32s(0x00B5E490 + (0x20 * 4), 
        [shop_item_file.start, 
        shop_item_file.end, 
        shop_item_vram_start, 
        shop_item_vram_start + (shop_item_file.end - shop_item_file.start)])

    # Update DMA Table
    update_dmadata(rom, shop_item_file)

    # Create 2nd Bazaar Room
    bazaar_room_file = File({
            'Name':'shop1_room_1',
            'Start':'028E4000',
            'End':'0290D7B0',
            'RemapStart':'03489000',
        })
    bazaar_room_file.dma_key = 0x03472000
    bazaar_room_file.relocate(rom)
    # Update DMA Table
    update_dmadata(rom, bazaar_room_file)

    # Add new Bazaar Room to Bazaar Scene
    rom.write_int32s(0x28E3030, [0x00010000, 0x02000058]) #reduce position list size
    rom.write_int32s(0x28E3008, [0x04020000, 0x02000070]) #expand room list size

    rom.write_int32s(0x28E3070, [0x028E4000, 0x0290D7B0, 
                     bazaar_room_file.start, bazaar_room_file.end]) #room list
    rom.write_int16s(0x28E3080, [0x0000, 0x0001]) # entrance list
    rom.write_int16(0x28E4076, 0x0005) # Change shop to Kakariko Bazaar
    #rom.write_int16(0x3489076, 0x0005) # Change shop to Kakariko Bazaar

    # Load Message and Shop Data
    messages = read_messages(rom)
    shop_items = read_shop_items(rom, shop_item_file.start + 0x1DEC)
    remove_unused_messages(messages)

    # Revert Song Get Override Injection
    if not world.shuffle_song_items:
        # general get song
        rom.write_int32(0xAE5DF8, 0x240200FF)
        rom.write_int32(0xAE5E04, 0xAD0F00A4)
        # requiem of spirit
        rom.write_int32s(0xAC9ABC, [0x3C010001, 0x00300821])
        # sun song
        rom.write_int32(0xE09F68, 0x8C6F00A4)
        rom.write_int32(0xE09F74, 0x01CFC024)
        rom.write_int32(0xE09FB0, 0x240F0001)
        # epona
        rom.write_int32(0xD7E77C, 0x8C4900A4)
        rom.write_int32(0xD7E784, 0x8D088C24)
        rom.write_int32s(0xD7E8D4, [0x8DCE8C24, 0x8C4F00A4])
        rom.write_int32s(0xD7E140, [0x8DCE8C24, 0x8C6F00A4])
        rom.write_int32(0xD7EBBC, 0x14410008)
        rom.write_int32(0xD7EC1C, 0x17010010)
        # song of time
        rom.write_int32(0xDB532C, 0x24050003)

    # Set default targeting option to Hold
    if world.default_targeting == 'hold':
        rom.write_byte(0xB71E6D, 0x01)

    # Set OHKO mode
    if world.difficulty == 'ohko':
        rom.write_int32(0xAE80A8, 0xA4A00030) # sh  zero,48(a1)
        rom.write_int32(0xAE80B4, 0x06000003) # bltz s0, +0003

    # give dungeon items the correct messages
    message_patch_for_dungeon_items(messages, shop_items, world)

    # reduce item message lengths
    update_item_messages(messages, world)

    #rova_text = "\x06\x37\x08Oh, OK, Koume.\x09\x0C\x14\x04\x06\x30\x08Kotake\x09 and \x08Koume's\x09\x06\x1C\x08Double\x09 Dynamite \x08Attack!\x09\x0E\x28" 
    #update_message_by_id(messages, 0x605A, rova_text)

    repack_messages(rom, messages)
    write_shop_items(rom, shop_item_file.start + 0x1DEC, shop_items)

    # actually write the save table to rom
    write_save_table(rom)

    # patch music 
    if world.background_music == 'random':
        randomize_music(rom)
    elif world.background_music == 'off':    
        disable_music(rom)

    # re-seed for aesthetic effects. They shouldn't be affected by the generation seed
    random.seed()
    
    # Custom color tunic 
    Tunics = []
    Tunics.append(0x00B6DA38) # Kokiri Tunic
    Tunics.append(0x00B6DA3B) # Goron Tunic
    Tunics.append(0x00B6DA3E) # Zora Tunic
    colorList = get_tunic_colors()
    randomColors = random.choices(colorList, k=3)

    for i in range(len(Tunics)):
        # get the color option
        thisColor = world.tunic_colors[i]
        # handle true random
        randColor = [random.getrandbits(8), random.getrandbits(8), random.getrandbits(8)]
        if thisColor == 'Completely Random':
            color = randColor
        else:
            # handle random
            if world.tunic_colors[i] == 'Random Choice':
                color = TunicColors[randomColors[i]]
            # grab the color from the list
            elif thisColor in TunicColors: 
                color = TunicColors[thisColor] 
            # build color from hex code  
            else: 
                color = list(int(thisColor[i:i+2], 16) for i in (0, 2 ,4)) 
        rom.write_bytes(Tunics[i], color)

    # patch navi colors
    Navi = []
    Navi.append([0x00B5E184]) # Default
    Navi.append([0x00B5E19C, 0x00B5E1BC]) # Enemy, Boss
    Navi.append([0x00B5E194]) # NPC
    Navi.append([0x00B5E174, 0x00B5E17C, 0x00B5E18C, 0x00B5E1A4, 0x00B5E1AC, 0x00B5E1B4, 0x00B5E1C4, 0x00B5E1CC, 0x00B5E1D4]) # Everything else
    naviList = get_navi_colors()
    randomColors = random.choices(naviList, k=4)

    for i in range(len(Navi)):
        # do everything in the inner loop so that "true random" changes even for subcategories
        for j in range(len(Navi[i])):
            # get the color option
            thisColor = world.navi_colors[i]
            # handle true random
            randColor = [random.getrandbits(8), random.getrandbits(8), random.getrandbits(8), 0xFF,
                         random.getrandbits(8), random.getrandbits(8), random.getrandbits(8), 0x00]
            if thisColor == 'Completely Random':
                color = randColor
            else:
                # handle random
                if world.navi_colors[i] == 'Random Choice':
                    color = NaviColors[randomColors[i]]
                # grab the color from the list
                elif thisColor in NaviColors: 
                    color = NaviColors[thisColor] 
                # build color from hex code  
                else: 
                    color = list(int(thisColor[i:i+2], 16) for i in (0, 2 ,4)) 
                    color = color + [0xFF] + color + [0x00] 
            rom.write_bytes(Navi[i][j], color)

    #Navi hints
    NaviHint = []
    NaviHint.append([0xAE7EF2, 0xC26C7E]) #Overworld Hint
    NaviHint.append([0xAE7EC6]) #Enemy Target Hint
    naviHintSFXList = ['Default', 'Notification', 'Rupee', 'Timer', 'Tamborine', 'Recovery Heart', 'Carrot Refill', 'Navi - Hey!', 'Navi - Random', 'Zelda - Gasp', 'Cluck', 'Mweep!', 'None']
    randomNaviHintSFX = random.choices(naviHintSFXList, k=2)
    
    for i in range(len(NaviHint)):
        for j in range(len(NaviHint[i])):
            thisNaviHintSFX = world.navi_hint_sounds[i]
            if thisNaviHintSFX == 'Random Choice':
                thisNaviHintSFX = randomNaviHintSFX[i]
            if thisNaviHintSFX == 'Notification':
                naviHintSFX = [0x48, 0x20]
            elif thisNaviHintSFX == 'Rupee':
                naviHintSFX = [0x48, 0x03]
            elif thisNaviHintSFX == 'Timer':
                naviHintSFX = [0x48, 0x1A]
            elif thisNaviHintSFX == 'Tamborine':
                naviHintSFX = [0x48, 0x42]
            elif thisNaviHintSFX == 'Recovery Heart':
                naviHintSFX = [0x48, 0x0B]
            elif thisNaviHintSFX == 'Carrot Refill':
                naviHintSFX = [0x48, 0x45]
            elif thisNaviHintSFX == 'Navi - Hey!':
                naviHintSFX = [0x68, 0x5F]
            elif thisNaviHintSFX == 'Navi - Random':
                naviHintSFX = [0x68, 0x43]
            elif thisNaviHintSFX == 'Zelda - Gasp':
                naviHintSFX = [0x68, 0x79]
            elif thisNaviHintSFX == 'Cluck':
                naviHintSFX = [0x28, 0x12]
            elif thisNaviHintSFX == 'Mweep!':
                naviHintSFX = [0x68, 0x7A]
            elif thisNaviHintSFX == 'None':
                naviHintSFX = [0x00, 0x00]
            if thisNaviHintSFX != 'Default':
                rom.write_bytes(NaviHint[i][j], naviHintSFX)

    #Low health beep
    healthSFXList = ['Default', 'Softer Beep', 'Rupee', 'Timer', 'Tamborine', 'Recovery Heart', 'Carrot Refill', 'Navi - Hey!', 'Zelda - Gasp', 'Cluck', 'Mweep!', 'None']
    randomSFX = random.choice(healthSFXList)
    address = 0xADBA1A
    
    if world.healthSFX == 'Random Choice':
        thisHealthSFX = randomSFX
    else:
        thisHealthSFX = world.healthSFX
    if thisHealthSFX == 'Default':
        healthSFX = [0x48, 0x1B]
    elif thisHealthSFX == 'Softer Beep':
        healthSFX = [0x48, 0x04]
    elif thisHealthSFX == 'Rupee':
        healthSFX = [0x48, 0x03]
    elif thisHealthSFX == 'Timer':
        healthSFX = [0x48, 0x1A]
    elif thisHealthSFX == 'Tamborine':
        healthSFX = [0x48, 0x42]
    elif thisHealthSFX == 'Recovery Heart':
        healthSFX = [0x48, 0x0B]
    elif thisHealthSFX == 'Carrot Refill':
        healthSFX = [0x48, 0x45]
    elif thisHealthSFX == 'Navi - Hey!':
        healthSFX = [0x68, 0x5F]
    elif thisHealthSFX == 'Zelda - Gasp':
        healthSFX = [0x68, 0x79]
    elif thisHealthSFX == 'Cluck':
        healthSFX = [0x28, 0x12]
    elif thisHealthSFX == 'Mweep!':
        healthSFX = [0x68, 0x7A]
    elif thisHealthSFX == 'None':
        healthSFX = [0x00, 0x00, 0x00, 0x00]
        address = 0xADBA14
    rom.write_bytes(address, healthSFX)
        
    return rom

# Format: (Title, Sequence ID)
bgm_sequence_ids = [
    ('Hyrule Field', 0x02),
    ('Dodongos Cavern', 0x18),
    ('Kakariko Adult', 0x19),
    ('Battle', 0x1A),
    ('Boss Battle', 0x1B),
    ('Inside Deku Tree', 0x1C),
    ('Market', 0x1D),
    ('Title Theme', 0x1E),
    ('House', 0x1F),
    ('Jabu Jabu', 0x26),
    ('Kakariko Child', 0x27),
    ('Fairy Fountain', 0x28),
    ('Zelda Theme', 0x29),
    ('Fire Temple', 0x2A),
    ('Forest Temple', 0x2C),
    ('Castle Courtyard', 0x2D),
    ('Ganondorf Theme', 0x2E),
    ('Lon Lon Ranch', 0x2F),
    ('Goron City', 0x30),
    ('Miniboss Battle', 0x38),
    ('Temple of Time', 0x3A),
    ('Kokiri Forest', 0x3C),
    ('Lost Woods', 0x3E),
    ('Spirit Temple', 0x3F),
    ('Horse Race', 0x40),
    ('Ingo Theme', 0x42),
    ('Fairy Flying', 0x4A),
    ('Deku Tree', 0x4B),
    ('Windmill Hut', 0x4C),
    ('Shooting Gallery', 0x4E),
    ('Sheik Theme', 0x4F),
    ('Zoras Domain', 0x50),
    ('Shop', 0x55),
    ('Chamber of the Sages', 0x56),
    ('Ice Cavern', 0x58),
    ('Kaepora Gaebora', 0x5A),
    ('Shadow Temple', 0x5B),
    ('Water Temple', 0x5C),
    ('Gerudo Valley', 0x5F),
    ('Potion Shop', 0x60),
    ('Kotake and Koume', 0x61),
    ('Castle Escape', 0x62),
    ('Castle Underground', 0x63),
    ('Ganondorf Battle', 0x64),
    ('Ganon Battle', 0x65),
    ('Fire Boss', 0x6B),
    ('Mini-game', 0x6C)
]

def randomize_music(rom):
    # Read in all the Music data
    bgm_data = []
    for bgm in bgm_sequence_ids:
        bgm_sequence = rom.read_bytes(0xB89AE0 + (bgm[1] * 0x10), 0x10)
        bgm_instrument = rom.read_int16(0xB89910 + 0xDD + (bgm[1] * 2))
        bgm_data.append((bgm_sequence, bgm_instrument))

    # shuffle data
    random.shuffle(bgm_data)

    # Write Music data back in random ordering
    for bgm in bgm_sequence_ids:
        bgm_sequence, bgm_instrument = bgm_data.pop()
        rom.write_bytes(0xB89AE0 + (bgm[1] * 0x10), bgm_sequence)
        rom.write_int16(0xB89910 + 0xDD + (bgm[1] * 2), bgm_instrument)

   # Write Fairy Fountain instrument to File Select (uses same track but different instrument set pointer for some reason) 
    rom.write_int16(0xB89910 + 0xDD + (0x57 * 2), rom.read_int16(0xB89910 + 0xDD + (0x28 * 2))) 
         
def disable_music(rom):
    # First track is no music
    blank_track = rom.read_bytes(0xB89AE0 + (0 * 0x10), 0x10)
    for bgm in bgm_sequence_ids:
        rom.write_bytes(0xB89AE0 + (bgm[1] * 0x10), blank_track)

