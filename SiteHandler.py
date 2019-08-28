import packages.requests as requests
import re

# Site splitter

def findZiploc(addonpage, version):
    # Curse
    if addonpage.startswith('https://www.curseforge.com/wow/addons/'):
        return curse(addonpage, version)

    # Curse Project
    elif addonpage.startswith('https://wow.curseforge.com/projects/'):
        if addonpage.endswith('/files'):
            # Remove /files from the end of the URL, since it gets added later
            return curseProject(addonpage[:-6])
        else:
            return curseProject(addonpage)

    # WowAce Project
    elif addonpage.startswith('https://www.wowace.com/projects/'):
        if addonpage.endswith('/files'):
            # Remove /files from the end of the URL, since it gets added later
            return wowAceProject(addonpage[:-6])
        else:
            return wowAceProject(addonpage)

    # Tukui
    elif addonpage.startswith('https://www.tukui.org/'):
        return tukui(addonpage)

    # Wowinterface
    elif addonpage.startswith('https://www.wowinterface.com/'):
        return wowinterface(addonpage)

    # Invalid page
    else:
        print('Invalid addon page.')


def getCurrentVersion(addonpage,version):
    # Curse
    if addonpage.startswith('https://www.curseforge.com/wow/addons/'):
        return getCurseVersion(addonpage,version)

    # Curse Project
    elif addonpage.startswith('https://wow.curseforge.com/projects/'):
        return getCurseProjectVersion(addonpage)

    # WowAce Project
    elif addonpage.startswith('https://www.wowace.com/projects/'):
        return getWowAceProjectVersion(addonpage)

    # Tukui
    elif addonpage.startswith('https://www.tukui.org/'):
        return getTukuiVersion(addonpage)

    # Wowinterface
    elif addonpage.startswith('https://www.wowinterface.com/'):
        return getWowinterfaceVersion(addonpage)

    # Invalid page
    else:
        print('Invalid addon page.')


def getAddonName(addonpage):
    # TODO : Replace URL remover with a regex
    addonName = addonpage.replace('https://mods.curse.com/addons/wow/', '')
    addonName = addonName.replace('https://www.curseforge.com/wow/addons/', '')
    addonName = addonName.replace('https://wow.curseforge.com/projects/', '')
    addonName = addonName.replace('https://www.wowinterface.com/downloads/', '')
    addonName = addonName.replace('https://www.wowace.com/projects/', '')
    addonName = addonName.replace('https://git.tukui.org/', '')
    if addonName.lower().find('+tukui') != -1:
        addonName = 'TukUI'
    if addonName.lower().find('+elvui') != -1:
        addonName = 'ElvUI'
    if addonName.endswith('/files'):
        addonName = addonName[:-6]
    return addonName


# Curse

def curse(addonpage, version):
    try:
        filePath = ''
        page = requests.get(addonpage + '/download')
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        # TODO This is last addon version regardless of game version
        match = re.search(r'PublicProjectDownload.countdown\(\"(?P<hash>[^<]+?)\"', contentString)
        if match:
            filePath = match.group('hash')

        # For different version, we have to retrieve another webpage
        page = requests.get(addonpage + '/files')
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        pattern = re.compile(r'<a data-action="file-link" href="(\S+)">\S+</a>.+?<div class="mr-2">\\r\\n(\S+).+?</div>'
                             , re.DOTALL)

        versions = re.finditer(pattern, contentString)
        for x in versions:
            if x.group(2).find(version) != -1:
                return "https://www.curseforge.com"+x.group(1).replace("files", "download")+"/file"
        # If no corresponding version has been found, return the last one
        return "https://www.curseforge.com"+filePath
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''

def getCurseVersion(addonpage, version):
    try:
        result = ''
        page = requests.get(addonpage + '/files')
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        # TODO This is last addon version regardless of game version
        match = re.search(r'<h3 class="text-primary-500 text-lg">(?P<hash>[^<]+?)</h3>', contentString)
        result = ''
        if match:
            result = match.group('hash')

        pattern = re.compile(r'<a data-action="file-link" href="\S+">(\S+)</a>.+?<div class="mr-2">\\r\\n(\S+).+?</div>'
                             , re.DOTALL)

        versions = re.finditer(pattern, contentString)
        for x in versions:
            if x.group(2).find(version) != -1:
                return x.group(1)
        # If no corresponding version has been found, return the last one
        return result
    except Exception:
        print('Failed to find version number for: ' + addonpage)
        return ''


# Curse Project

def curseProject(addonpage):
    try:
        # Apparently the Curse project pages are sometimes sending people to WowAce now.
        # Check if the URL forwards to WowAce and use that URL instead.
        page = requests.get(addonpage)
        page.raise_for_status()   # Raise an exception for HTTP errors
        if page.url.startswith('https://www.wowace.com/projects/'):
            return wowAceProject(page.url)
        return addonpage + '/files/latest'
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''


def getCurseProjectVersion(addonpage):
    try:
        page = requests.get(addonpage + '/files')
        if page.status_code == 404:
            # Maybe the project page got moved to WowAce?
            page = requests.get(addonpage)
            page.raise_for_status() # Raise an exception for HTTP errors
            page = requests.get(page.url + '/files') # page.url refers to the place where the last one redirected to
            page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        startOfTable = contentString.find('project-file-list-item')
        indexOfVer = contentString.find('data-name="', startOfTable) + 11  # first char of the version string
        endTag = contentString.find('">', indexOfVer)  # ending tag after the version string
        return contentString[indexOfVer:endTag].strip()
    except Exception:
        print('Failed to find version number for: ' + addonpage)
        return ''


# WowAce Project

def wowAceProject(addonpage):
    try:
        return addonpage + '/files/latest'
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''


def getWowAceProjectVersion(addonpage):
    try:
        page = requests.get(addonpage + '/files')
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        startOfTable = contentString.find('project-file-list-item')
        indexOfVer = contentString.find('data-name="', startOfTable) + 11  # first char of the version string
        endTag = contentString.find('">', indexOfVer)  # ending tag after the version string
        return contentString[indexOfVer:endTag].strip()
    except Exception:
        print('Failed to find version number for: ' + addonpage)
        return ''

# New TukUI implemntation

def tukui(addonpage):
    try:
        if '+' in addonpage: # Expected input format: "https://www.tukui.org+tukui"
            complement = addonpage.split('+')[1]
            addonpage = addonpage.split('+')[0]
        else:
            print('Failed to find a specific addon to get for elvui. Skipping...\n')
            return ''
        page = requests.get(addonpage+'download.php?ui='+complement.lower())
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        indexOfZiploc = contentString.find('<a href="/downloads/') + 9  # Will be the index of the first char of the url
        endQuote = contentString.find('"', indexOfZiploc)  # Will be the index of the ending quote after the url
        return 'https://www.tukui.org' + contentString[indexOfZiploc:endQuote]
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''

def getTukuiVersion(addonpage):
    try:
        if '+' in addonpage: # Expected input format: "https://www.tukui.org+tukui"
            complement = addonpage.split('+')[1]
            addonpage = addonpage.split('+')[0]
        else:
            print('Failed to find a specific addon to get for elvui. Skipping...\n')
            return ''
        page = requests.get(addonpage+'download.php?ui='+complement.lower())
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        indexOfZiploc = contentString.find('is <b class="Premium">') + 22  # Will be the index of the first char of the url
        endQuote = contentString.find('</b>', indexOfZiploc)  # Will be the index of the ending quote after the url
        return contentString[indexOfZiploc:endQuote]
    except Exception:
        print('Failed to find version number for: ' + addonpage)
        return ''

# Wowinterface

def wowinterface(addonpage):
    downloadpage = addonpage.replace('info', 'download')
    try:
        page = requests.get(downloadpage + '/download')
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        indexOfZiploc = contentString.find('Problems with the download? <a href="') + 37  # first char of the url
        endQuote = contentString.find('"', indexOfZiploc)  # ending quote after the url
        return contentString[indexOfZiploc:endQuote]
    except Exception:
        print('Failed to find downloadable zip file for addon. Skipping...\n')
        return ''


def getWowinterfaceVersion(addonpage):
    try:
        page = requests.get(addonpage)
        page.raise_for_status()   # Raise an exception for HTTP errors
        contentString = str(page.content)
        indexOfVer = contentString.find('id="version"') + 22  # first char of the version string
        endTag = contentString.find('</div>', indexOfVer)  # ending tag after the version string
        return contentString[indexOfVer:endTag].strip()
    except Exception:
        print('Failed to find version number for: ' + addonpage)
        return ''
