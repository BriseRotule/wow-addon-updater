import zipfile, configparser
from os.path import isfile, join, dirname
from os import chdir, listdir
from io import BytesIO
import shutil
import tempfile
import SiteHandler
import cfscrape
import packages.requests as requests
from tkinter import *
from tkinter import scrolledtext, filedialog
from tkinter.ttk import *
import queue
import threading


def confirmExit():
    input('\nPress the Enter key to exit')
    exit(0)

class AddonUpdater:
    def __init__(self):
        # Read config file
        self.config = configparser.ConfigParser()
        configFile = 'config.ini'

        if isfile(configFile):
            self.config.read(configFile)
        elif isfile(join(dirname(__file__), configFile)):
            # Couldn't find configFile in the current directory, but found it in the script's directory.
            chdir(dirname(__file__))
            self.config.read(configFile)
        else:
            print('Failed to read configuration file. Are you sure there is a file called "config.ini"?\n')
            confirmExit()

        try:
            self.WOW_ADDON_LOCATION = self.config['WOW ADDON UPDATER']['WoW Addon Location']
            self.ADDON_LIST_FILE = self.config['WOW ADDON UPDATER']['Addon List File']
            self.INSTALLED_VERS_FILE = self.config['WOW ADDON UPDATER']['Installed Versions File']
            self.AUTO_CLOSE = self.config['WOW ADDON UPDATER']['Close Automatically When Completed']
            self.VERSION = self.config['WOW ADDON UPDATER']['Game Version']
        except Exception:
            print('Failed to parse configuration file. Are you sure it is formatted correctly?\n')
            confirmExit()

        # Add "Use GUI = true" to the config file if the option is missing.
        try:
            useguivalue = self.config['WOW ADDON UPDATER']['Use GUI']
            if str.lower(useguivalue) in ["yes", "true", "1", "on"]:
                self.USE_GUI = True
            else:
                self.USE_GUI = False
        except KeyError:
            self.USE_GUI = True
            self.config['WOW ADDON UPDATER']['Use GUI'] = "True"

        if not isfile(self.ADDON_LIST_FILE):
            print('Failed to read addon file. Are you sure the file exists?\n')
            open(self.ADDON_LIST_FILE,'a')
            # TODO feedback app initialized without addons - better to do it elsewhere

        if not isfile(self.INSTALLED_VERS_FILE):
            with open(self.INSTALLED_VERS_FILE, 'w') as newInstalledVersFile:
                newInstalledVers = configparser.ConfigParser()
                newInstalledVers['Installed Versions'] = {}
                newInstalledVers.write(newInstalledVersFile)
        if self.USE_GUI:
            self.initGUI()

    def updateTree(self):
        with open(self.ADDON_LIST_FILE, "r") as fin:
            for line in fin:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Here we populate the Tree
                    line = line.strip()
                    if '|' in line: # Expected input format: "mydomain.com/myzip.zip" or "mydomain.com/myzip.zip|subfolder"
                        subfolder = line.split('|')[1]
                        line = line.split('|')[0]
                    else:
                        subfolder = ''
                    addonName = SiteHandler.getAddonName(line)
                    installedVersion = self.getInstalledVersion(line,subfolder)
                    newVersion = SiteHandler.getCurrentVersion(line,self.VERSION)
                    if newVersion == installedVersion:
                        state = '"Up to date"'
                    else:
                        state = '"New version available"'
                    self.tree.item(addonName,values=(installedVersion+' '+newVersion+' '+state))

    def initGUI(self):
        # We don't need any of this stuff if we're not running the GUI.
        self.textqueue = queue.Queue()
        self.progressqueue = queue.Queue()
        root = Tk()
        root.title("WoW Addon Updater")

        root.minsize(290, 214)
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        mainframe = Frame(root, padding="3 3 3 3")
        mainframe.grid(sticky=(N, W, E, S))

        mainframe.rowconfigure(0, weight=0)
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(1, weight=1)
        mainframe.columnconfigure(1, weight=1)
        mainframe.rowconfigure(2, weight=0)
        mainframe.columnconfigure(2, weight=1)
        mainframe.rowconfigure(3, weight=0)

        Sizegrip(root).grid(row=0, sticky=(S,E))

        Label(mainframe, text="WoW Addon Updater", font=("Helvetica", 20)).grid(column=0, row=0, sticky=(N), columnspan=3)

        # TODO make something with this
        output_text = scrolledtext.ScrolledText(mainframe, width=110, height=20, wrap=WORD)
        output_text.grid(column=0, row=1, sticky=(N,S,E,W), columnspan=3)

        # Implement tree instead of ScrolledText
        self.tree = Treeview(mainframe)
        self.tree.grid(column=0, row=1, sticky=(N,S,E,W), columnspan=3)
        self.tree['columns'] = ('currentVersion', 'newVersion', 'update')
        self.tree.heading('#0', text='Name', anchor=W)
        self.tree.heading('currentVersion', text='Current version', anchor=W)
        self.tree.heading('newVersion', text='Availlable version', anchor=W)
        self.tree.heading('update', text='Update')

        progressbar = Progressbar(mainframe, orient="horizontal", mode="determinate")
        progressbar.grid(column=0, row=2, sticky=(E,W), columnspan=3)
        with open(self.ADDON_LIST_FILE, "r") as fin:
            length = 0
            for line in fin:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Here we populate the Tree
                    line = line.strip()
                    if '|' in line: # Expected input format: "mydomain.com/myzip.zip" or "mydomain.com/myzip.zip|subfolder"
                        subfolder = line.split('|')[1]
                        line = line.split('|')[0]
                    else:
                        subfolder = ''
                    addonName = SiteHandler.getAddonName(line)
                    installedVersion = self.getInstalledVersion(line,subfolder)
                    newVersion = SiteHandler.getCurrentVersion(line,self.VERSION)
                    if newVersion == installedVersion:
                        state = '"Up to date"'
                    else:
                        state = '"New version available"'
                    self.tree.insert('','end',addonName,text=addonName,values=(installedVersion+' '+newVersion+' '+state))
                    length += 1
            progressbar.configure(value=0, maximum = length)

        self.root = root
        self.output_text = output_text
        self.progressbar = progressbar
        self.ABORT = threading.Event()
        root.protocol("WM_DELETE_WINDOW", self.shutdownGUI)

        self.cancelbutton = Button(mainframe, text="Cancel", command=self.abortUpdating, state=DISABLED)
        self.cancelbutton.grid(column=0, row=3)
        self.configButton = Button(mainframe, text="Configure", command=self.editConfig)
        self.configButton.grid(column=1, row=3)
        self.startbutton = Button(mainframe, text="Update", command=self.startUpdating)
        self.startbutton.grid(column=2, row=3)

        for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)
        self.output_text.insert(END, 'Welcome to WoW Addon Updater. If you\'ve already made an addons.txt file, click Start to begin.' + '\n')
        self.updateGUI()

    def updateGUI(self):
        # GUI refresh loop.
        try:
            text = self.textqueue.get_nowait()
            self.output_text.insert(END, '\n' + text)
            self.output_text.see(END)
        except queue.Empty:
            pass
        try:
            progress = self.progressqueue.get_nowait()
            self.progressbar.step()
        except queue.Empty:
            pass
        try:
            if not self.updatethread.is_alive():
                self.finishUpdating()
                # updatethread is dead and we've cleaned up, so wipe it.
                self.updatethread = None
        except AttributeError:
            pass
        self.root.after(200, self.updateGUI)

    def addText(self, text):
        # Put output in the queue for the GUI if we're using the GUI.
        # updateGUI() picks it up from the queue and adds it to the text box.
        # Threads suck. Only the GUI thread can touch GUI controls.
        print(str(text))

    def addProgress(self):
        self.progressqueue.put("step")

    def startUpdating(self):
        self.startbutton['state'] = DISABLED
        self.cancelbutton['state'] = NORMAL
        self.ABORT.clear()
        self.updatethread = threading.Thread(target=self.update)
        self.updatethread.start()

    def finishUpdating(self):
        # Clean up if update thread is dead.
        self.startbutton['state'] = NORMAL
        self.cancelbutton['state'] = DISABLED
        self.progressbar.configure(value=0)

    def shutdownGUI(self):
        # No doing other things while we're shutting down
        self.startbutton['state'] = DISABLED
        self.cancelbutton['state'] = DISABLED
        # This should only be called from the GUI thread, so we can touch the text box directly.
        # Using the queue won't work because we're not refreshing any more.
        self.output_text.insert(END, '\n' + 'Shutting down.')
        self.output_text.see(END)
        # Refresh the GUI to show the above changes.
        self.root.update_idletasks()
        try:
            if self.updatethread.is_alive():
                # The update thread is running, so set the ABORT flag and wait.
                self.ABORT.set()
                self.updatethread.join()
        except AttributeError:
            # Update thread doesn't exist, so, continuing.
            pass
        exit()

    def abortUpdating(self):
        try:
            if self.updatethread.is_alive():
                self.ABORT.set()
                self.addText("Trying to cancel...")
                self.cancelbutton['state'] = DISABLED
            else:
                self.addText("Update isn't running.")
        except AttributeError:
            self.addText("Update doesn't seem to be running.")

    def editConfig(self):
        configWindow = Toplevel(self.root)
        configWindow.grab_set()
        configWindow.wm_title("Configuration")

        # Declaring the properties we can edit
        configPath = StringVar()
        version = StringVar()
        version.set(self.VERSION)

        Label(configWindow, text="Add on path :").grid(row=1,column=0)
        Label(configWindow, text="Game version :").grid(row=2,column=0)

        def exitAction(self):
            configWindow.destroy()
            configWindow.update()
            self.updateTree()


        def saveChanges():
            self.WOW_ADDON_LOCATION = configPath.get()
            self.config['WOW ADDON UPDATER']['WoW Addon Location'] = self.WOW_ADDON_LOCATION

            self.VERSION = version.get()
            self.config['WOW ADDON UPDATER']['game version'] = self.VERSION
            # TODO Add verification to check if the folder exist
            with open("config.ini", "w+") as configfile:
                self.config.write(configfile)
            exitAction(self)

        configWindow.applybutton = Button(configWindow, text="Apply", command=saveChanges)
        configWindow.cancelbutton = Button(configWindow, text="Cancel", command=lambda: exitAction(self))

        configPathField = Entry(configWindow, textvariable=configPath, width=60, state=DISABLED)
        configPath.set(self.WOW_ADDON_LOCATION)

        def browse():
            options = {}
            options['initialdir'] = self.WOW_ADDON_LOCATION
            options['title'] = "Addon folder"
            options['mustexist'] = True
            filename = filedialog.askdirectory(**options)
            if filename == "":
                configPath.set(self.WOW_ADDON_LOCATION)
            else:
                configPath.set(filename)

        configWindow.browse = Button(configWindow, text="Browse...", command=browse)

        supported = self.config['SUPPORTED VERSIONS']['versions'].split(",")

        configWindow.version = OptionMenu(configWindow, version, version.get(), *supported)

        configPathField.grid(row=1,column=1)
        configWindow.browse.grid(row=1, column=2)
        configWindow.version.grid(row=2,column=1)

        # Buttons are always at the bottom of the window
        col_count, row_count = configWindow.grid_size()
        configWindow.cancelbutton.grid(row=col_count+1,column=1)
        configWindow.applybutton.grid(row=col_count+1,column=2)


        col_count, row_count = configWindow.grid_size()
        configWindow.minsize(50, row_count*20+10)

        for col in range(col_count):
            configWindow.grid_columnconfigure(col, minsize=20)

        for row in range(row_count):
            configWindow.grid_rowconfigure(row, minsize=20)

    def update(self):
        uberlist = []
        self.threads = []
        with open(self.ADDON_LIST_FILE, "r") as fin:
            if self.USE_GUI:
                self.addText('Checking for updates.' + '\n')
            for line in fin:
                self.threads.append(threading.Thread(target=self.update_addon, args=(line, uberlist)))

        for thread in self.threads:
            thread.start()

        for thread in self.threads:
            thread.join()

        if self.USE_GUI:
            self.addText('\n' + 'All done!')
            return
        if self.AUTO_CLOSE == 'False':
            if len(uberlist) != 0:
                col_width = max(len(word) for row in uberlist for word in row) + 2  # padding
                print("".join(word.ljust(col_width) for word in ("Name","Iversion","Cversion")))
                for row in uberlist:
                    print("".join(word.ljust(col_width) for word in row), end='\n')
                confirmExit()
            else:
                print("AddOns list empty.")

    def update_addon(self, addon, uberlist):
        # TODO better way of handling cancel. Should watch for every thread and close them
        current_node = []
        addon = addon.rstrip('\n')
        if not addon or addon.startswith('#'):
            return
        if self.USE_GUI and self.ABORT.is_set():
            # The GUI thread has asked the update thread to stop.
            self.addText("Cancelled.")
            return
        if '|' in addon: # Expected input format: "mydomain.com/myzip.zip" or "mydomain.com/myzip.zip|subfolder"
            subfolder = addon.split('|')[1]
            addon = addon.split('|')[0]
        else:
            subfolder = ''
        addonName = SiteHandler.getAddonName(addon)
        currentVersion = SiteHandler.getCurrentVersion(addon, self.VERSION)
        if currentVersion is None:
            currentVersion = 'Not Available'
        current_node.append(addonName)
        current_node.append(currentVersion)
        installedVersion = self.getInstalledVersion(addon,subfolder)
        if self.USE_GUI and self.ABORT.is_set():
            # The GUI thread has asked the update thread to stop.
            self.addText("Cancelled.")
            return
        # TODO should not be checked here anymore
        if not currentVersion == installedVersion:
            self.addText('Installing/updating addon: ' + addonName + ' to version: ' + currentVersion)
            ziploc = SiteHandler.findZiploc(addon, self.VERSION)
            install_success = False
            install_success = self.getAddon(ziploc, subfolder)
            current_node.append(self.getInstalledVersion(addon, subfolder))
            if install_success and (currentVersion is not ''):
                # Update was successfull, we handle the GUI change
                if self.USE_GUI:
                    self.addProgress()
                    self.tree.item(addonName,values=(currentVersion+' '+currentVersion+' "Up to date"'))
                self.setInstalledVersion(addon, subfolder, currentVersion)
        else:
            self.addText('Up to date: ' + addonName + ' version ' + currentVersion)
            current_node.append("Up to date")
        uberlist.append(current_node)

    def update_addon(self, addon, uberlist):
        current_node = []
        addon = addon.rstrip('\n')
        if not addon or addon.startswith('#'):
            return
        if self.USE_GUI and self.ABORT.is_set():
            # The GUI thread has asked the update thread to stop.
            self.addText("Cancelled.")
            return
        if '|' in addon: # Expected input format: "mydomain.com/myzip.zip" or "mydomain.com/myzip.zip|subfolder"
            subfolder = addon.split('|')[1]
            addon = addon.split('|')[0]
        else:
            subfolder = ''
        addonName = SiteHandler.getAddonName(addon)
        currentVersion = SiteHandler.getCurrentVersion(addon,self.VERSION)
        if currentVersion is None:
            currentVersion = 'Not Available'
        current_node.append(addonName)
        current_node.append(currentVersion)
        installedVersion = self.getInstalledVersion(addon,subfolder)
        self.addProgress()
        if self.USE_GUI and self.ABORT.is_set():
            # The GUI thread has asked the update thread to stop.
            self.addText("Cancelled.")
            return
        if not currentVersion == installedVersion:
            self.addText('Installing/updating addon: ' + addonName + ' to version: ' + currentVersion)
            ziploc = SiteHandler.findZiploc(addon, self.VERSION)
            install_success = False
            install_success = self.getAddon(ziploc, subfolder)
            current_node.append(self.getInstalledVersion(addon, subfolder))
            if install_success and (currentVersion is not ''):
                self.setInstalledVersion(addon, subfolder, currentVersion)
        else:
            self.addText('Up to date: ' + addonName + ' version ' + currentVersion)
            current_node.append("Up to date")
        uberlist.append(current_node)

    def getAddon(self, ziploc, subfolder):
        if ziploc == '':
            return False
        try:
            session = requests.Session()
            session.headers = SiteHandler.myHeaders
            scraper = cfscrape.create_scraper(sess=session)
            r = scraper.get(ziploc, stream=True)
            r.raise_for_status()   # Raise an exception for HTTP errors
            z = zipfile.ZipFile(BytesIO(r.content))
            self.extract(z, ziploc, subfolder)
            return True
        except Exception:
            self.addText('Failed to download or extract zip file for addon. Skipping...\n')
            return False

    def extract(self, zip, url, subfolder):
        if subfolder == '':
            zip.extractall(self.WOW_ADDON_LOCATION)
        else: # Pull subfolder out to main level, remove original extracted folder
            try:
                with tempfile.TemporaryDirectory() as tempDirPath:
                    zip.extractall(tempDirPath)
                    extractedFolderPath = join(tempDirPath, listdir(tempDirPath)[0])
                    subfolderPath = join(extractedFolderPath, subfolder)
                    destination_dir = join(self.WOW_ADDON_LOCATION, subfolder)
                    # Delete the existing copy, as shutil.copytree will not work if
                    # the destination directory already exists!
                    shutil.rmtree(destination_dir, ignore_errors=True)
                    shutil.copytree(subfolderPath, destination_dir)
            except Exception:
                print('Failed to get subfolder ' + subfolder)

    def getInstalledVersion(self, addonpage, subfolder):
        addonName = SiteHandler.getAddonName(addonpage)
        installedVers = configparser.ConfigParser()
        installedVers.read(self.INSTALLED_VERS_FILE)
        try:
            if(subfolder):
                return installedVers['Installed Versions'][addonName + '|' + subfolder] # Keep subfolder info in installed listing
            else:
                return installedVers['Installed Versions'][addonName]
        except Exception:
            return '"Version not found"'

    def setInstalledVersion(self, addonpage, subfolder, currentVersion):
        addonName = SiteHandler.getAddonName(addonpage)
        installedVers = configparser.ConfigParser()
        installedVers.read(self.INSTALLED_VERS_FILE)
        if(subfolder):
            installedVers.set('Installed Versions', addonName + '|' + subfolder, currentVersion) # Keep subfolder info in installed listing
        else:
            installedVers.set('Installed Versions', addonName, currentVersion)
        with open(self.INSTALLED_VERS_FILE, 'w') as installedVersFile:
            installedVers.write(installedVersFile)


def main():
    if(isfile('changelog.txt')):
        downloadedChangelog = requests.get('https://raw.githubusercontent.com/briserotule/wow-addon-updater/master/changelog.txt').text.split('\n')
        with open('changelog.txt') as cl:
            presentChangelog = cl.readlines()
            for i in range(len(presentChangelog)):
                presentChangelog[i] = presentChangelog[i].strip('\n')

    if(downloadedChangelog != presentChangelog):
        print('A new update to WoWAddonUpdater is available! Check it out at https://github.com/kuhnerdm/wow-addon-updater !')
    
    addonupdater = AddonUpdater()
    if addonupdater.USE_GUI:
        addonupdater.root.mainloop()
    else:
        addonupdater.update()
    return


if __name__ == "__main__":
    # execute only if run as a script
    main()
