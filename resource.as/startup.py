######################################################################################################################################################
##
## STARTUP SERVICE
##
######################################################################################################################################################

import xbmc, xbmcaddon, xbmcgui, xbmcplugin, os, sys, xbmcvfs, glob
import shutil
import urllib2,urllib
import re
import uservar
from datetime import date, datetime, timedelta
from resources.libs import wizard as wiz

AUTOCLEANUP    = wiz.getS('autoclean')
AUTOCACHE      = wiz.getS('clearcache')
AUTOPACKAGES   = wiz.getS('clearpackages')

if AUTOCLEANUP == 'true':
	if AUTOCACHE == 'true': wiz.log('[AUTO CLEAN UP][Cache: on]'); wiz.clearCache()
	else: wiz.log('[AUTO CLEAN UP][Cache: off]')
	if AUTOPACKAGES == 'true': wiz.log('[AUTO CLEAN UP][Packages: on]'); wiz.clearPackages('startup')
	else: wiz.log('[AUTO CLEAN UP][Packages: off]')
else: wiz.log('[AUTO CLEAN UP: off]')

