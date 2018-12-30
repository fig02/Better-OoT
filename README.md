# Better OoT


This is a ROM patcher for _The Legend of Zelda: Ocarina of Time_ that applies various quality-of-life changes to the game. These changes are implemented with various speedrun categories in mind.


This is an extension of an idea initially created by Moltov. This project aims to furhter allow the user to customize their settings and preserve most aspects of all main speedrunning categories


This project is based on the 3.0 version of the Ocarina of Time Randomizer. Many new features were added, and many details were tweaked to preserve details of speedrun routes

## Download and Install

Download the appropriate version for your system from the [releases page](https://github.com/fig02/Better-OoT/releases)

Windows 10 - Download "BOoT-win10-32exe.zip" and extract the contents of the zip folder to your location of choice. Double click BetterOoT.exe (the app with the ocarina icon) to run

Windows 8/7/Vista/XP - Download "BOoT-win-other-32exe.zip" and extract the contents of the zip folder to your location of choice. Double click BetterOoT.exe (the app with the ocarina icon) to run.
(If youre on windows 10 you can run this version too. It just has more files so it is a bit more cluttered than the win10 release)

Mac/Linux - Bundled versions are not supported for these operating systems. You will need to download and install [python 3.7](https://www.python.org/downloads/) and run from source. Download BOoT-Source.zip and run the Gui.py python script

## Usage

After opening Better OoT you will be greeted by a ROM patcher. This patcher has 3 tabs which you can use to tweak the settings to your liking

### ROM Tab
This tab is where you specify file information for the patcher

Base ROM - Path to a Vanilla 1.0 OoT rom. This is the rom the patcher will use a base. You must supply your own ROM, one is not included with this program.

Base WAD - Path to a Vanilla 1.2 OoT WAD. This is only neccessary if you are patching a WAD for use on VC. If you are making a WAD remember to still supply a ROM too. You must supply your own WAD, one is not included with this program.

Output Directory - Path for the output of the program. By default this is set to an "Output" folder in the Better OoT folder. If this folder does not exist, the patcher will create it.

Output File Type - You can choose from creating a ROM or a WAD. Select ROM if you are playing on N64/Emulator. Select WAD if you are playing on Wii Virtual Console. If you select WAD you must supply a base WAD in the field above.

### Options Tab
This tab is where you specify settings that will effect gameplay

Remove Area Intro Cutscenes - Listed are checkboxes for most area introduction cutscenes in the game. These are customizeable because they can have an effect on speedrun routes depending on the category. For example: Glitchless would want to keep the Gerudo Fortress cutscene because of the guard cycles, while other categories would want to get rid of it. Uncheck a box to add the intro cutscene for that area back.

Skip Intro Cutscene - With this checked, the cutscene played at the beginning of a new file will be skipped. You will immediatley spawn in links house

Skip Forest Elevator Cutscene - Toggle if the cutscene in Forest Temple plays where the Poe Sisters bring the elevator down. It is desireable to add this back mainly for 100%

Skip Nabooru Defeat Cutscene - Toggle if the Nabooru Knuckle cs plays when defeating her. This is toggleable because you can skip it with glitches

Fast Blue Warp Cutscenes - Speed up all cutscenes that play when entering a dungeon blue warp. Note that Wrong Warps still work when this option is enabled.

Fast Song Cutscenes - When learning songs you will immediatley be prompted to play the song. This is toggleable because you can skip most of these cutscenes with glitches

Fast Chest Cutscenes - Link will kick open all chests regardless of size

Remove Owls - Owl triggers will be removed. Note that this effects time of day

Quick Boots - With this enabled Hover Boots and Iron Boots will be toggleable on the dpad wihout needing to pause the game. This is more of a fun extra feature that was made for rando, and was requested to be included here too.

Damage - Choose between normal damage and one hit ko mode

Dungeon Quest - Choose between Vanilla and Master Quest Dungeons

Default Targetting Option - Hold Targetting is mandatory (Kappa)


### Cosmetics Tab