# ============================================================
# KCleaner - Version 2.7 by D. Lanik (2017)
# ------------------------------------------------------------
# Clean up Kodi
# ------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
# ============================================================

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import os
import shutil
import sqlite3
import json
import urllib2
import gzip
import urllib
import sys
import codecs
import pickle
from distutils.util import strtobool
from xml.dom import minidom

# ============================================================
# Define Sizes Class
# ============================================================


class Sizes():
    def __init__(self, subcat, cat, size):
        self.subcat = subcat
        self.cat = cat
        self.size = size

    def __repr__(self):
        return "%s %s %s" % (self.subcat, self.cat, self.size)

    def __str__(self):
        return "%s %s %s" % (self.subcat, self.cat, self.size)


# ============================================================
# Calculate how much space would be reclaimed
# ============================================================

def CalcDeleted():
    global __addon__
    global arr
    global ignoreAniGifs
    global ignore_existing_thumbs
    global ignore_packages

    TotalfileSize = 0.0
    fileSize = 0.0

    ignore_existing_thumbs = bool(strtobool(str(__addon__.getSetting('ignore_existing_thumbs').title())))
    ignore_packages = int(__addon__.getSetting('ignore_packages'))

    totSizeArr = []

    for j, entry in enumerate(arr):
        clear_cache_path = xbmc.translatePath(entry[1])

        if os.path.exists(clear_cache_path):
            anigPath = os.path.join(clear_cache_path, "animatedgifs")
            arccPath = os.path.join(xbmc.translatePath("special://temp"), "archive_cache")

            if entry[3] == 'thumbnails':
                dataBase = os.path.join(xbmc.translatePath("special://database/"), "Textures13.db")
                conn = sqlite3.connect(dataBase)
                c = conn.cursor()

            if entry[3] == 'packages' and ignore_packages > 0:
                plist = getPackages()

            for root, dirs, files in os.walk(clear_cache_path):
                if (root != anigPath and root != arccPath) or (root == anigPath and not ignoreAniGifs):
                    for f in files:
                        fileSize = os.path.getsize(os.path.join(root, f))

                        if entry[3] == 'packages' and ignore_packages > 0:
                            if f in plist:
                                TotalfileSize += fileSize

                        elif entry[3] == 'thumbnails' and ignore_existing_thumbs and not fast_thumb_check:
                            thumbFolder = os.path.split(root)[1]
                            thumbPath = thumbFolder + "/" + f

                            sqlstr = "SELECT * FROM texture WHERE cachedurl=" + "'" + thumbPath + "'"
                            c.execute(sqlstr)
                            data = c.fetchone()

                            if not data:
                                TotalfileSize += fileSize

                        elif entry[3] == 'addons':
                            if not entry[4]:
                                TotalfileSize += fileSize
                        else:
                            TotalfileSize += fileSize

                    if entry[2]:
                        for d in dirs:
                            if os.path.join(root, d) != anigPath and os.path.join(root, d) != arccPath:
                                TotalfileSize += getFolderSize(os.path.join(root, d))

            if entry[3] == 'thumbnails':
                conn.close()

            mess3 = " %0.2f " % ((TotalfileSize / (1048576.00000001)),)
            mess = entry[0] + mess3

            totSizeArr.append(Sizes(entry[0], entry[3], str(TotalfileSize)))
            TotalfileSize = 0.0

    addontot = 0.0
    custtot = 0.0
    atvtot = 0.0
    totalsize = 0.0

    msizes = []

    for i, line in enumerate(totSizeArr):
        if line.cat == 'addons':
            addontot += float(line.size)
            totalsize += addontot
        elif line.cat == 'custom':
            custtot += float(line.size)
            totalsize += custtot
        elif line.cat == 'atv':
            atvtot += float(line.size)
            totalsize += atvtot
        else:
            mess = " %0.2f " % ((float(line.size) / (1048576.00000001)),)
            msizes.append([line.cat, mess])
            totalsize += float(line.size)

    mess = " %0.2f " % ((addontot / (1048576.00000001)),)
    msizes.append(['addons', mess])

    mess = " %0.2f " % ((custtot / (1048576.00000001)),)
    msizes.append(['custom', mess])

    mess = " %0.2f " % ((atvtot / (1048576.00000001)),)
    msizes.append(['atv', mess])

    TotalfileSize = 0                                                 # get uninstalled addon data size
    data_path = xbmc.translatePath('special://profile/addon_data/')

    installedAddons, countInstalledAddons = getLocalAddons()
    addonData, intObjects = getLocalAddonDataFolders()
    for d in addonData:
        if d not in installedAddons:
            fullName = os.path.join(data_path, d)
            TotalfileSize += getFolderSize(fullName)

    mess = " %0.2f " % ((TotalfileSize / (1048576.00000001)),)
    msizes.append(['emptyaddon', mess])
    totalsize += float(TotalfileSize)

    mess = " %0.2f " % ((totalsize / (1048576.00000001)),)
    msizes.append(['total', mess])

    for i, line in enumerate(msizes):
        xbmc.log("KCLEANER >> CALCULATED SAVINGS >> " + str(line).encode('utf8'))

    return msizes

# ============================================================
# Change local path(s) in settings to special://
# ============================================================


def ProcessSpecial(iMode):
    global strEndMessage
    global __addon__

    __addon__.setSetting('lock', 'true')
    intCancel = 0
    intObjects = 0
    counter = 0
    intTot = 0

    strMess = __addon__.getLocalizedString(30118)                                    # Checking paths to be compacted...
    strMess2 = __addon__.getLocalizedString(30115)                                   # Checking...

    if iMode:
        progress = xbmcgui.DialogProgressBG()
    else:
        progress = xbmcgui.DialogProgress()

    progress.create(strMess, strMess2)

    userDataPath = xbmc.translatePath("special://userdata")

    for root, dirs, files in os.walk(userDataPath):
        for f in files:
            if get_extension(f) == "xml":
                intObjects += 1

    intObjects += 0.1

    for root, dirs, files in os.walk(userDataPath):
        for f in files:
            if get_extension(f) == "xml":
                if get_filename(f) == "settings" or root == userDataPath:
                    p = os.path.join(root, f)
                    pout = os.path.join(root, f + "_NEW")

                    strMess = __addon__.getLocalizedString(30025)             # Checking:
                    strMess2 = __addon__.getLocalizedString(30018)            # Compacted:

                    percent = (counter / intObjects) * 100

                    message1 = strMess + str(f)
                    message2 = strMess2 + str(int(counter)) + " / " + str(int(intObjects))

                    progress.update(int(percent), unicode(message1), unicode(message2))

                    if not iMode:
                        try:
                            if progress.iscanceled():
                                intCancel = 1
                                break
                        except Exception:
                            pass

                    fp = codecs.open(p, "r", "utf-8")

                    if os.path.isfile(pout):
                        try:
                            os.remove(pout)
                        except Exception:
                            xbmc.log("KCLEANER >> COULDN'T DELETE OLD _NEW FILE")

                    fpout = codecs.open(pout, "w", "utf-8")

                    wasChanged = False

                    for line in fp:
                        if userDataPath in line:
                            newline = line.replace(userDataPath, "special://userdata/")
                            newline = newline.replace("\\", "/")
                            xbmc.log("KCLEANER >> COMPACTING PATH: " + root.encode('utf8') + "\\" + f.encode('utf8'))
                            wasChanged = True
                        else:
                            newline = line

                        fpout.write(newline)

                    fp.close()
                    fpout.close()

                    counter += 1

                    if wasChanged:
                        intTot += 1
                        try:
                            if os.path.isfile(p + "_ORIG"):
                                os.remove(p + "_ORIG")
                            os.rename(p, p + "_ORIG")
                            os.rename(pout, p)
                            pass
                        except Exception:
                            xbmc.log("KCLEANER >> COULDN'T DELETE OR RENAME ORIGINAL FILE")
                    else:
                        try:
                            os.remove(pout)
                        except Exception:
                            xbmc.log("KCLEANER >> COULDN'T DELETE NEW FILE")

    if intTot > 0:
        strMess = __addon__.getLocalizedString(30139)             # Compacted settings paths:
        strEndMessage = strMess + " " + str(intTot) + "\n"
    else:
        strEndMessage = __addon__.getLocalizedString(30139) + " " + __addon__.getLocalizedString(30153) + "\n"      # Compacted settings paths: / # No paths compacted.

    progress.close()

    return intCancel, intTot

# ============================================================
# Clean texture database
# ============================================================


def CleanTextures(iMode):
    global __addon__
    global booDebug
    global strEndMessage

    __addon__.setSetting('lock', 'true')
    intCancel = 0
    intObjects = 0
    counter = 0

    strMess = __addon__.getLocalizedString(30114)                                    # Scanning Textures database...
    strMess2 = __addon__.getLocalizedString(30115)                                   # Checking...

    if iMode == 1:
        progress = xbmcgui.DialogProgressBG()
        progress.create(strMess, strMess2)
    elif iMode == 0:
        progress = xbmcgui.DialogProgress()
        progress.create(strMess, strMess2)

    dataBase = os.path.join(xbmc.translatePath("special://database/"), "Textures13.db")
    oldfileSize = os.path.getsize(dataBase)
    conn = sqlite3.connect(dataBase)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM texture")
    intObjects = c.fetchone()[0]
    intObjects += 0.1

    try:
        c.execute("SELECT * FROM texture")
        data = c.fetchall()
    except Exception as e:
        xbmc.log("KCLEANER >> SQL ERROR IN Textures13: " + str(e))
        data = None

    for d in data:
        recID = d[0]
        textureName = d[2].replace('/', os.sep)
        thumbPath = os.path.join(xbmc.translatePath("special://thumbnails"), textureName)
        fileName = xbmc.translatePath(d[1])

        strMess = __addon__.getLocalizedString(30116)             # Checking record ID:
        strMess2 = __addon__.getLocalizedString(30014)            # Deleted:

        percent = (counter / intObjects) * 100

        message1 = strMess + str(recID)
        message2 = strMess2 + str(int(counter)) + " / " + str(int(intObjects))

        if iMode < 2:
            progress.update(int(percent), unicode(message1), unicode(message2))

        if iMode == 0:
            try:
                if progress.iscanceled():
                    intCancel = 1
                    break
            except Exception:
                pass

        if not os.path.isfile(thumbPath):
            try:
                c.execute("DELETE FROM texture WHERE id=?", (recID,))
                conn.commit()

                c.execute("DELETE FROM sizes WHERE idtexture=?", (recID,))
                conn.commit()

                if booDebug:
                    xbmc.log("KCLEANER >> DELETED RECORD FROM DB: " + str(thumbPath))

                counter += 1
            except Exception as e:
                xbmc.log("KCLEANER >> SQL ERROR IN Textures13 DELETING ID: " + str(recID) + " >> " + str(e))

        if fileName.startswith("http://") or fileName.startswith("https://") or fileName.startswith("image://") or fileName.endswith("/transform?size=thumb"):
            pass
        else:
            if not os.path.isfile(fileName):
                try:
                    c.execute("DELETE FROM texture WHERE id=?", (recID,))
                    conn.commit()

                    c.execute("DELETE FROM sizes WHERE idtexture=?", (recID,))
                    conn.commit()

                    if booDebug:
                        xbmc.log("KCLEANER >> DELETED RECORD FROM DB: " + str(fileName))

                    counter += 1
                except Exception as e:
                    xbmc.log("KCLEANER >> SQL ERROR IN Textures13 DELETING ID: " + str(recID) + " >> " + str(e))

    conn.execute("VACUUM")
    conn.close()

    if counter > 0:
        newfileSize = os.path.getsize(dataBase)
        intTot = (oldfileSize - newfileSize) / 1048576.00000001
        strSaved = '%0.2f' % (intTot,)

        strMess = __addon__.getLocalizedString(30136)             # Deleted
        strMess2 = __addon__.getLocalizedString(30137)            # stale records from Textures13.db database
        strMess3 = __addon__.getLocalizedString(30112)            # Mb
        strEndMessage = strMess + " " + str(counter) + " " + strMess2 + " (" + strSaved + " " + strMess3 + ")\n"
    else:
        intTot = 0
        strEndMessage += (__addon__.getLocalizedString(30099) + ": ")          # Clean textures DB
        strEndMessage += __addon__.getLocalizedString(30152) + "\n"            # No records deleted

    if iMode < 2:
        progress.close()

    return intCancel, intTot

# ============================================================
# Textbox class
# ============================================================


def TextBoxes(heading, anounce):
    class TextBox():
        """Thanks to BSTRDMKR for this code:)"""
        WINDOW = 10147
        CONTROL_LABEL = 1
        CONTROL_TEXTBOX = 5                # constants

        def __init__(self, *args, **kwargs):
            xbmc.executebuiltin("ActivateWindow(%d)" % (self.WINDOW,))      # activate the text viewer window
            self.win = xbmcgui.Window(self.WINDOW)                          # get window
            xbmc.sleep(500)                                                 # give window time to initialize
            self.setControls()

        def setControls(self):
            self.win.getControl(self.CONTROL_LABEL).setLabel(heading)       # set heading
            try:
                f = open(anounce)
                text = f.read()
            except Exception:
                text = anounce
            self.win.getControl(self.CONTROL_TEXTBOX).setText(text)
            return

    TextBox()

# ============================================================
# Get extension
# ============================================================


def get_extension(filename):
    ext = os.path.splitext(filename)[1][1:].strip()
    return ext

# ============================================================
# Get filename
# ============================================================


def get_filename(filename):
    name = os.path.splitext(filename)[0].strip()
    return name

# ============================================================
# Delete Cache
# ============================================================


def DeleteFiles(cleanIt, iMode):
    global __addon__
    global arr
    global ignoreAniGifs
    global ignore_existing_thumbs
    global ignore_packages
    global strEndMessage
    global booDebug

    __addon__.setSetting('lock', 'true')
    intCancel = 0
    intObjects = 0
    count = 0
    TotalfileSize = 0.0
    fileSize = 0.0
    intTot = 0
    grandTotal = 0

    ignore_existing_thumbs = bool(strtobool(str(__addon__.getSetting('ignore_existing_thumbs').title())))
    ignore_packages = int(__addon__.getSetting('ignore_packages'))

    for j, entry in enumerate(arr):
        if entry[3] in cleanIt and not entry[4]:
            clear_cache_path = xbmc.translatePath(entry[1])
            if os.path.exists(clear_cache_path):
                for root, dirs, files in os.walk(clear_cache_path):
                    intObjects += len(files)

    strMess = __addon__.getLocalizedString(30011)                                    # Scanning for temporary files
    strMess2 = __addon__.getLocalizedString(30012)                                   # Checking paths...

    if iMode == 1:
        progress = xbmcgui.DialogProgressBG()
        progress.create(strMess, strMess2)
    elif iMode == 0:
        progress = xbmcgui.DialogProgress()
        progress.create(strMess, strMess2)

    intObjects += 0.1

    for j, entry in enumerate(arr):
        if entry[3] in cleanIt and not entry[4]:
            clear_cache_path = xbmc.translatePath(entry[1])

            if os.path.exists(clear_cache_path):
                anigPath = os.path.join(clear_cache_path, "animatedgifs")
                arccPath = os.path.join(xbmc.translatePath("special://temp"), "archive_cache")

                if entry[3] == 'thumbnails':
                    dataBase = os.path.join(xbmc.translatePath("special://database/"), "Textures13.db")
                    conn = sqlite3.connect(dataBase)
                    c = conn.cursor()

                if entry[3] == 'packages' and ignore_packages > 0:
                    plist = getPackages()

                for root, dirs, files in os.walk(clear_cache_path):
                    if (root != anigPath and root != arccPath) or (root == anigPath and not ignoreAniGifs):
                        for f in files:
                            strMess = __addon__.getLocalizedString(30013)             # Cleaning:
                            strMess2 = __addon__.getLocalizedString(30014)            # Deleted:

                            percent = (count / intObjects) * 100

                            message1 = strMess + entry[0]
                            message2 = strMess2 + str(int(count)) + " / " + str(int(intObjects))

                            if iMode < 2:
                                progress.update(int(percent), unicode(message1), unicode(message2))

                            if iMode == 0:
                                try:
                                    if progress.iscanceled():
                                        intCancel = 1
                                        break
                                except Exception:
                                    pass

                            fileSize = os.path.getsize(os.path.join(root, f))

                            if entry[3] == 'packages' and ignore_packages > 0:
                                if f in plist:
                                    try:
                                        os.unlink(os.path.join(root, f))
                                        TotalfileSize += fileSize
                                        if booDebug:
                                            xbmc.log("KCLEANER >> DELETED >>" + f.encode('utf8'))
                                    except Exception as e:
                                        xbmc.log("KCLEANER >> CAN NOT DELETE FILE >>" + f.encode('utf8') + "<< ERROR: " + str(e))

                                    count += 1

                            elif entry[3] == 'thumbnails' and ignore_existing_thumbs:
                                thumbFolder = os.path.split(root)[1]
                                thumbPath = thumbFolder + "/" + f

                                sqlstr = "SELECT * FROM texture WHERE cachedurl=" + "'" + thumbPath + "'"
                                c.execute(sqlstr)
                                data = c.fetchone()

                                if not data:
                                    try:
                                        os.unlink(os.path.join(root, f))
                                        TotalfileSize += fileSize
                                        if booDebug:
                                            xbmc.log("KCLEANER >> DELETED >>" + f.encode('utf8'))
                                    except Exception as e:
                                        xbmc.log("KCLEANER >> CAN NOT DELETE FILE >>" + f.encode('utf8') + "<< ERROR: " + str(e))

                                    count += 1

                            else:
                                try:
                                    os.unlink(os.path.join(root, f))
                                    TotalfileSize += fileSize
                                    if booDebug:
                                        xbmc.log("KCLEANER >> DELETED >>" + f.encode('utf8'))
                                except Exception as e:
                                    xbmc.log("KCLEANER >> CAN NOT DELETE FILE >>" + f.encode('utf8') + "<< ERROR: " + str(e))

                                count += 1

                        if entry[2]:
                            for d in dirs:
                                if os.path.join(root, d) != anigPath and os.path.join(root, d) != arccPath:
                                    try:
                                        shutil.rmtree(os.path.join(root, d))
                                        if booDebug:
                                            xbmc.log("KCLEANER >> DELETED >>" + d.encode('utf8'))
                                    except Exception as e:
                                        xbmc.log("KCLEANER >> CAN NOT DELETE FOLDER >>" + d.encode('utf8') + "<< ERROR: " + str(e))
                    else:
                        pass

                if entry[3] == 'thumbnails':
                    conn.close()

                if TotalfileSize > 0:
                    mess1 = __addon__.getLocalizedString(30113)                        # cleaned:
                    mess2 = __addon__.getLocalizedString(30112)                        # Mb:
                    mess3 = " %0.2f " % ((TotalfileSize / (1048576.00000001)),)

                    mess = entry[3].title().encode('utf8') + " (" + entry[0].encode('utf8') + "): " + entry[0].encode('utf8') + mess1 + mess3 + mess2
                    strEndMessage += (mess + "\n")

                    xbmc.log("KCLEANER >> CLEANING >> " + mess.encode('utf8'))
                    intTot = TotalfileSize / 1048576.00000001
                    grandTotal += TotalfileSize
                else:
                    strEndMessage += (entry[3].title().encode('utf8') + " (" + entry[0].encode('utf8') + ") : ")
                    strEndMessage += __addon__.getLocalizedString(30150) + "\n"                   # No files deleted

                TotalfileSize = 0.0

    if iMode < 2:
        progress.close()

    return intCancel, intTot

# ============================================================
# Get All Packages
# ============================================================


def getPackages():
    global ignore_packages

    packAge = []

    clear_cache_path = xbmc.translatePath('special://home/addons/packages')
    if os.path.exists(clear_cache_path):
        for root, dirs, files in os.walk(clear_cache_path):
            for e, f in enumerate(files):
                name = os.path.splitext(f)[0]
                version = name.rsplit('-', 1)
                dt = os.path.getmtime(os.path.join(root, f))

                packAge.append([version[0], version[1], dt, f])

        uniquePackage = set()

        for e, item in enumerate(packAge):
            uniquePackage.add(packAge[e][0])

        deletePackages = []

        for item in uniquePackage:
            strVers = []
            for e, lst in enumerate(packAge):
                if packAge[e][0] == item:
                    strVers.append(packAge[e])

            strVers.sort(key=lambda date: packAge[e][2])
            strVers.reverse()

            for i, vv in enumerate(strVers):
                if i >= ignore_packages:
                    deletePackages.append(vv[3])

    return deletePackages

# ============================================================
# Compact DBs
# ============================================================


def CompactDatabases(iMode):
    global __addon__
    global strEndMessage

    __addon__.setSetting('lock', 'true')
    intCancel = 0
    intObjects = 0
    counter = 0

    intTot = 0
    GreatTotal = 0

    strMess = __addon__.getLocalizedString(30016)                                    # Scanning for databases
    strMess2 = __addon__.getLocalizedString(30012)                                   # Checking paths...

    if iMode == 1:
        progress = xbmcgui.DialogProgressBG()
        progress.create(strMess, strMess2)
    elif iMode == 0:
        progress = xbmcgui.DialogProgress()
        progress.create(strMess, strMess2)

    dbPath = xbmc.translatePath("special://database/")
    intObjects = 0

    if os.path.exists(dbPath):
        files = ([f for f in os.listdir(dbPath) if f.endswith('.db') and os.path.isfile(os.path.join(dbPath, f))])
        intObjects = len(files)
        intObjects += 0.1

        for f in files:
            strMess = __addon__.getLocalizedString(30017)             # Compacting:
            strMess2 = __addon__.getLocalizedString(30018)            # Compacted:

            percent = (counter / intObjects) * 100

            message1 = strMess + f
            message2 = strMess2 + str(int(counter)) + " / " + str(int(intObjects))

            if iMode < 2:
                progress.update(int(percent), unicode(message1), unicode(message2))

            if iMode == 0:
                try:
                    if progress.iscanceled():
                        intCancel = 1
                        break
                except Exception:
                    pass

            fileSizeBefore = os.path.getsize(os.path.join(dbPath, f))
            CompactDB(os.path.join(dbPath, f))
            fileSizeAfter = os.path.getsize(os.path.join(dbPath, f))

            xbmc.log("KCLEANER >> COMPACTED DATABASE >>" + f.encode('utf8'))

            if fileSizeAfter != fileSizeBefore:
                mess1 = __addon__.getLocalizedString(30110)             # Database
                mess2 = __addon__.getLocalizedString(30111)             # compacted:
                mess3 = " %0.2f " % (((fileSizeBefore - fileSizeAfter) / (1048576.00000001)),)
                mess4 = __addon__.getLocalizedString(30112)             # Mb
                strEndMessage += mess1 + f.encode('utf8') + mess2 + mess3 + mess4 + "\n"

                intTot += (fileSizeBefore - fileSizeAfter) / 1048576.00000001
                GreatTotal += (fileSizeBefore - fileSizeAfter)
            counter += 1

    if iMode < 2:
        progress.close()

    if GreatTotal == 0:
        intTot = 0
        strEndMessage += __addon__.getLocalizedString(30151) + "\n"                       # No database compacted.

    return intCancel, intTot

# ============================================================
# Compact DB
# ============================================================


def CompactDB(SQLiteFile):
    conn = sqlite3.connect(SQLiteFile)
    conn.execute("VACUUM")
    conn.close()

# ============================================================
# Get list of repositories
# ============================================================


def getLocalRepos():
    global booDebug

    installedRepos = []
    repos = getJson("Addons.GetAddons", "type", "xbmc.addon.repository", "addons")
    for f in repos:
        installedRepos.append(f["addonid"])
        if booDebug:
            xbmc.log("KCLEANER >> INSTALLED REPOS >>" + f["addonid"].encode('utf8'))

    count = len(installedRepos)

    return installedRepos, count

# ============================================================
# Get list of installed addons
# ============================================================


def getLocalAddons():
    global booDebug

    installedAddons = []
    addons = getJson("Addons.GetAddons", "type", "unknown", "addons")
    for f in addons:
        if f["type"] != "xbmc.addon.repository":
            installedAddons.append(f["addonid"])
            if booDebug:
                xbmc.log("KCLEANER >> INSTALLED ADDONS >>" + f["addonid"].encode('utf8'))

    count = len(installedAddons)

    return installedAddons, count

# ============================================================
# Get list of addon data folders
# ============================================================


def getLocalAddonDataFolders():
    addonData = []

    data_path = xbmc.translatePath('special://profile/addon_data/')

    for item in os.listdir(data_path):
        if os.path.isdir(os.path.join(data_path, item)):
            addonData.append(item)

    count = len(addonData)

    return addonData, count

# ============================================================
# Delete data folders for nonexistant (uninstalled) addons
# ============================================================


def deleteAddonData(iMode):
    global __addon__
    global strEndMessage

    __addon__.setSetting('lock', 'true')
    intCancel = 0
    counter = 0
    TotalfileSize = 0
    deleted = 0

    strMess = __addon__.getLocalizedString(30117)                                    # Checking unused data folders
    strMess2 = __addon__.getLocalizedString(30012)                                   # Checking paths...

    if iMode == 1:
        progress = xbmcgui.DialogProgressBG()
        progress.create(strMess, strMess2)
    elif iMode == 0:
        progress = xbmcgui.DialogProgress()
        progress.create(strMess, strMess2)

    data_path = xbmc.translatePath('special://profile/addon_data/')

    installedAddons, countInstalledAddons = getLocalAddons()
    addonData, intObjects = getLocalAddonDataFolders()
    intObjects += 0.1

    for d in addonData:
        strMess = __addon__.getLocalizedString(30025)             # Checking:
        strMess2 = __addon__.getLocalizedString(30014)            # Deleted:

        percent = (counter / intObjects) * 100

        message1 = strMess + str(d)
        message2 = strMess2 + str(int(deleted)) + " / " + str(int(intObjects))

        if iMode < 2:
            progress.update(int(percent), unicode(message1), unicode(message2))

        if iMode == 0:
            try:
                if progress.iscanceled():
                    intCancel = 1
                    break
            except Exception:
                pass

        if d not in installedAddons:
            fullName = os.path.join(data_path, d)
            TotalfileSize += getFolderSize(fullName)

            try:
                shutil.rmtree(fullName)
                xbmc.log("KCLEANER >> DELETING UNUSED ADDON DATA FOLDER >>" + fullName.encode('utf8'))
                deleted += 1
            except Exception as e:
                xbmc.log("KCLEANER >> ERROR DELETING UNUSED ADDON DATA FOLDER: " + str(e))

        counter += 1

    if TotalfileSize > 0:
        mess1 = __addon__.getLocalizedString(30113)                        # cleaned:
        mess2 = __addon__.getLocalizedString(30112)                        # Mb:
        mess3 = " %0.2f " % ((TotalfileSize / (1048576.00000001)),)

        mess = __addon__.getLocalizedString(30100) + mess1 + mess3 + mess2             # Unused addon data folders
        strEndMessage += (mess + "\n")
    else:
        strEndMessage += (__addon__.getLocalizedString(30100) + ": ")                  # Unused addon data folders
        strEndMessage += __addon__.getLocalizedString(30150) + "\n"                    # No files deleted

    if iMode < 2:
        progress.close()

    return intCancel, (TotalfileSize / 1048576.00000001)

# ============================================================
# Get folder size
# ============================================================


def getFolderSize(folder):
    total_size = os.path.getsize(folder)

    for item in os.listdir(folder):
        itempath = os.path.join(folder, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += getFolderSize(itempath)

    return total_size

# ============================================================
# Get Kodi data by json
# ============================================================


def getJson(method, param1, param2, retname):
    command = '''{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "%s",
    "params": {
        "%s": "%s"
        }
    }'''

    result = xbmc.executeJSONRPC(command % (method, param1, param2))
    py = json.loads(result)
    if 'result' in py and retname in py['result']:
        a = py['result'][retname]
        return a
    else:
        raise ValueError

# ============================================================
# Check Addons
# ============================================================


def ProcessAddons(iMode):
    global booDebug
    global strEndMessage

    intCancel = 0
    intObjects = 0
    c = 0

    strMess = __addon__.getLocalizedString(30019)                                    # Scanning for repositories
    strMess2 = __addon__.getLocalizedString(30012)                                   # Checking paths...

    if iMode:
        progress = xbmcgui.DialogProgressBG()
    else:
        progress = xbmcgui.DialogProgress()

    progress.create(strMess, strMess2)

    repos, intObjects = getLocalRepos()
    AddonsInstalled, intObjAddons = getLocalAddons()

    intObjects += intObjAddons
    intObjects += 0.1

    strMess = __addon__.getLocalizedString(30025)             # Checking:
    strMess2 = __addon__.getLocalizedString(30026)            # Checked:

    AddonsInRepo = []

    for r in repos:
        if r == "repository.xbmc.org":
            repoxml = os.path.join(xbmc.translatePath("special://xbmc"), "addons", r, "addon.xml")
        else:
            repoxml = os.path.join(xbmc.translatePath("special://home"), "addons", r, "addon.xml")

        percent = (c / intObjects) * 100

        message1 = strMess + r
        message2 = strMess2 + str(int(c)) + " / " + str(int(intObjects))

        progress.update(int(percent), unicode(message1), unicode(message2))

        if not iMode:
            try:
                if progress.iscanceled():
                    intCancel = 1
                    break
            except Exception:
                pass

        AddonsInRepo += GetAddonsInRepo(repoxml, r)

        c += 1

    for a in AddonsInstalled:
        percent = (c / intObjects) * 100

        message1 = strMess + a
        message2 = strMess2 + str(int(c)) + " / " + str(int(intObjects))

        progress.update(int(percent), unicode(message1), unicode(message2))

        if not iMode:
            try:
                if progress.iscanceled():
                    intCancel = 1
                    break
            except Exception:
                pass

        if os.path.isdir(os.path.join(xbmc.translatePath("special://xbmc"), "addons", a)):
            continue

        if a in AddonsInRepo:
            xbmc.log("KCLEANER >> ADDON >> " + a.encode('utf8') + " >> FOUND")
        else:
            xbmc.log("KCLEANER >> ADDON >> " + a.encode('utf8') + " >> IS IN NO REPOSITORY")
            mess1 = "IS IN NO REPOSITORY"  # __addon__.getLocalizedString(30121)             # IS IN NO REPOSITORY
            strEndMessage += a + " [B][COLOR red]" + mess1 + "[/B][/COLOR]\n"

        c += 1

    progress.close()

    return intCancel

# ============================================================
# Check Repos
# ============================================================


def ProcessRepos(iMode):
    global booDebug
    global strEndMessage

    intCancel = 0
    intObjects = 0
    c = 0

    strMess = __addon__.getLocalizedString(30019)                                    # Scanning for repositories
    strMess2 = __addon__.getLocalizedString(30012)                                   # Checking paths...

    if iMode:
        progress = xbmcgui.DialogProgressBG()
    else:
        progress = xbmcgui.DialogProgress()

    progress.create(strMess, strMess2)

    repos, intObjects = getLocalRepos()
    AddonsInstalled, intObjAddons = getLocalAddons()

    intObjects += 0.1

    for r in repos:
        if r == "repository.xbmc.org":
            repoxml = os.path.join(xbmc.translatePath("special://xbmc"), "addons", r, "addon.xml")
        else:
            repoxml = os.path.join(xbmc.translatePath("special://home"), "addons", r, "addon.xml")

        xbmc.log("KCLEANER >> PROCESSING REPO >>" + r.encode('utf8'))

        strMess = __addon__.getLocalizedString(30025)             # Checking:
        strMess2 = __addon__.getLocalizedString(30026)            # Checked:

        percent = (c / intObjects) * 100

        message1 = strMess + r
        message2 = strMess2 + str(int(c)) + " / " + str(int(intObjects))

        progress.update(int(percent), unicode(message1), unicode(message2))

        if not iMode:
            try:
                if progress.iscanceled():
                    intCancel = 1
                    break
            except Exception:
                pass

        AddonsInRepo = GetAddonsInRepo(repoxml, r)

        if len(AddonsInRepo) == 0:
            xbmc.log("KCLEANER >> REPO >> " + r + " >> " + repoxml.encode('utf8') + " >> EMPTY OR ERROR")
            mess1 = __addon__.getLocalizedString(30120)             # EMPTY OR ERROR READING
            strEndMessage += r + " [B][COLOR red]" + mess1 + "[/B][/COLOR]\n"
        else:
            similar = []
            for tup in AddonsInstalled:
                if tup in AddonsInRepo:
                    similar.append(tup)

            if len(similar) == 0:
                xbmc.log("KCLEANER >> REPO >> " + r.encode('utf8') + " >> CONTAINS NO LOCAL ADDONS")
                mess1 = __addon__.getLocalizedString(30121)             # CONTAINS NO LOCAL ADDONS
                strEndMessage += r + " [B][COLOR red]" + mess1 + "[/B][/COLOR]\n"
            else:
                if booDebug:
                    for i in similar:
                        xbmc.log("KCLEANER >> REPO >> " + r.encode('utf8') + " >> CONTAINS >>" + i.encode('utf8'))

        c += 1

    progress.close()

    return intCancel

# ============================================================
# Get list of addons in repository
# ============================================================


def GetAddonsInRepo(netxml, repo):
    global booDebug

    allAddonsInRepo = []

    if os.path.exists(netxml):
        if booDebug:
            xbmc.log("KCLEANER >> LOCAL XML EXISTS >>" + netxml.encode('utf8'))

        repopath = getRepoPath(netxml)

        if not repopath and booDebug:
            xbmc.log("KCLEANER >> INFO TAG NOT FOUND IN REPO >>" + netxml.encode('utf8'))

        for ri in repopath:
            id = getPathAddons(ri, repo)

            for addon in id:
                allAddonsInRepo.append(addon)
                if booDebug:
                    xbmc.log("KCLEANER >> ADDON >>" + addon.encode('utf8'))

    else:
        if booDebug:
            xbmc.log("KCLEANER >> LOCAL XML DOES NOT EXIST >>" + netxml.encode('utf8'))

    return allAddonsInRepo

# ============================================================
# Get repository path(s) from xml
# ============================================================


def getRepoPath(xmlFile):
    global booDebug

    XmlInfo = []

    xmldoc = minidom.parse(xmlFile)

    infoTag = xmldoc.getElementsByTagName("info")

    for r in infoTag:
        try:
            XmlInfo.append(r.childNodes[0].nodeValue.strip())
            if booDebug:
                xbmc.log("KCLEANER >> REPO PATHS >>" + r.childNodes[0].nodeValue.encode('utf8'))
        except Exception as e:
            xbmc.log("KCLEANER >> ERROR REPO PATHS >>" + str(e).encode('utf-8'))

    return XmlInfo

# ============================================================
# Get addons from xml
# ============================================================


def getPathAddons(xmlFile, repo):
    global booDebug

    XmlInfo = []

    try:
        req = urllib2.Request(xmlFile)
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        httpdata = response.read()
        response.close()

    except Exception as e:
        xbmc.log("KCLEANER >> ERROR >>" + str(e).encode('utf-8'))
        return ""

    if get_extension(xmlFile) == "gz":
        gzFile = os.path.join(xbmc.translatePath('special://temp'), 'addon.gz')
        with open(gzFile, 'wb') as output:
            output.write(httpdata)

        f = gzip.GzipFile(gzFile, 'rb')
        httpdata = f.read()
        f.close()

    try:
        xmldoc = minidom.parseString(httpdata)
    except Exception as e:
        xbmc.log("KCLEANER >> ERROR PARSING REPO >> " + str(e).encode('utf-8'))
        return ""

    infoTag = xmldoc.getElementsByTagName("addon")

    for r in infoTag:
        addon = r.attributes["id"].value.strip()
        if addon != repo:
            XmlInfo.append(addon)
            if booDebug:
                xbmc.log("KCLEANER >> REPO-ADDON-LIST >>" + addon)

    return XmlInfo


# ============================================================
# Get settings
# ============================================================

def GetSettings():
    global ignoreAniGifs
    global booDebug
    global booBackgroundRun
    global ignore_existing_thumbs
    global ignore_packages
    global ignore1
    global ignore2
    global ignore3
    global ignore4
    global ignore5
    global ignore6
    global ignore7
    global ignore8
    global ignore9
    global ignoreA
    global ignoreB
    global ignoreC
    global numberOfPaths
    global path_1
    global path_2
    global path_3
    global path_4
    global fast_thumb_check

    ignoreAniGifs = bool(strtobool(str(__addon__.getSetting('ignore0').title())))
    booDebug = bool(strtobool(str(__addon__.getSetting('debug').title())))
    booBackgroundRun = bool(strtobool(str(__addon__.getSetting('autoclean').title())))

    ignore1 = bool(strtobool(str(__addon__.getSetting('ignore1').title())))
    ignore2 = bool(strtobool(str(__addon__.getSetting('ignore2').title())))
    ignore3 = bool(strtobool(str(__addon__.getSetting('ignore3').title())))
    ignore4 = bool(strtobool(str(__addon__.getSetting('ignore4').title())))
    ignore5 = bool(strtobool(str(__addon__.getSetting('ignore5').title())))
    ignore6 = bool(strtobool(str(__addon__.getSetting('ignore6').title())))
    ignore7 = bool(strtobool(str(__addon__.getSetting('ignore7').title())))
    ignore8 = bool(strtobool(str(__addon__.getSetting('ignore8').title())))
    ignore9 = bool(strtobool(str(__addon__.getSetting('ignore9').title())))
    ignoreA = bool(strtobool(str(__addon__.getSetting('ignoreA').title())))
    ignoreB = bool(strtobool(str(__addon__.getSetting('ignoreB').title())))
    ignoreC = bool(strtobool(str(__addon__.getSetting('ignoreC').title())))
    ignore_existing_thumbs = bool(strtobool(str(__addon__.getSetting('ignore_existing_thumbs').title())))
    fast_thumb_check = bool(strtobool(str(__addon__.getSetting('fast_thumb_check').title())))
    ignore_packages = int(__addon__.getSetting('ignore_packages'))
    numberOfPaths = int(__addon__.getSetting('numberOfPaths'))

    path_1 = __addon__.getSetting('path_1')
    path_2 = __addon__.getSetting('path_2')
    path_3 = __addon__.getSetting('path_3')
    path_4 = __addon__.getSetting('path_4')

# ============================================================
# Display results of cleaning
# ============================================================


def showResults():
    global __addon__
    global totalSizes

    totalSizes = CalcDeleted()
    fp = open(os.path.join(__addondir__, "shared.pkl"), "w")
    pickle.dump(totalSizes, fp)
    fp.close()

    if intCancel == 0:
        header = "[B][COLOR red]" + __addon__.getLocalizedString(30133) + "[/B][/COLOR]"             # Cleanup report:
        TextBoxes(header, strEndMessage)
    elif intCancel == 1:
        strMess = __addon__.getLocalizedString(30030)                                     # Cleanup [COLOR red]interrupted[/COLOR].
        xbmc.executebuiltin("XBMC.Notification(%s,%s,5000,%s)" % (__addonname__.encode('utf8'), strMess, __addon__.getAddonInfo('icon')))
    elif intCancel == 2:
        pass
    else:
        strMess = __addon__.getLocalizedString(30031)                                     # Cleanup [COLOR red]done[/COLOR].
        xbmc.executebuiltin("XBMC.Notification(%s,%s,2000,%s)" % (__addonname__.encode('utf8'), strMess, __addon__.getAddonInfo('icon')))

    __addon__.setSetting('lock', 'false')

    while True:
        xbmc.sleep(200)
        ActDialog = xbmcgui.getCurrentWindowDialogId()

        if ActDialog != 10147:
            break

    xbmc.sleep(100)
    xbmc.executebuiltin('Container.Refresh')
    xbmc.log("KCLEANER >> FINISHED")


# ============================================================
# def Main menu
# ============================================================

def mainMenu():
    global __addon__
    global totalSizes

    xbmc.executebuiltin("Container.SetViewMode(500)")

    addDir(__addon__.getLocalizedString(30020) + " (" + str(totalSizes[7][1]) + __addon__.getLocalizedString(30112) + ")", 'url', 1, os.path.join(mediaPath, "folder_clean.png"))        # Clean
    addDir(__addon__.getLocalizedString(30005), 'url', 2, os.path.join(mediaPath, "folder_db.png"))           # Databases
    addItem(__addon__.getLocalizedString(30027), 'url', 4, os.path.join(mediaPath, "compact.png"))            # Clean All + Compact DBs
    addDir(__addon__.getLocalizedString(30006), 'url', 3, os.path.join(mediaPath, "folder_check.png"))        # Checks
    addItem(__addon__.getLocalizedString(30164), 'url', 40, os.path.join(mediaPath, "paths.png"))             # Compact settings paths to special://
    addItem(__addon__.getLocalizedString(30022), 'url', 5, os.path.join(mediaPath, "settings.png"))           # Settings

# ============================================================
# def Clean menu
# ============================================================


def CleanMenu():
    global __addon__
    global totalSizes
    global ignore_existing_thumbs

    xbmc.executebuiltin("Container.SetViewMode(500)")

    addItem(__addon__.getLocalizedString(30160) + " (" + str(totalSizes[0][1]) + __addon__.getLocalizedString(30112) + ")",
            'url', 10, os.path.join(mediaPath, "clean.png"))    # Clean Cache
    addItem(__addon__.getLocalizedString(30161) + " (" + str(totalSizes[1][1]) + __addon__.getLocalizedString(30112) + ")",
            'url', 11, os.path.join(mediaPath, "clean.png"))    # Clean Packages

    ignore_existing_thumbs = bool(strtobool(str(__addon__.getSetting('ignore_existing_thumbs').title())))

    if ignore_existing_thumbs:
        if fast_thumb_check:
            mess = __addon__.getLocalizedString(30172)
        else:
            mess = __addon__.getLocalizedString(30171)
    else:
        mess = __addon__.getLocalizedString(30170)

    addItem(__addon__.getLocalizedString(30162) + " (" + str(totalSizes[2][1]) + __addon__.getLocalizedString(30112) + ") " + mess,
            'url', 12, os.path.join(mediaPath, "clean.png"))    # Clean Thumbnails
    addItem(__addon__.getLocalizedString(30163) + " (" + str(totalSizes[3][1]) + __addon__.getLocalizedString(30112) + ")",
            'url', 13, os.path.join(mediaPath, "clean.png"))    # Clean Add-ons

    numberOfPaths = int(__addon__.getSetting('numberOfPaths'))
    if numberOfPaths > 0:
        addItem(__addon__.getLocalizedString(30044) + " (" + str(totalSizes[4][1]) + __addon__.getLocalizedString(30112) + ")",
                'url', 15, os.path.join(mediaPath, "clean.png"))    # Custom paths

    addItem(__addon__.getLocalizedString(30100) + " (" + str(totalSizes[5][1]) + __addon__.getLocalizedString(30112) + ")",
            'url', 14, os.path.join(mediaPath, "clean.png"))    # Unused addon data folders

    if os.path.exists('/private/var/mobile/Library/Caches/AppleTV/Video/Other'):
        addItem(__addon__.getLocalizedString(30101) + " (" + str(totalSizes[6][1]) + __addon__.getLocalizedString(30112) + ")",
                'url', 16, os.path.join(mediaPath, "clean.png"))    # ATV

    addItem(__addon__.getLocalizedString(30004) + " (" + str(totalSizes[7][1]) + __addon__.getLocalizedString(30112) + ")",
            'url', 17, os.path.join(mediaPath, "clean.png"))    # Clean All

# ============================================================
# def Databases menu
# ============================================================


def DatabasesMenu():
    global __addon__

    xbmc.executebuiltin("Container.SetViewMode(500)")

    addItem(__addon__.getLocalizedString(30003), 'url', 20, os.path.join(mediaPath, "db.png"))                # Clean + Compact Textures DB
    addItem(__addon__.getLocalizedString(30023), 'url', 21, os.path.join(mediaPath, "db.png"))                # Compact all databases

# ============================================================
# def Checks menu
# ============================================================


def ChecksMenu():
    global __addon__

    xbmc.executebuiltin("Container.SetViewMode(500)")

    addItem(__addon__.getLocalizedString(30024), 'url', 30, os.path.join(mediaPath, "check.png"))             # Check for unused repositories
    addItem(__addon__.getLocalizedString(30001), 'url', 31, os.path.join(mediaPath, "check.png"))             # Check for addons without repo

# ============================================================
# Add to menues - link
# ============================================================


def addLink(name, url, iconimage):
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': iconimage})
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
    return ok


# ============================================================
# Add to menues - dir
# ============================================================

def addDir(name, url, mode, iconimage):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': iconimage})
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


# ============================================================
# Add to menues - item
# ============================================================

def addItem(name, url, mode, iconimage):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': iconimage})
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
    return ok

# ============================================================
# Parse choice
# ============================================================


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param

# ============================================================
# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
# ============================================================


__addon__ = xbmcaddon.Addon(id='script.kcleaner')
__addonwd__ = xbmc.translatePath(__addon__.getAddonInfo('path').decode("utf-8"))
__addondir__ = xbmc.translatePath(__addon__.getAddonInfo('profile').decode('utf8'))
__addonname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')

mediaPath = os.path.join(__addonwd__, 'media')

xbmc.log("KCLEANER >> STARTED VERSION %s" % (__version__))

ignore1 = False
ignore2 = False
ignore3 = False
ignore4 = False
ignore5 = False
ignore6 = False
ignore7 = False
ignore8 = False
ignore9 = False
ignoreA = False
ignoreB = False
ignoreC = False
ignoreD = False

ignore_existing_thumbs = False
fast_thumb_check = False
ignoreAniGifs = False
ignore_packages = 0
booDebug = False
booBackgroundRun = False
numberOfPaths = 0

path_1 = ""
path_2 = ""
path_3 = ""
path_4 = ""

mess = ""
strEndMessage = ""
arr = []

GetSettings()

arr.append(['Cache', 'special://home/cache', True, "cache", False])
if os.path.join(xbmc.translatePath('special://temp'), "") != os.path.join(xbmc.translatePath('special://home/cache'), ""):
    arr.append(['Temp', 'special://temp', True, "cache", False])
arr.append(['Packages', 'special://home/addons/packages', True, "packages", False])
arr.append(['Thumbnails', 'special://thumbnails', False, "thumbnails", False])

numberOfPaths = int(__addon__.getSetting('numberOfPaths'))
if numberOfPaths > 0:
    for x in range(1, numberOfPaths+1):
        pathnr = "path_" + str(x)
        pp = __addon__.getSetting(pathnr)
        if os.path.exists(pp):
            if x == 1:
                arr.append(["Custom Paths", pp, True, "custom", False])
            else:
                arr.append(["Custom Paths (" + str(x) + ")", pp, True, "custom", False])

arr.append(['Custom Paths (5)', '/dummy/dummy/dummy', False, "custom", False])

arr.append(['ADDONS (!)', '/dummy/dummy/dummy', False, "addons", False])

arr.append(['WTF', 'special://profile/addon_data/plugin.video.whatthefurk/cache', True, "addons", ignore1])
arr.append(['4oD', 'special://profile/addon_data/plugin.video.4od/cache', True, "addons", ignore2])
arr.append(['BBC iPlayer', 'special://profile/addon_data/plugin.video.iplayer/iplayer_http_cache', True, "addons", ignore3])
arr.append(['Simple Downloader', 'special://profile/addon_data/script.module.simple.downloader', True, "addons", ignore4])
arr.append(['ITV', 'special://profile/addon_data/plugin.video.itv/Images', True, "addons", ignore5])
arr.append(['MP3 Streams', 'special://profile/addon_data/plugin.audio.mp3streams/temp_dl', True, "addons", ignore6])
arr.append(['ArtistSlideshow', 'special://profile/addon_data/script.artistslideshow/ArtistInformation', True, "addons", ignore7])
arr.append(['ArtistSlideshow (Images)', 'special://profile/addon_data/script.artistslideshow/ArtistSlideshow', True, "addons", ignore7])
arr.append(['Titlovi', 'special://profile/addon_data/service.subtitles.titlovi/temp', True, "addons", ignore8])
arr.append(['Titulky', 'special://profile/addon_data/service.subtitles.titulky.com/temp', True, "addons", ignore9])
arr.append(['Artwork Downloader', 'special://profile/addon_data/script.artwork.downloader/temp', True, "addons", ignoreA])
arr.append(['Spotitube', 'special://profile/addon_data/plugin.video.spotitube/cache', True, "addons", ignoreB])
arr.append(['Retrospect', 'special://profile/addon_data/net.rieter.xot/cache', True, "addons", ignoreC])
arr.append(['Database Pre-Wash Scrub', 'special://userdata/Database/backups', True, "addons", ignoreD])
arr.append(['ATV', '/dummy/dummy/dummy', False, "atv", False])
if os.path.exists('/private/var/mobile/Library/Caches/AppleTV/Video/Other'):
    arr.append(['ATV', '/private/var/mobile/Library/Caches/AppleTV/Video/Other', True, "atv", False])
    arr.append(['ATV (LocalAndRental)', '/private/var/mobile/Library/Caches/AppleTV/Video/LocalAndRental', True, "atv", False])

actionToken = []
totalSizes = []

actionToken.append(["cache"])                                                           # 0 CACHE
actionToken.append(["packages"])                                                        # 1 PACKAGES
actionToken.append(["thumbnails"])                                                      # 2 THUMBS
actionToken.append(["addons"])                                                          # 3 ADDONS
actionToken.append(["custom"])                                                          # 4 CUSTOM
actionToken.append(["atv"])                                                             # 5 ATV
actionToken.append(["cache", "packages", "thumbnails", "addons", "custom", "atv"])      # 6 ALL

actions = []

for act in actionToken:
    actionString = ""
    for a in act:
        actionString += a + ", "

    actions.append(__addon__.getLocalizedString(30020) + actionString[:-2])                 # Clean

arrMax = len(actions) + 10

actions.append(__addon__.getLocalizedString(30023))                                         # Compact all databases
actions.append(__addon__.getLocalizedString(30027))                                         # Clean All + Compact DBs
actions.append(__addon__.getLocalizedString(30003))                                         # Clean + Compact Textures DB
actions.append(__addon__.getLocalizedString(30100))                                         # Unused addon data folders
actions.append(__addon__.getLocalizedString(30024))                                         # Check unused repositories
actions.append(__addon__.getLocalizedString(30001))                                         # Check for addons without repo
actions.append(__addon__.getLocalizedString(30022))                                         # Settings

strEndMessage = ""
strMess = __addon__.getLocalizedString(30021)                                         # Choose Action:
intCancel = 0

xbmc.log('KCLEANER SERVICE >> RUNNING APP...' + str(xbmcgui.Window(xbmcgui.getCurrentWindowId()).getProperty('kcleaner')))

if __name__ == '__main__':
    if __addon__.getSetting('lock') == 'true':
        exit()

    params = get_params()
    url = None
    name = None
    mode = None

    try:
        url = urllib.unquote_plus(params["url"])
    except Exception:
        pass
    try:
        name = urllib.unquote_plus(params["name"])
    except Exception:
            pass
    try:
        mode = int(params["mode"])
    except Exception:
        pass

    if mode is None or url is None or len(url) < 1:                                                                # MAIN MENU
        totalSizes = CalcDeleted()
        fp = open(os.path.join(__addondir__, "shared.pkl"), "w")
        pickle.dump(totalSizes, fp)
        fp.close()
        mainMenu()

    elif mode == 1:                                                                                                # CLEAN MENU
        fp = open(os.path.join(__addondir__, "shared.pkl"))
        totalSizes = pickle.load(fp)
        fp.close()
        CleanMenu()

    elif mode == 2:                                                                                                # DATABASE MENU
        DatabasesMenu()

    elif mode == 3:                                                                                                # CHECKS MENU
        ChecksMenu()

    elif mode == 4:                                                                                                # CLEAN ALL + COMPACT DB
        dialog = xbmcgui.Dialog()

        if dialog.yesno(__addon__.getLocalizedString(30028), __addon__.getLocalizedString(30027)):                 # Confirm action: / # Clean All + Compact DBs
            intCancel, intMbDel = DeleteFiles(actionToken[6], 0)
        else:
            intCancel = 1

        if intCancel == 0:
            intCancel, intMbTxt = deleteAddonData(0)
        else:
            intCancel = 1

        if intCancel == 0:
            intCancel, intMbCom = CompactDatabases(0)
        else:
            intCancel = 1

        showResults()

    elif mode == 5:                                                                                                # SETTINGS
        __addon__.openSettings()
        intCancel = 2
        xbmc.executebuiltin('Container.Refresh')

    elif mode == 10:                                                                                               # 0 - CACHE
        mode -= 10
        WhatToClean = ""
        for j, entry in enumerate(arr):
            if entry[3] in actionToken[mode]:
                clear_cache_path = xbmc.translatePath(entry[1])
                if os.path.exists(clear_cache_path):
                    if entry[0][-1:] != ")":
                        WhatToClean += entry[0] + ", "

        WhatToClean = WhatToClean[:-2]

        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30010), WhatToClean):           # KCleaner - Confirm cleanup of:
            intCancel, intMbDel = DeleteFiles(actionToken[mode], 0)
        else:
            intCancel = 1

        showResults()

    elif mode == 11:                                                                                               # 1 - PACKAGES
        mode -= 10
        WhatToClean = ""
        for j, entry in enumerate(arr):
            if entry[3] in actionToken[mode]:
                clear_cache_path = xbmc.translatePath(entry[1])
                if os.path.exists(clear_cache_path):
                    if entry[0][-1:] != ")":
                        WhatToClean += entry[0] + ", "

        WhatToClean = WhatToClean[:-2]

        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30010), WhatToClean):           # KCleaner - Confirm cleanup of:
            intCancel, intMbDel = DeleteFiles(actionToken[mode], 0)
        else:
            intCancel = 1

        showResults()

    elif mode == 12:                                                                                               # 2 - THUMBS
        mode -= 10
        WhatToClean = ""
        for j, entry in enumerate(arr):
            if entry[3] in actionToken[mode]:
                clear_cache_path = xbmc.translatePath(entry[1])
                if os.path.exists(clear_cache_path):
                    if entry[0][-1:] != ")":
                        WhatToClean += entry[0] + ", "

        WhatToClean = WhatToClean[:-2]

        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30010), WhatToClean):           # KCleaner - Confirm cleanup of:
            intCancel, intMbDel = DeleteFiles(actionToken[mode], 0)
        else:
            intCancel = 1

        showResults()

    elif mode == 13:                                                                                               # 3 - ADDONS
        mode -= 10
        WhatToClean = ""
        for j, entry in enumerate(arr):
            if entry[3] in actionToken[mode]:
                clear_cache_path = xbmc.translatePath(entry[1])
                if os.path.exists(clear_cache_path):
                    if entry[0][-1:] != ")" and not entry[4]:
                        WhatToClean += entry[0] + ", "

        WhatToClean = WhatToClean[:-2]

        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30010), WhatToClean):           # KCleaner - Confirm cleanup of:
            intCancel, intMbDel = DeleteFiles(actionToken[mode], 0)
        else:
            intCancel = 1

        showResults()

    elif mode == 14:                                                                                               # X - UNUSED DATA FOLDERS
        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30010), __addon__.getLocalizedString(30100)):   # KCleaner - Confirm cleanup of: / # Unused addon data folders
            intCancel, intMbTxt = deleteAddonData(0)
        else:
            intCancel = 1

        showResults()

    elif mode == 15:                                                                                               # 4 - CUSTOM
        mode -= 11

        WhatToClean = ""
        for j, entry in enumerate(arr):
            if entry[3] in actionToken[mode]:
                clear_cache_path = xbmc.translatePath(entry[1])
                if os.path.exists(clear_cache_path):
                    if entry[0][-1:] != ")":
                        WhatToClean += entry[0] + ", "

        WhatToClean = WhatToClean[:-2]

        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30010), WhatToClean):           # KCleaner - Confirm cleanup of:
            intCancel, intMbDel = DeleteFiles(actionToken[mode], 0)
        else:
            intCancel = 1

        showResults()

    elif mode == 16:                                                                                               # 5 - ATV
        mode -= 11

        WhatToClean = ""
        for j, entry in enumerate(arr):
            if entry[3] in actionToken[mode]:
                clear_cache_path = xbmc.translatePath(entry[1])
                if os.path.exists(clear_cache_path):
                    if entry[0][-1:] != ")":
                        WhatToClean += entry[0] + ", "

        WhatToClean = WhatToClean[:-2]

        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30010), WhatToClean):           # KCleaner - Confirm cleanup of:
            intCancel, intMbDel = DeleteFiles(actionToken[mode], 0)
        else:
            intCancel = 1

        showResults()

    elif mode == 17:                                                                                               # 6 - ALL
        mode -= 11
        WhatToClean = ""
        for j, entry in enumerate(arr):
            if entry[3] in actionToken[mode]:
                clear_cache_path = xbmc.translatePath(entry[1])
                if os.path.exists(clear_cache_path):
                    if entry[0][-1:] != ")" and not entry[4]:
                        WhatToClean += entry[0] + ", "

        WhatToClean = WhatToClean + __addon__.getLocalizedString(30100)

        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30010), WhatToClean):           # KCleaner - Confirm cleanup of:
            intCancel, intMbDel = DeleteFiles(actionToken[mode], 0)
        else:
            intCancel = 1

        if intCancel == 0:
            intCancel, intMbTxt = deleteAddonData(0)
        else:
            intCancel = 1

        showResults()

    elif mode == 20:                                                                                               # 20 - TEXTURES DATABASE
        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30010), __addon__.getLocalizedString(30002)):   # KCleaner - Confirm cleanup of: / # Textures database
            intCancel, intMbTxt = CleanTextures(0)
        else:
            intCancel = 1

        showResults()

    elif mode == 21:                                                                                               # 21 - COMPACT DATABASES
        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30010), __addon__.getLocalizedString(30023)):   # KCleaner - Confirm cleanup of: / # Compact all databases
            intCancel, intMbCom = CompactDatabases(0)
        else:
            intCancel = 1

        showResults()

    elif mode == 30:                                                                                               # 30 - CHECK UNUSED REPO
        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30010), __addon__.getLocalizedString(30024)):   # KCleaner - Confirm cleanup of: / # Check for unused repositories
            intCancel = ProcessRepos(0)
        else:
            intCancel = 1

        showResults()

    elif mode == 31:                                                                                               # 31 - CHECK ADDONS
        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30010), __addon__.getLocalizedString(30001)):   # KCleaner - Confirm cleanup of: / # Check for addons without repo
            intCancel = ProcessAddons(0)
        else:
            intCancel = 1

        showResults()

    elif mode == 40:                                                                                               # 40 - COMPACT PATHS
        dialog = xbmcgui.Dialog()
        if dialog.yesno(__addon__.getLocalizedString(30028), __addon__.getLocalizedString(30164)):   # KCleaner - Confirm action: / # Compact settings paths to special://
            intCancel, intCnt = ProcessSpecial(0)
        else:
            intCancel = 1

        showResults()

    xbmc.log("KCLEANER >> FINISHED")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

# ------------------------------------------------------------
# ------------------------------------------------------------
# ------------------------------------------------------------
# ------------------------------------------------------------
# ------------------------------------------------------------
# ------------------------------------------------------------
# ------------------------------------------------------------
# ------------------------------------------------------------
# ------------------------------------------------------------
# ------------------------------------------------------------
