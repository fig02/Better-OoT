from collections import OrderedDict
from itertools import zip_longest
import json
import logging
import platform
import random
import subprocess
import time
import os
import struct

from BaseClasses import World, CollectionState, Item
from Rom import LocalRom
from Patches import patch_rom
from Utils import default_output_path

class dummy_window():
    def __init__(self):
        pass
    def update_status(self, text):
        pass
    def update_progress(self, val):
        pass

def main(settings, window=dummy_window()):

    start = time.clock()
    logger = logging.getLogger('')

    # initialize the world
    worlds = []
    if not settings.world_count:
        settings.world_count = 1
    if settings.world_count < 1:
        raise Exception('World Count must be at least 1')
    if settings.player_num > settings.world_count or settings.player_num < 1:
        raise Exception('Player Num must be between 1 and %d' % settings.world_count)

    for i in range(0, settings.world_count):
        worlds.append(World(settings))

    logger.info('Patching ROM.')

    outfilebase = 'BOoT_%s' % (worlds[0].settings_string)
    output_dir = default_output_path(settings.output_dir)

    window.update_status('Patching ROM')
    rom = LocalRom(settings)
    patch_rom(worlds[settings.player_num - 1], rom)
    window.update_progress(65)

    rom_path = os.path.join(output_dir, '%s.z64' % outfilebase)

    window.update_status('Saving Uncompressed ROM')
    rom.write_to_file(rom_path)

    window.update_status('Compressing ROM')
    logger.info('Compressing ROM.')

    compressor_path = ""
    if platform.system() == 'Windows':
        if 8 * struct.calcsize("P") == 64:
            compressor_path = "bin\\Compress\\Compress.exe"
        else:
            compressor_path = "bin\\Compress\\Compress32.exe"
    elif platform.system() == 'Linux':
        compressor_path = "bin/Compress/Compress"
    elif platform.system() == 'Darwin':
        compressor_path = "bin/Compress/Compress.out"
    else:
        logger.info('OS not supported for compression')

    #uncomment below for decompressed output (for debugging)
    #rom.write_to_file(default_output_path('%s.z64' % outfilebase))
    run_process(window, logger, [compressor_path, rom_path, os.path.join(output_dir, '%s-comp.z64' % outfilebase)])
    os.remove(rom_path)
    window.update_progress(95)

    window.update_progress(100)
    window.update_status('Success: ROM patched successfully')
    logger.info('Done. Enjoy.')
    logger.debug('Total Time: %s', time.clock() - start)

    return worlds[settings.player_num - 1]

def run_process(window, logger, args):
    process = subprocess.Popen(args, bufsize=1, stdout=subprocess.PIPE)
    filecount = None
    while True:
        line = process.stdout.readline()
        if line != b'':
            find_index = line.find(b'files remaining')
            if find_index > -1:
                files = int(line[:find_index].strip())
                if filecount == None:
                    filecount = files
                window.update_progress(65 + ((1 - (files / filecount)) * 30))
            logger.info(line.decode('utf-8').strip('\n'))
        else:
            break



