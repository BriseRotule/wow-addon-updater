# wow-addon-updater

This utility provides an alternative to the Twitch/Curse client for management and updating of addons for World of Warcraft. The Twitch/Curse client is rather bloated and buggy, and comes with many features that most users will not ever use in the first place. This utility, however, is lightweight and makes it very easy to manage which addons are being updated, and to update them just by running a python script.

Changelog located in changelog.txt

## GUI
This version of wow-addon-updater use the primitive GUI from zurohki, if you don't want it to boot, change the config file "Use GUI" to False.

This is not recommenbded as support will not be provided.

## First-time setup

This utility has 3 dependencies :

* A version of [Python](https://www.python.org/) 3 (Any version of Python 3 should do)
* cloudflare-scrape (pip install cfscrape)
* PySocks (pip install pysocks)

## Configuring the utility

The UI provide you with the ability to change the install directory of the addonsas well as the version you want to play (The list has been initialized with classic and retail, other version can be added by editing the config.ini)

The default location to install the addons to is "D:\Jeux\World of Warcraft\_retail_\Interface\AddOns". That's probably not where you installed it, so change it via the UI.

The default location of the addon list file is simply "addons.txt", but this file will not exist on your PC, so you should either create "addons.txt" in the same location as the utility, or name the file something else and edit "config.ini" to point to the new file.

Before first startup, you won't have any addon present, you have to create a file named addons.txt or use the one generated and file in the list of addon you want to maintain (see below).

A way of adding addons with the UI is in the works.

## Input file format

Whatever file you use for your list of mods needs to be formatted in a particular way. Each line corresponds to a mod, and the line just needs to contain the link to the Curse or WoWInterface page for the mod. For example:

    https://www.curseforge.com/wow/addons/world-quest-tracker
    https://www.curseforge.com/wow/addons/deadly-boss-mods
    https://www.curseforge.com/wow/addons/auctionator
    http://www.wowinterface.com/downloads/info24005-RavenousMounts.html
    
    
Each link needs to be the main page for the addon, as shown above.

There is a special syntax for TukUI & ElvUI mods should be added to the list like :

    https://www.tukui.org/+tukui
    https://www.tukui.org/+elvui

Example show both, use one or the other (or both I don't judge).

because the downloadable zip from this website contains a subfolder called "ElvUI" containing the actual mod.

## macOS Installation Instructions - Thanks to https://github.com/melwan

1. Install Python 3 for macOS
2. Run get-pip.py (Run menu > Run Module)
3. Run get-requests.py (Run menu > Run Module)
4. Edit config.ini (using TextEdit.app)
5. Create in.txt (using TextEdit.app)
6. Run WoWAddonUpdater.py (Run menu > Run Module)

The standard addon location on macOS is /Applications/World of Warcraft/Interface/AddOns

*Note: To save to a .txt file in TextEdit, go to Preferences > "New Document" tab > Under the "Format" section, choose "Plain Text".*

## Running the utility

After configuring the utility and setting up your input file, updating your addons is as simple as double clicking the "WoWAddonUpdater.py" file.

## Contact info

Have any questions, concerns, issues, or suggestions for the utility? Feel free to either submit an issue through Github or trhough reddit at /u/Bromur. Please put in the subject line that this is for the WoW Addon Updater.

## Future plans

* Update to the visual interface  - The actual UI is very barebone
    - Implement the ability to add a addon
    - General redesign
    - Logo



Thanks for checking this out; hopefully it helps a lot of you :)
