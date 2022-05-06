

def initGUI(self):
    # We don't need any of this stuff if we're not running the GUI.
    # C'est la modification C
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

    output_text = scrolledtext.ScrolledText(mainframe, width=110, height=20, wrap=WORD)
    output_text.grid(column=0, row=1, sticky=(N,S,E,W), columnspan=3)

    progressbar = Progressbar(mainframe, orient="horizontal", mode="determinate")
    progressbar.grid(column=0, row=2, sticky=(E,W), columnspan=3)
    with open(self.ADDON_LIST_FILE, "r") as fin:
        length = 0
        for line in fin:
            line = line.strip()
            if line and not line.startswith('#'):
                length += 1
        progressbar.configure(value=0, maximum = length)

    self.root = root
    self.output_text = output_text
    self.progressbar = progressbar
    self.ABORT = threading.Event()
    root.protocol("WM_DELETE_WINDOW", self.shutdownGUI)

    self.cancelbutton = Button(mainframe, text="Cancel", command=self.abortUpdating, state=DISABLED)
    self.cancelbutton.grid(column=0, row=3)
    self.startbutton = Button(mainframe, text="Start", command=self.startUpdating)
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
