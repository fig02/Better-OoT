import argparse
import textwrap
import string
import re
import random
import hashlib

from Patches import get_tunic_color_options, get_navi_color_options

class ArgumentDefaultsHelpFormatter(argparse.RawTextHelpFormatter):

    def _get_help_string(self, action):
        return textwrap.dedent(action.help)

# 32 characters
letters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
index_to_letter = { i: letters[i] for i in range(32) }
letter_to_index = { v: k for k, v in index_to_letter.items() }

def bit_string_to_text(bits):
    # pad the bits array to be multiple of 5
    if len(bits) % 5 > 0:
        bits += [0] * (5 - len(bits) % 5)
    # convert to characters
    result = ""
    for i in range(0, len(bits), 5):
        chunk = bits[i:i + 5]
        value = 0
        for b in range(5):
            value |= chunk[b] << b
        result += index_to_letter[value]
    return result

def text_to_bit_string(text):
    bits = []
    for c in text:
        index = letter_to_index[c]
        for b in range(5):
            bits += [ (index >> b) & 1 ]
    return bits

# holds the info for a single setting
class Setting_Info():

    def __init__(self, name, type, bitwidth=0, shared=False, args_params={}, gui_params=None):
        self.name = name # name of the setting, used as a key to retrieve the setting's value everywhere
        self.type = type # type of the setting's value, used to properly convert types in GUI code
        self.bitwidth = bitwidth # number of bits needed to store the setting, used in converting settings to a string
        self.shared = shared # whether or not the setting is one that should be shared, used in converting settings to a string
        self.args_params = args_params # parameters that should be pased to the command line argument parser's add_argument() function
        self.gui_params = gui_params # parameters that the gui uses to build the widget components

# holds the particular choices for a run's settings
class Settings():

    def get_settings_display(self):
        padding = 0
        for setting in filter(lambda s: s.shared, setting_infos):
            padding = max( len(setting.name), padding )
        padding += 2
        output = ''
        for setting in filter(lambda s: s.shared, setting_infos):
            name = setting.name + ': ' + ' ' * (padding - len(setting.name))
            val = str(self.__dict__[setting.name])
            output += name + val + '\n'
        return output

    def get_settings_string(self):
        bits = []
        for setting in filter(lambda s: s.shared and s.bitwidth > 0, setting_infos):
            value = self.__dict__[setting.name]
            i_bits = []
            if setting.type == bool:
                i_bits = [ 1 if value else 0 ]
            if setting.type == str:
                index = setting.args_params['choices'].index(value)
                # https://stackoverflow.com/questions/10321978/integer-to-bitfield-as-a-list
                i_bits = [1 if digit=='1' else 0 for digit in bin(index)[2:]]
                i_bits.reverse()
            if setting.type == int:
                value = value - ('min' in setting.gui_params and setting.gui_params['min'] or 0)
                value = int(value / ('step' in setting.gui_params and setting.gui_params['step'] or 1))
                value = min(value, ('max' in setting.gui_params and setting.gui_params['max'] or value))
                # https://stackoverflow.com/questions/10321978/integer-to-bitfield-as-a-list
                i_bits = [1 if digit=='1' else 0 for digit in bin(value)[2:]]
                i_bits.reverse()
            # pad it
            i_bits += [0] * ( setting.bitwidth - len(i_bits) )
            bits += i_bits
        return bit_string_to_text(bits)

    def update_with_settings_string(self, text):
        bits = text_to_bit_string(text)

        for setting in filter(lambda s: s.shared and s.bitwidth > 0, setting_infos):
            cur_bits = bits[:setting.bitwidth]
            bits = bits[setting.bitwidth:]
            value = None
            if setting.type == bool:
                value = True if cur_bits[0] == 1 else False
            if setting.type == str:
                index = 0
                for b in range(setting.bitwidth):
                    index |= cur_bits[b] << b
                value = setting.args_params['choices'][index]
            if setting.type == int:
                value = 0
                for b in range(setting.bitwidth):
                    value |= cur_bits[b] << b
                value = value * ('step' in setting.gui_params and setting.gui_params['step'] or 1)
                value = value + ('min' in setting.gui_params and setting.gui_params['min'] or 0)
            self.__dict__[setting.name] = value

        self.settings_string = self.get_settings_string()
        self.numeric_seed = self.get_numeric_seed()

    def get_numeric_seed(self):
        # salt seed with the settings, and hash to get a numeric seed
        full_string = self.settings_string + self.seed
        return int(hashlib.sha256(full_string.encode('utf-8')).hexdigest(), 16)

    def sanatize_seed(self):
        # leave only alphanumeric and some punctuation
        self.seed = re.sub(r'[^a-zA-Z0-9_-]', '', self.seed, re.UNICODE)

    def update_seed(self, seed):
        self.seed = seed
        self.sanatize_seed()
        self.numeric_seed = self.get_numeric_seed()

    def update(self):
        self.settings_string = self.get_settings_string()
        self.numeric_seed = self.get_numeric_seed()

    # add the settings as fields, and calculate information based on them
    def __init__(self, settings_dict):
        self.__dict__.update(settings_dict)
        for info in setting_infos:
            if info.name not in self.__dict__:
                if info.type == bool:
                    self.__dict__[info.name] = True if info.gui_params['default'] == 'checked' else False
                if info.type == str:
                    if 'default' in info.args_params:
                        self.__dict__[info.name] = info.gui_params['default'] or info.args_params['default']
                    else:
                        self.__dict__[info.name] = ""
                if info.type == int:
                    self.__dict__[info.name] = info.gui_params['default'] or 1
        self.settings_string = self.get_settings_string()
        if(self.seed is None):
            # https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python
            self.seed = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        self.sanatize_seed()
        self.numeric_seed = self.get_numeric_seed()

def parse_custom_tunic_color(s):
    if s == 'Custom Color':
        raise argparse.ArgumentTypeError('Specify custom color by using \'Custom (#xxxxxx)\'')
    elif re.match(r'^Custom \(#[A-Fa-f0-9]{6}\)$', s):
        return re.findall(r'[A-Fa-f0-9]{6}', s)[0]
    elif s in get_tunic_color_options():
        return s
    else:
        raise argparse.ArgumentTypeError('Invalid color specified')

def parse_custom_navi_color(s):
    if s == 'Custom Color':
        raise argparse.ArgumentTypeError('Specify custom color by using \'Custom (#xxxxxx)\'')
    elif re.match(r'^Custom \(#[A-Fa-f0-9]{6}\)$', s):
        return re.findall(r'[A-Fa-f0-9]{6}', s)[0]
    elif s in get_navi_color_options():
        return s
    else:
        raise argparse.ArgumentTypeError('Invalid color specified')

# a list of the possible settings
setting_infos = [
    
    Setting_Info('check_version', bool, 0, False, 
    {
        'help': '''\
                Checks if you are on the latest version
                ''',
        'action': 'store_true'
    }),
        Setting_Info('create_wad', str, 2, False, 
        {
            'default': 'False',
            'const': 'False',
            'nargs': '?',
            'choices': ['True', 'False'],
            'help': '''\
                    Choose the ouput file type.
                    True: Creates a WAD for use on VC
                    False: Creates a ROM for use on N64 or Emu
                    ''',
        },
        {
            'text': 'Output File Type',
            'group': 'rom_tab',
            'widget': 'Radiobutton',
            'default': '          ROM          ',
            'horizontal': True,
            'options': {
                '          ROM          ': 'False',
                '          WAD          ': 'True',
            },
            'tooltip':'''\
                      Choose the output file type.
                      ROM: For use on N64 or Emulator
                      WAD: For use on Wii Virtual Console
                      '''
        }),
    Setting_Info('rom', str, 0, False, {
            'default': 'ZOOTDEC.z64',
            'help': 'Path to an OoT 1.0 rom to use as a base.'}),
    Setting_Info('wad', str, 0, False, {
            'default': '',
            'help': 'Path to a 1.2 WAD to use as a base for VC inject.'}),
    Setting_Info('output_dir', str, 0, False, {
            'default': '',
            'help': 'Path to output directory for rom generation.'}),

    Setting_Info('seed', str, 0, False, {
            'help': 'Define seed number to generate.'}),
    Setting_Info('count', int, 0, False, {
            'help': '''\
                    Use to batch generate multiple seeds with same settings.
                    If --seed is provided, it will be used for the first seed, then
                    used to derive the next seed (i.e. generating 10 seeds with
                    --seed given will produce the same 10 (different) roms each
                    time).
                    ''',
            'type': int}),
    Setting_Info('world_count', int, 0, False, {
            'default': 1,
            'help': '''\
                    Use to create a multi-world generation for co-op seeds.
                    World count is the number of players. Warning: Increasing
                    the world count will drastically increase generation time.
                    ''',
            'type': int}),
    Setting_Info('player_num', int, 0, False, {
            'default': 1,
            'help': '''\
                    Use to select world to generate when there are multiple worlds.
                    ''',
            'type': int}),
    Setting_Info('create_spoiler', bool, 1, True, 
        {
            'help': 'Output a Spoiler File',
            'action': 'store_true'
        }, 
        {
            'text': 'Create Spoiler Log',
            'group': 'rom_tab',
            'widget': 'Checkbutton',
            'default': 'unchecked',
            'dependency': lambda guivar: guivar['compress_rom'].get() != 'No ROM Output',
            'tooltip':'''\
                      Enabling this will change the seed.
                      '''
        }),
    Setting_Info('compress_rom', str, 2, False, 
        {
            'default': 'True',
            'const': 'True',
            'nargs': '?',
            'choices': ['True', 'False', 'None'],
            'help': '''\
                    Create a compressed version of the output rom file.
                    True: Compresses. Improves stability. Will take longer to generate
                    False: Uncompressed. Unstable. Faster generation
                    None: No ROM Output. Creates spoiler log only
                    ''',
        },
        {
            'text': 'Compress Rom',
            'group': 'rom_tab',
            'widget': 'Radiobutton',
            'default': 'Compressed [Stable]',
            'horizontal': True,
            'options': {
                'Compressed [Stable]': 'True',
                'Uncompressed [Crashes]': 'False',
                'No ROM Output': 'None',
            },
            'tooltip':'''\
                      The first time compressed generation will take a while 
                      but subsequent generations will be quick. It is highly 
                      recommended to compress or the game will crash 
                      frequently except on real N64 hardware.
                      '''
        }),
    Setting_Info('open_kakariko', bool, 1, True, 
        {
            'help': '''\
                    The gate in Kakariko Village to Death Mountain Trail
                    is always open, instead of needing Zelda's Letter.
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Open Kakariko Gate',
            'group': 'open',
            'widget': 'Checkbutton',
            'default': 'unchecked',
            'tooltip':'''\
                      The gate in Kakariko Village to Death Mountain Trail
                      is always open, instead of needing Zelda's Letter.

                      Either way, the gate is always open as adult.
                      '''
        }),
    Setting_Info('shuffle_song_items', bool, 1, True, 
        {
            'help': '''\
                    Shuffles the songs with with rest of the item pool so that
                    song can appear at other locations, and items can appear at
                    the song locations.
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Shuffle Songs with Items',
            'group': 'logic',
            'widget': 'Checkbutton',
            'default': 'unchecked',
            'tooltip':'''\
                      Songs can appear anywhere as normal items,
                      not just at vanilla song locations.
                      '''
        }),
    Setting_Info('background_music', str, 2, False,
        {
            'default': 'normal',
            'const': 'normal',
            'nargs': '?',
            'choices': ['normal', 'off', 'random'],
            'help': '''\
                    Sets the background music behavior
                    normal:      Areas play their normal background music
                    off:         No background music
                    random:      Areas play random background music
                    '''
        },
        {
            'text': 'Background Music',
            'group': 'cosmetics',
            'widget': 'Combobox',
            'default': 'Normal',
            'options': {
                'Normal': 'normal',
                'No Music': 'off',
                'Random': 'random',
            },
            'tooltip': '''\
                       'No Music': No background music.
                       is played.

                       'Random': Area background music is
                       randomized.
                       '''
        }),

    Setting_Info('kokiricolor', str, 0, False, 
        {
            'default': 'Kokiri Green',
            'const': 'Kokiri Green',
            'nargs': '?',
            'type': parse_custom_tunic_color,
            'help': '''\
                    Choose the color for Link's Kokiri Tunic. (default: %(default)s)
                    Color:              Make the Kokiri Tunic this color.
                    Random Choice:      Choose a random color from this list of colors.
                    Completely Random: Choose a random color from any color the N64 can draw.
                    '''
        },
        {
            'text': 'Kokiri Tunic Color',
            'group': 'tuniccolor',
            'widget': 'Combobox',
            'default': 'Kokiri Green',
            'options': get_tunic_color_options(),
            'tooltip':'''\
                      'Random Choice': Choose a random 
                      color from this list of colors.
                      'Completely Random': Choose a random 
                      color from any color the N64 can draw.
                      '''
        }),
    Setting_Info('goroncolor', str, 0, False, 
        {
            'default': 'Goron Red',
            'const': 'Goron Red',
            'nargs': '?',
            'type': parse_custom_tunic_color,
            'help': '''\
                    Choose the color for Link's Goron Tunic. (default: %(default)s)
                    Color:              Make the Goron Tunic this color.
                    Random Choice:      Choose a random color from this list of colors.
                    Completely Random: Choose a random color from any color the N64 can draw.
                    '''
        },
        {
            'text': 'Goron Tunic Color',
            'group': 'tuniccolor',
            'widget': 'Combobox',
            'default': 'Goron Red',
            'options': get_tunic_color_options(),
            'tooltip':'''\
                      'Random Choice': Choose a random 
                      color from this list of colors.
                      'Completely Random': Choose a random 
                      color from any color the N64 can draw.
                      '''
        }),
    Setting_Info('zoracolor', str, 0, False, 
        {
            'default': 'Zora Blue',
            'const': 'Zora Blue',
            'nargs': '?',
            'type': parse_custom_tunic_color,
            'help': '''\
                    Choose the color for Link's Zora Tunic. (default: %(default)s)
                    Color:              Make the Zora Tunic this color.
                    Random Choice:      Choose a random color from this list of colors.
                    Completely Random: Choose a random color from any color the N64 can draw.
                    '''
        },
        {
            'text': 'Zora Tunic Color',
            'group': 'tuniccolor',
            'widget': 'Combobox',
            'default': 'Zora Blue',
            'options': get_tunic_color_options(),
            'tooltip':'''\
                      'Random Choice': Choose a random 
                      color from this list of colors.
                      'Completely Random': Choose a random 
                      color from any color the N64 can draw.
                      '''
        }),
    Setting_Info('navicolordefault', str, 0, False, 
        {
            'default': 'White',
            'const': 'White',
            'nargs': '?',
            'type': parse_custom_navi_color,
            'help': '''\
                    Choose the color for Navi when she is idle. (default: %(default)s)
                    Color:             Make the Navi this color.
                    Random Choice:     Choose a random color from this list of colors.
                    Completely Random: Choose a random color from any color the N64 can draw.
                    '''
        },
        {
            'text': 'Navi Idle',
            'group': 'navicolor',
            'widget': 'Combobox',
            'default': 'White',
            'options': get_navi_color_options(),
            'tooltip':'''\
                      'Random Choice': Choose a random 
                      color from this list of colors.
                      'Comepletely Random': Choose a random 
                      color from any color the N64 can draw.
                      '''
        }),
    Setting_Info('navicolorenemy', str, 0, False, 
        {
            'default': 'Yellow',
            'const': 'Yellow',
            'nargs': '?',
            'type': parse_custom_navi_color,
            'help': '''\
                    Choose the color for Navi when she is targeting an enemy. (default: %(default)s)
                    Color:             Make the Navi this color.
                    Random Choice:     Choose a random color from this list of colors.
                    Completely Random: Choose a random color from any color the N64 can draw.
                    '''
        },
        {
            'text': 'Navi Targeting Enemy',
            'group': 'navicolor',
            'widget': 'Combobox',
            'default': 'Yellow',
            'options': get_navi_color_options(),
            'tooltip':'''\
                      'Random Choice': Choose a random 
                      color from this list of colors.
                      'Comepletely Random': Choose a random 
                      color from any color the N64 can draw.
                      '''
        }),
    Setting_Info('navicolornpc', str, 0, False, 
        {
            'default': 'Light Blue',
            'const': 'Light Blue',
            'nargs': '?',
            'type': parse_custom_navi_color,
            'help': '''\
                    Choose the color for Navi when she is targeting an NPC. (default: %(default)s)
                    Color:             Make the Navi this color.
                    Random Choice:     Choose a random color from this list of colors.
                    Completely Random: Choose a random color from any color the N64 can draw.
                    '''
        },
        {
            'text': 'Navi Targeting NPC',
            'group': 'navicolor',
            'widget': 'Combobox',
            'default': 'Light Blue',
            'options': get_navi_color_options(),
            'tooltip':'''\
                      'Random Choice': Choose a random 
                      color from this list of colors.
                      'Comepletely Random': Choose a random 
                      color from any color the N64 can draw.
                      '''
        }),
    Setting_Info('navicolorprop', str, 0, False, 
        {
            'default': 'Green',
            'const': 'Green',
            'nargs': '?',
            'type': parse_custom_navi_color,
            'help': '''\
                    Choose the color for Navi when she is targeting a prop. (default: %(default)s)
                    Color:             Make the Navi this color.
                    Random Choice:     Choose a random color from this list of colors.
                    Completely Random: Choose a random color from any color the N64 can draw.
                    '''
        },
        {
            'text': 'Navi Targeting Prop',
            'group': 'navicolor',
            'widget': 'Combobox',
            'default': 'Green',
            'options': get_navi_color_options(),
            'tooltip':'''\
                      'Random Choice': Choose a random 
                      color from this list of colors.
                      'Comepletely Random': Choose a random 
                      color from any color the N64 can draw.
                      '''
        }),
    Setting_Info('navisfxoverworld', str, 0, False, 
        {
            'default': 'Default',
            'const': 'Default',
            'nargs': '?',
            'choices': ['Default', 'Notification', 'Rupee', 'Timer', 'Tamborine', 'Recovery Heart', 'Carrot Refill', 'Navi - Hey!', 'Navi - Random', 'Zelda - Gasp', 'Cluck', 'Mweep!', 'Random', 'None'],
            'help': '''\
                    Select the sound effect that plays when Navi has a hint. (default: %(default)s)
                    Sound:         Replace the sound effect with the chosen sound.
                    Random Choice: Replace the sound effect with a random sound from this list.
                    None:          Eliminate Navi hint sounds.
                    '''
        },
        {
            'text': 'Navi Hint',
            'group': 'navihint',
            'widget': 'Combobox',
            'default': 'Default',
            'options': [
                'Random Choice', 
                'Default', 
                'Notification', 
                'Rupee', 
                'Timer', 
                'Tamborine', 
                'Recovery Heart', 
                'Carrot Refill', 
                'Navi - Hey!',
                'Navi - Random',
                'Zelda - Gasp', 
                'Cluck', 
                'Mweep!', 
                'None',
            ]
        }),
        Setting_Info('navisfxenemytarget', str, 0, False, 
        {
            'default': 'Default',
            'const': 'Default',
            'nargs': '?',
            'choices': ['Default', 'Notification', 'Rupee', 'Timer', 'Tamborine', 'Recovery Heart', 'Carrot Refill', 'Navi - Hey!', 'Navi - Random', 'Zelda - Gasp', 'Cluck', 'Mweep!', 'Random', 'None'],
            'help': '''\
                    Select the sound effect that plays when targeting an enemy. (default: %(default)s)
                    Sound:         Replace the sound effect with the chosen sound.
                    Random Choice: Replace the sound effect with a random sound from this list.
                    None:          Eliminate Navi hint sounds.
                    '''
        },
        {
            'text': 'Navi Enemy Target',
            'group': 'navihint',
            'widget': 'Combobox',
            'default': 'Default',
            'options': [
                'Random Choice', 
                'Default', 
                'Notification', 
                'Rupee', 
                'Timer', 
                'Tamborine', 
                'Recovery Heart', 
                'Carrot Refill', 
                'Navi - Hey!',
                'Navi - Random',
                'Zelda - Gasp', 
                'Cluck', 
                'Mweep!', 
                'None',
            ]
        }),
    Setting_Info('healthSFX', str, 0, False, 
        {
            'default': 'Default',
            'const': 'Default',
            'nargs': '?',
            'choices': ['Default', 'Softer Beep', 'Rupee', 'Timer', 'Tamborine', 'Recovery Heart', 'Carrot Refill', 'Navi - Hey!', 'Zelda - Gasp', 'Cluck', 'Mweep!', 'Random', 'None'],
            'help': '''\
                    Select the sound effect that loops at low health. (default: %(default)s)
                    Sound:         Replace the sound effect with the chosen sound.
                    Random Choice: Replace the sound effect with a random sound from this list.
                    None:          Eliminate heart beeps.
                    '''
        },
        {
            'text': 'Low Health SFX',
            'group': 'lowhp',
            'widget': 'Combobox',
            'default': 'Default',
            'options': [
                'Random Choice', 
                'Default', 
                'Softer Beep', 
                'Rupee', 
                'Timer', 
                'Tamborine', 
                'Recovery Heart', 
                'Carrot Refill', 
                'Navi - Hey!', 
                'Zelda - Gasp', 
                'Cluck', 
                'Mweep!', 
                'None',
            ],
            'tooltip':'''\
                      'Random Choice': Choose a random 
                      sound from this list.
                      'Default': Beep. Beep. Beep.
                      '''
        }),

    ########################################################################
    #Better OoT Settings
    ########################################################################

    Setting_Info('skip_intro', bool, 1, True, 
        {
            'help': '''\
                    Toggle the intro cutscene
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Skip Intro Cutscene',
            'group': 'other',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Skip the intro cutscene
                      '''
        }),


    Setting_Info('forest_elevator', bool, 1, True, 
        {
            'help': '''\
                    Toggle if the Poe Sisters cutscene is present in Forest Temple.
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Skip Forest Elevator Cutscene',
            'group': 'other',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Toggle if the Poe Sisters cutscene is 
                      present in Forest Temple.
                      '''
        }),

    Setting_Info('knuckle_cs', bool, 1, True, 
        {
            'help': '''\
                    Toggle if the cutscene plays after defeating Nabooru Knuckle
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Skip Nabooru Defeat Cutscene',
            'group': 'other',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Toggle if the cutscene plays after 
                      defeating Nabooru Knuckle
                      '''
        }),

    Setting_Info('dungeon_speedup', bool, 1, True, 
        {
            'help': '''\
                    Shorten blue warp cutscenes.
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Fast Blue Warp Cutscenes',
            'group': 'other',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Shorten blue warp cutscenes
                      '''
        }),

    Setting_Info('song_speedup', bool, 1, True, 
        {
            'help': '''\
                    Shorten song cutscenes
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Fast Song Cutscenes',
            'group': 'other',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Shorten song cutscenes
                      '''
        }),

    Setting_Info('fast_chests', bool, 1, True, 
        {
            'help': '''\
                    Makes all chests open without the large chest opening cutscene
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Fast Chest Cutscenes',
            'group': 'other',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      All chest animations are fast
                      '''
        }),

    Setting_Info('no_owls', bool, 1, True, 
        {
            'help': '''\
                    Toggle Owls in the overworld.
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Remove Owls',
            'group': 'other',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove owl triggers in the overworld.
                      '''
        }),

    Setting_Info('quickboots', bool, 1, True, 
        {
            'help': '''\
                    Toggle Owls in the overworld.
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Quick Boots',
            'group': 'other',
            'widget': 'Checkbutton',
            'default': 'unchecked',
            'tooltip':'''\
                      Toggle boots with the d-pad
                      '''
        }),

        Setting_Info('difficulty', str, 2, True, 
        {
            'default': 'normal',
            'const': 'normal',
            'nargs': '?',
            'choices': ['normal', 'ohko'],
            'help': '''\
                    Change the item pool for an added challenge.
                    normal:         Default items
                    hard:           Double defense, double magic, and all 8 heart containers are removed
                    very_hard:      Double defense, double magic, Nayru's Love, and all health upgrades are removed
                    ohko:           Same as very hard, and Link will die in one hit.
                    '''
        },
        {
            'text': 'Damage',
            'group': 'other',
            'widget': 'Combobox',
            'default': 'Normal',
            'options': {
                'Normal': 'normal',
                'One Hit KO': 'ohko'
            },
            'tooltip':'''\
                      'Normal': Vanilla behavior
                      'One Hit KO': Link dies in one hit.
                      '''
        }),

    Setting_Info('quest', str, 2, True, 
        {
            'default': 'vanilla',
            'const': 'vanilla',
            'nargs': '?',
            'choices': ['vanilla', 'master'],
            'help': '''\
                    Vanilla:       Dungeons will be the original Ocarina of Time dungeons.
                    Master:        Dungeons will be in the form of the Master Quest.
                    
                    '''
        },
        {
            'text': 'Dungeon Quest',
            'group': 'other',
            'widget': 'Combobox',
            'default': 'Vanilla',
            'options': {
                'Vanilla': 'vanilla',
                'Master Quest': 'master',
            },
            'tooltip':'''\
                      'Vanilla': Dungeons will be vanilla.
                      'Master Quest': Dungeons will be Master Quest.
                      ''',
        }),

    Setting_Info('default_targeting', str, 1, False, 
        {
            'default': 'hold',
            'const': 'always',
            'nargs': '?',
            'choices': ['hold', 'switch'],
            'help': '''\
                    Choose what the default Z-targeting is
                    '''
        },
        {
            'text': 'Default Targeting Option',
            'group': 'other',
            'widget': 'Combobox',
            'default': 'Hold',
            'options': {
                'Hold': 'hold',
                'Switch': 'switch',
            }
        }),

    #######################
    #area intro cutscenes
    #######################

    Setting_Info('skip_field', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Hyrule Field (affects time of day)',
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'unchecked',
            'tooltip':'''\
                      Remove area intro cutscene for this location. 
                      Note that enabling this option will add to initial time of day, making it start later in the day.
                      This can cause problems making it to market for ESS Owl Skip or Aqua Escape.
                      '''
        }),

    Setting_Info('skip_castle', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Hyrule Castle (affects time of day)',
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'unchecked',
            'tooltip':'''\
                      Remove area intro cutscene for this location. 
                      Note that enabling this option will add to initial time of day, making it start later in the day.
                      This can cause problems making it to market for ESS Owl Skip or Aqua Escape.
                      '''
        }),

    Setting_Info('skip_kak', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Kakariko Village',
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_gy', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Graveyard',
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_dmt', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Death Mountain Trail',
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_gc', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Goron City',
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_dmc', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': "Death Mountain Crater",
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_domain', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': "Zora's Domain",
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_fountain', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': "Zora's Fountain",
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_lh', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Lake Hylia',
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_gv', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Gerudo Valley',
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_gf', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Gerudo Fortress',
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_colossus', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Desert Colossus',
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_deku', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': 'Deku Tree',
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_dc', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': "Dodongo's Cavern",
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),

    Setting_Info('skip_jabu', bool, 1, True, 
        {
            'help': '''\
                    Remove area intro cutscene for this location
                    ''',
            'action': 'store_true'
        },
        {
            'text': "Jabu Jabu's Belly",
            'group': 'convenience',
            'widget': 'Checkbutton',
            'default': 'checked',
            'tooltip':'''\
                      Remove area intro cutscene for this location
                      '''
        }),
]

# gets the randomizer settings, whether to open the gui, and the logger level from command line arguments
def get_settings_from_command_line_args():
    parser = argparse.ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    for info in setting_infos:
        parser.add_argument("--" + info.name, **info.args_params)

    parser.add_argument('--gui', help='Launch the GUI', action='store_true')
    parser.add_argument('--loglevel', default='info', const='info', nargs='?', choices=['error', 'info', 'warning', 'debug'], help='Select level of logging for output.')
    parser.add_argument('--settings_string', help='Provide sharable settings using a settings string. This will override all flags that it specifies.')

    args = parser.parse_args()

    result = {}
    for info in setting_infos:
        result[info.name] = vars(args)[info.name]
    settings = Settings(result)

    if args.settings_string is not None:
        settings.update_with_settings_string(args.settings_string)

    return settings, args.gui, args.loglevel
