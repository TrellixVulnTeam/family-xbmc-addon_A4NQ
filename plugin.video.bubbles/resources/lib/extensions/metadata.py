# -*- coding: utf-8 -*-

'''
	Bubbles Add-on
	Copyright (C) 2016 Bubbles

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import re
import os
import sys
import json
import platform
import subprocess
import datetime
import time
import collections
import math
import threading
import signal
import uuid
import numbers

from difflib import SequenceMatcher

from resources.lib.modules import client
from resources.lib.modules import cleantitle

from resources.lib.externals.unidecode import unidecode
from resources.lib.externals.hachoir.hachoir_parser import createParser
from resources.lib.externals.hachoir.hachoir_metadata import extractMetadata

from resources.lib.extensions import network
from resources.lib.extensions import tools
from resources.lib.extensions import interface

# Python 2.6 and lower (eg: Android SPMC) do not have an OrderedDict module. Use a manual one.
try: from collections import OrderedDict
except: from resources.lib.externals.ordereddict.ordereddict import OrderedDict

# Handles the metadata of files.

class Metadata(object):

	# Information
	InformationAll = 0
	InformationEssential = 1
	InformationNonessential = 2

	IgnoreDifference = 0.4 # The minimum difference between the name and the title. If below, the file will be ignored. 0.3 is not enough (EzTV Kings of Queens S05E03)
	IgnoreContains = 0.8 # The percentage of split parts of the title that has to match the file name split.
	IgnoreSize = 20971520 # Files smaller than this will be ignored. 20 MB.

	Seasons = [
		'season%02d',
		'season %02d',
		's%02d',
		'season%d',
		'season %d',
		's%d',

		# French
		'box%02d',
		'box %02d',
		'saison%02d',
		'saison %02d',
	]
	SeasonsExclude = '(e|ep|episode)\s*[0-9]+'

	Episodes = [
		's%02de%02d',
		's%02d e%02d',
		'%02dx%02d',
		'%02d_%02d',
		'%02d-%02d',
		'%02d.%02d',
		'season%02depisode%02d',
		'season%02d episode%02d',
		'season %02d episode %02d',
		's%de%d',
		's%d e%d',
		'%dx%d',
		'%d_%d',
		'%d-%d',
		'%d.%d',
		'season%depisode%d',
		'season%d episode%d',
		'season %d episode %d',
	]

	DefaultVideoQuality = 'SD'
	VideoQualityOrder = ['CAM', 'CAM720', 'CAM1080', 'SCR', 'SCR720', 'SCR1080', 'SD', 'HD720', 'HD1080', 'HD2K', 'HD4K', 'HD6K', 'HD8K']

	# Must be ordered from best to worst. Especially if HD is in the title, it should default to 720, but the true HD quality might be somewhere else in the title.
	# Always check for SCR and CAM first, because later CAM versions are often 720p or 1080p, but should not be detected as HD quality. Eg: The.Great.Wall.2016.1080p.HC.HDRip.X264.AC3-EVO[EtHD]
	DictionaryVideoQuality = OrderedDict([
		('CAM1080' , [['camrip', 'cam rip', 'tsrip', 'ts rip', 'hdcam', 'hd cam', 'hdts', 'hd ts', 'dvdcam', 'dvd cam', 'dvdts', 'dvd ts', 'cam', 'telesync', 'tele sync', 'ts', 'pdvd', 'camrip ', 'tsrip ', 'hdcam ', 'hdts ', 'dvdcam ', 'dvdts ', 'telesync ', 'hdtc', 'hd tc', 'telecine', 'hdrip', 'hd rip'], ['1080', '1080p', '1080i', 'hd1080', '1080hd', '1080 ', '1080p ', '1080i ', 'hd1080 ', '1080hd ', '1200p', '1200i', 'hd1200', '1200hd', '1200p ', '1200i ', 'hd1200 ', '1200hd ']]),
		('CAM720' , [['camrip', 'cam rip', 'tsrip', 'ts rip', 'hdcam', 'hd cam', 'hdts', 'hd ts', 'dvdcam', 'dvd cam', 'dvdts', 'dvd ts', 'cam', 'telesync', 'tele sync', 'ts', 'pdvd', 'camrip ', 'tsrip ', 'hdcam ', 'hdts ', 'dvdcam ', 'dvdts ', 'telesync ', 'hdtc', 'hd tc', 'telecine', 'hdrip', 'hd rip'], ['720', '720p', '720i', 'hd720', '720hd', 'hd', '720 ', '720p ', '720i ', 'hd720 ', '720hd ']]),
		('CAM' , ['camrip', 'cam rip', 'tsrip', 'ts rip', 'hdcam', 'hd cam', 'hdts', 'hd ts', 'dvdcam', 'dvd cam', 'dvdts', 'dvd ts', 'cam', 'telesync', 'tele sync', 'ts', 'pdvd', 'camrip ', 'tsrip ', 'hdcam ', 'hdts ', 'dvdcam ', 'dvdts ', 'telesync ', 'hdtc', 'hd tc', 'telecine', 'hdrip', 'hd rip']),
		('SCR1080' , [['dvdscr', 'dvdscreener', 'screener', 'scr', 'bdscr', 'r5', 'r6', 'dvdscr ', 'r5 ', 'r6 ', 'ddc'], ['1080', '1080p', '1080i', 'hd1080', '1080hd', '1080 ', '1080p ', '1080i ', 'hd1080 ', '1080hd ', '1200p', '1200i', 'hd1200', '1200hd', '1200p ', '1200i ', 'hd1200 ', '1200hd ']]),
		('SCR720' , [['dvdscr', 'dvdscreener', 'screener', 'scr', 'bdscr', 'r5', 'r6', 'dvdscr ', 'r5 ', 'r6 ', 'ddc'], ['720', '720p', '720i', 'hd720', '720hd', 'hd', '720 ', '720p ', '720i ', 'hd720 ', '720hd ']]),
		('SCR' , ['dvdscr', 'dvdscreener', 'screener', 'scr', 'bdscr', 'r5', 'r6', 'dvdscr ', 'r5 ', 'r6 ', 'ddc']),

		('HD8K' , ['8k', 'hd8k', 'hd8k ', '8khd', '8khd ', '4320p', '4320i', 'hd4320', '4320hd', '4320p ', '4320i ', 'hd4320 ', '4320hd ', '5120p', '5120i', 'hd5120', '5120hd', '5120p ', '5120i ', 'hd5120 ', '5120hd ', '8192p', '8192i', 'hd8192', '8192hd', '8192p ', '8192i ', 'hd8192 ', '8192hd ']),
		('HD6K' , ['6k', 'hd6k', 'hd6k ', '6khd', '6khd ', '3160p', '3160i', 'hd3160', '3160hd', '3160p ', '3160i ', 'hd3160 ', '3160hd ', '4096p', '4096i', 'hd4096', '4096hd', '4096p ', '4096i ', 'hd4096 ', '4096hd ']),
		('HD4K' , ['4k', 'hd4k', 'hd4k ', '4khd', '4khd ', 'uhd', 'ultrahd', 'ultra hd', 'ultra high', '2160', '2160p', '2160i', 'hd2160', '2160hd', '2160 ', '2160p ', '2160i ', 'hd2160 ', '2160hd ', '1716p', '1716i', 'hd1716', '1716hd', '1716p ', '1716i ', 'hd1716 ', '1716hd ', '2664p', '2664i', 'hd2664', '2664hd', '2664p ', '2664i ', 'hd2664 ', '2664hd ', '3112p', '3112i', 'hd3112', '3112hd', '3112p ', '3112i ', 'hd3112 ', '3112hd ', '2880p', '2880i', 'hd2880', '2880hd', '2880p ', '2880i ', 'hd2880 ', '2880hd ']),
		('HD2K' , ['2k', 'hd2k', 'hd2k ', '2khd', '2khd ', '2048p', '2048i', 'hd2048', '2048hd', '2048p ', '2048i ', 'hd2048 ', '2048hd ', '1332p', '1332i', 'hd1332', '1332hd', '1332p ', '1332i ', 'hd1332 ', '1332hd ', '1556p', '1556i', 'hd1556', '1556hd', '1556p ', '1556i ', 'hd1556 ', '1556hd ', ]),
		('HD1080' , ['1080', '1080p', '1080i', 'hd1080', '1080hd', '1080 ', '1080p ', '1080i ', 'hd1080 ', '1080hd ', '1200p', '1200i', 'hd1200', '1200hd', '1200p ', '1200i ', 'hd1200 ', '1200hd ']),
		('HD720' , ['720', '720p', '720i', 'hd720', '720hd', 'hd', '720 ', '720p ', '720i ', 'hd720 ', '720hd ']),
		('SD' , ['sd', '576', '576p', '576i', 'sd576', '576sd', '576 ', '576p ', '576i ', 'sd576 ', '576sd ', '480', '480p', '480i', 'sd480', '480sd', '480 ', '480p ', '480i ', 'sd480 ', '480sd ', '360', '360p', '360i', 'sd360', '360sd', '360 ', '360p ', '360i ', 'sd360 ', '360sd ', '240', '240p', '240i', 'sd240', '240sd', '240 ', '240p ', '240i ', 'sd240 ', '240sd ']),
	])

	DictionaryVideoCodec = OrderedDict([
		('H265' , ['hevc', 'h265', 'x265', '265', 'hevc ', 'h265 ', 'x265 ']),
		('H264' , ['avc', 'h264', 'x264', '264', 'h264 ', 'x264 ']),
		('H262' , ['h262', 'x262', '262', 'h262 ', 'x262 ']),
		('H222' , ['h222', 'x222', '222', 'h222 ', 'x222 ']),
		('XVID' , ['xvid', 'xvid ']),
		('DIVX' , ['divx', 'divx ', 'div2', 'div2 ', 'div3', 'div3 ']),
		('MPEG' , ['mp4', 'mpeg', 'm4v', 'mpg', 'mpg1', 'mpg2', 'mpg3', 'mpg4', 'mp4 ', 'mpeg ', 'msmpeg', 'msmpeg4', 'mpegurl', 'm4v ', 'mpg ', 'mpg1 ', 'mpg2 ', 'mpg3 ', 'mpg4 ', 'msmpeg ', 'msmpeg4 ']),
		('AVI' , ['avi']),
		('FLV' , ['flv', 'f4v', 'swf', 'flv ', 'f4v ', 'swf ']),
		('WMV' , ['wmv', 'wmv ']),
		('MOV' , ['mov']),
		('3GP' , ['3gp', '3gp ']),
		('MKV' , ['mkv', 'mkv ', 'matroska', 'matroska ']),
	])

	DictionaryVideoExtra = OrderedDict([
		('3D' , ['3d', 'sbs', 'hsbs', 'sidebyside', 'side by side', 'stereoscopic', 'tab', 'htab', 'topandbottom', 'top and bottom']),
	])

	DictionaryEdition = OrderedDict([
		('Extended' , ['ee', 'see', 'ext', 'exted', 'extendededition', 'extended', 'extendedcut', 'directors', 'directorsedition', 'directorscut', 'special', 'specialedition', 'specialcut', 'collector', 'collectoredition', 'collectorcut', 'collectors', 'collectorsedition', 'collectorscut']),
	])

	DictionaryAudioChannels = OrderedDict([
		('8CH' , ['ch8', '8ch', 'ch7', '7ch', '7 1', 'ch7 1', '7 1ch', 'ch8 ', '8ch ', 'ch7 ', '7ch ']),
		('6CH' , ['ch6', '6ch', 'ch6', '6ch', '6 1', 'ch6 1', '6 1ch', '5 1', 'ch5 1', '5 1ch', 'ch6 ', '6ch ', 'ch6 ', '6ch ']),
		('2CH' , ['ch2', '2ch', 'stereo', 'dualaudio', 'dual', '2 0', 'ch2 0', '2 0ch', 'ch2 ', '2ch ', 'stereo ', 'dualaudio ', 'dual ']),
		('1CH' , ['ch1', '1ch', 'mono', 'monoaudio', 'ch1 0', '1 0ch', 'ch1 ', '1ch ', 'mono ']),
	])

	DictionaryAudioCodec = OrderedDict([
		('DD' , ['dd', 'dolbydigital', 'dobly digital', 'dolby', 'doblypro', 'dolbyhd', 'dolbyex', 'doblyatmos', 'ddhd', 'ddpro', 'ddex', 'ddatmos', 'ac3', 'ac 3', 'dd ', 'dolbydigital ', 'doblypro ', 'dolbyhd ', 'dolbyex ', 'doblyatmos ', 'ddhd ', 'ddpro ', 'ddex ', 'ddatmos ', 'ac3 ']),
		('DTS' , ['dts', 'dtshd', 'dtsx', 'dtsneo', 'dtses', 'dts ', 'dtshd ', 'dtsx ', 'dtsneo ', 'dtses ', 'dca', 'dca ']),
		('AAC' , ['aac', 'aacp', 'heaac', 'aac ', 'aacp ', 'heaac ']),
	])

	DictionaryAudioDubbed = OrderedDict([
		('Dubbed' , ['dubbed', 'dubb', 'dub']),
	])

	DictionarySubtitles = OrderedDict([
		('Hard Subs' , ['hc', 'hardsubs', 'hard subs', 'hardcoded', 'hard coded', 'hardcodedsubs', 'hard coded subs']),
		('Soft Subs' , ['sub', 'subs', 'subtitle', 'sub title', 'subtitles', 'sub titles', 'aarsub', 'abksub', 'acesub', 'achsub', 'adasub', 'adysub', 'afasub', 'afhsub', 'afrsub', 'ainsub', 'akasub', 'akksub', 'albsub', 'sqisub', 'alesub', 'algsub', 'altsub', 'amhsub', 'angsub', 'anpsub', 'apasub', 'arasub', 'arcsub', 'argsub', 'armsub', 'hyesub', 'arnsub', 'arpsub', 'artsub', 'arwsub', 'asmsub', 'astsub', 'athsub', 'aussub', 'avasub', 'avesub', 'awasub', 'aymsub', 'azesub', 'badsub', 'baisub', 'baksub', 'balsub', 'bamsub', 'bansub', 'baqsub', 'eussub', 'bassub', 'batsub', 'bejsub', 'belsub', 'bemsub', 'bensub', 'bersub', 'bhosub', 'bihsub', 'biksub', 'binsub', 'bissub', 'blasub', 'bntsub', 'tibsub', 'bodsub', 'bossub', 'brasub', 'bresub', 'btksub', 'buasub', 'bugsub', 'bulsub', 'bursub', 'myasub', 'bynsub', 'cadsub', 'caisub', 'carsub', 'catsub', 'causub', 'cebsub', 'celsub', 'czesub', 'cessub', 'chasub', 'chbsub', 'chesub', 'chgsub', 'chisub', 'zhosub', 'chksub', 'chmsub', 'chnsub', 'chosub', 'chpsub', 'chrsub', 'chusub', 'chvsub', 'chysub', 'cmcsub', 'copsub', 'corsub', 'cossub', 'cpesub', 'cpfsub', 'cppsub', 'cresub', 'crhsub', 'crpsub', 'csbsub', 'cussub', 'welsub', 'cymsub', 'daksub', 'dansub', 'darsub', 'daysub', 'delsub', 'densub', 'gersub', 'deusub', 'dgrsub', 'dinsub', 'divsub', 'doisub', 'drasub', 'dsbsub', 'duasub', 'dumsub', 'dutsub', 'nldsub', 'dyusub', 'dzosub', 'efisub', 'egysub', 'ekasub', 'gresub', 'ellsub', 'elxsub', 'engsub', 'enmsub', 'eposub', 'estsub', 'ewesub', 'ewosub', 'fansub', 'faosub', 'persub', 'fassub', 'fatsub', 'fijsub', 'filsub', 'finsub', 'fiusub', 'fonsub', 'fresub', 'frasub', 'frmsub', 'frosub', 'frrsub', 'frssub', 'frysub', 'fulsub', 'fursub', 'gaasub', 'gaysub', 'gbasub', 'gemsub', 'geosub', 'katsub', 'gezsub', 'gilsub', 'glasub', 'glesub', 'glgsub', 'glvsub', 'gmhsub', 'gohsub', 'gonsub', 'gorsub', 'gotsub', 'grbsub', 'grcsub', 'grnsub', 'gswsub', 'gujsub', 'gwisub', 'haisub', 'hatsub', 'hausub', 'hawsub', 'hebsub', 'hersub', 'hilsub', 'himsub', 'hinsub', 'hitsub', 'hmnsub', 'hmosub', 'hrvsub', 'hsbsub', 'hunsub', 'hupsub', 'ibasub', 'ibosub', 'icesub', 'islsub', 'idosub', 'iiisub', 'ijosub', 'ikusub', 'ilesub', 'ilosub', 'inasub', 'incsub', 'indsub', 'inesub', 'inhsub', 'ipksub', 'irasub', 'irosub', 'itasub', 'javsub', 'jbosub', 'jpnsub', 'jprsub', 'jrbsub', 'kaasub', 'kabsub', 'kacsub', 'kalsub', 'kamsub', 'kansub', 'karsub', 'kassub', 'kausub', 'kawsub', 'kazsub', 'kbdsub', 'khasub', 'khisub', 'khmsub', 'khosub', 'kiksub', 'kinsub', 'kirsub', 'kmbsub', 'koksub', 'komsub', 'konsub', 'korsub', 'kossub', 'kpesub', 'krcsub', 'krlsub', 'krosub', 'krusub', 'kuasub', 'kumsub', 'kursub', 'kutsub', 'ladsub', 'lahsub', 'lamsub', 'laosub', 'latsub', 'lavsub', 'lezsub', 'limsub', 'linsub', 'litsub', 'lolsub', 'lozsub', 'ltzsub', 'luasub', 'lubsub', 'lugsub', 'luisub', 'lunsub', 'luosub', 'lussub', 'macsub', 'mkdsub', 'madsub', 'magsub', 'mahsub', 'maisub', 'maksub', 'malsub', 'mansub', 'maosub', 'mrisub', 'mapsub', 'marsub', 'massub', 'maysub', 'msasub', 'mdfsub', 'mdrsub', 'mensub', 'mgasub', 'micsub', 'minsub', 'missub', 'mkhsub', 'mlgsub', 'mltsub', 'mncsub', 'mnisub', 'mnosub', 'mohsub', 'monsub', 'mossub', 'mulsub', 'munsub', 'mussub', 'mwlsub', 'mwrsub', 'mynsub', 'myvsub', 'nahsub', 'naisub', 'napsub', 'nausub', 'navsub', 'nblsub', 'ndesub', 'ndosub', 'ndssub', 'nepsub', 'newsub', 'niasub', 'nicsub', 'niusub', 'nnosub', 'nobsub', 'nogsub', 'nonsub', 'norsub', 'nqosub', 'nsosub', 'nubsub', 'nwcsub', 'nyasub', 'nymsub', 'nynsub', 'nyosub', 'nzisub', 'ocisub', 'ojisub', 'orisub', 'ormsub', 'osasub', 'osssub', 'otasub', 'otosub', 'paasub', 'pagsub', 'palsub', 'pamsub', 'pansub', 'papsub', 'pausub', 'peosub', 'phisub', 'phnsub', 'plisub', 'polsub', 'ponsub', 'porsub', 'prasub', 'prosub', 'pussub', 'quesub', 'rajsub', 'rapsub', 'rarsub', 'roasub', 'rohsub', 'romsub', 'rumsub', 'ronsub', 'runsub', 'rupsub', 'russub', 'sadsub', 'sagsub', 'sahsub', 'saisub', 'salsub', 'samsub', 'sansub', 'sassub', 'satsub', 'scnsub', 'scosub', 'selsub', 'semsub', 'sgasub', 'sgnsub', 'shnsub', 'sidsub', 'sinsub', 'siosub', 'sitsub', 'slasub', 'slosub', 'slksub', 'slvsub', 'smasub', 'smesub', 'smisub', 'smjsub', 'smnsub', 'smosub', 'smssub', 'snasub', 'sndsub', 'snksub', 'sogsub', 'somsub', 'sonsub', 'sotsub', 'spasub', 'srdsub', 'srnsub', 'srpsub', 'srrsub', 'ssasub', 'sswsub', 'suksub', 'sunsub', 'sussub', 'suxsub', 'swasub', 'swesub', 'sycsub', 'syrsub', 'tahsub', 'taisub', 'tamsub', 'tatsub', 'telsub', 'temsub', 'tersub', 'tetsub', 'tgksub', 'tglsub', 'thasub', 'tigsub', 'tirsub', 'tivsub', 'tklsub', 'tlhsub', 'tlisub', 'tmhsub', 'togsub', 'tonsub', 'tpisub', 'tsisub', 'tsnsub', 'tsosub', 'tuksub', 'tumsub', 'tupsub', 'tursub', 'tutsub', 'tvlsub', 'twisub', 'tyvsub', 'udmsub', 'ugasub', 'uigsub', 'ukrsub', 'umbsub', 'undsub', 'urdsub', 'uzbsub', 'vaisub', 'vensub', 'viesub', 'volsub', 'votsub', 'waksub', 'walsub', 'warsub', 'wassub', 'wensub', 'wlnsub', 'wolsub', 'xalsub', 'xhosub', 'yaosub', 'yapsub', 'yidsub', 'yorsub', 'ypksub', 'zapsub', 'zblsub', 'zensub', 'zghsub', 'zhasub', 'zndsub', 'zulsub', 'zunsub', 'zxxsub', 'zzasub', 'aarsubs', 'abksubs', 'acesubs', 'achsubs', 'adasubs', 'adysubs', 'afasubs', 'afhsubs', 'afrsubs', 'ainsubs', 'akasubs', 'akksubs', 'albsubs', 'sqisubs', 'alesubs', 'algsubs', 'altsubs', 'amhsubs', 'angsubs', 'anpsubs', 'apasubs', 'arasubs', 'arcsubs', 'argsubs', 'armsubs', 'hyesubs', 'arnsubs', 'arpsubs', 'artsubs', 'arwsubs', 'asmsubs', 'astsubs', 'athsubs', 'aussubs', 'avasubs', 'avesubs', 'awasubs', 'aymsubs', 'azesubs', 'badsubs', 'baisubs', 'baksubs', 'balsubs', 'bamsubs', 'bansubs', 'baqsubs', 'eussubs', 'bassubs', 'batsubs', 'bejsubs', 'belsubs', 'bemsubs', 'bensubs', 'bersubs', 'bhosubs', 'bihsubs', 'biksubs', 'binsubs', 'bissubs', 'blasubs', 'bntsubs', 'tibsubs', 'bodsubs', 'bossubs', 'brasubs', 'bresubs', 'btksubs', 'buasubs', 'bugsubs', 'bulsubs', 'bursubs', 'myasubs', 'bynsubs', 'cadsubs', 'caisubs', 'carsubs', 'catsubs', 'causubs', 'cebsubs', 'celsubs', 'czesubs', 'cessubs', 'chasubs', 'chbsubs', 'chesubs', 'chgsubs', 'chisubs', 'zhosubs', 'chksubs', 'chmsubs', 'chnsubs', 'chosubs', 'chpsubs', 'chrsubs', 'chusubs', 'chvsubs', 'chysubs', 'cmcsubs', 'copsubs', 'corsubs', 'cossubs', 'cpesubs', 'cpfsubs', 'cppsubs', 'cresubs', 'crhsubs', 'crpsubs', 'csbsubs', 'cussubs', 'welsubs', 'cymsubs', 'daksubs', 'dansubs', 'darsubs', 'daysubs', 'delsubs', 'densubs', 'gersubs', 'deusubs', 'dgrsubs', 'dinsubs', 'divsubs', 'doisubs', 'drasubs', 'dsbsubs', 'duasubs', 'dumsubs', 'dutsubs', 'nldsubs', 'dyusubs', 'dzosubs', 'efisubs', 'egysubs', 'ekasubs', 'gresubs', 'ellsubs', 'elxsubs', 'engsubs', 'enmsubs', 'eposubs', 'estsubs', 'ewesubs', 'ewosubs', 'fansubs', 'faosubs', 'persubs', 'fassubs', 'fatsubs', 'fijsubs', 'filsubs', 'finsubs', 'fiusubs', 'fonsubs', 'fresubs', 'frasubs', 'frmsubs', 'frosubs', 'frrsubs', 'frssubs', 'frysubs', 'fulsubs', 'fursubs', 'gaasubs', 'gaysubs', 'gbasubs', 'gemsubs', 'geosubs', 'katsubs', 'gezsubs', 'gilsubs', 'glasubs', 'glesubs', 'glgsubs', 'glvsubs', 'gmhsubs', 'gohsubs', 'gonsubs', 'gorsubs', 'gotsubs', 'grbsubs', 'grcsubs', 'grnsubs', 'gswsubs', 'gujsubs', 'gwisubs', 'haisubs', 'hatsubs', 'hausubs', 'hawsubs', 'hebsubs', 'hersubs', 'hilsubs', 'himsubs', 'hinsubs', 'hitsubs', 'hmnsubs', 'hmosubs', 'hrvsubs', 'hsbsubs', 'hunsubs', 'hupsubs', 'ibasubs', 'ibosubs', 'icesubs', 'islsubs', 'idosubs', 'iiisubs', 'ijosubs', 'ikusubs', 'ilesubs', 'ilosubs', 'inasubs', 'incsubs', 'indsubs', 'inesubs', 'inhsubs', 'ipksubs', 'irasubs', 'irosubs', 'itasubs', 'javsubs', 'jbosubs', 'jpnsubs', 'jprsubs', 'jrbsubs', 'kaasubs', 'kabsubs', 'kacsubs', 'kalsubs', 'kamsubs', 'kansubs', 'karsubs', 'kassubs', 'kausubs', 'kawsubs', 'kazsubs', 'kbdsubs', 'khasubs', 'khisubs', 'khmsubs', 'khosubs', 'kiksubs', 'kinsubs', 'kirsubs', 'kmbsubs', 'koksubs', 'komsubs', 'konsubs', 'korsubs', 'kossubs', 'kpesubs', 'krcsubs', 'krlsubs', 'krosubs', 'krusubs', 'kuasubs', 'kumsubs', 'kursubs', 'kutsubs', 'ladsubs', 'lahsubs', 'lamsubs', 'laosubs', 'latsubs', 'lavsubs', 'lezsubs', 'limsubs', 'linsubs', 'litsubs', 'lolsubs', 'lozsubs', 'ltzsubs', 'luasubs', 'lubsubs', 'lugsubs', 'luisubs', 'lunsubs', 'luosubs', 'lussubs', 'macsubs', 'mkdsubs', 'madsubs', 'magsubs', 'mahsubs', 'maisubs', 'maksubs', 'malsubs', 'mansubs', 'maosubs', 'mrisubs', 'mapsubs', 'marsubs', 'massubs', 'maysubs', 'msasubs', 'mdfsubs', 'mdrsubs', 'mensubs', 'mgasubs', 'micsubs', 'minsubs', 'missubs', 'mkhsubs', 'mlgsubs', 'mltsubs', 'mncsubs', 'mnisubs', 'mnosubs', 'mohsubs', 'monsubs', 'mossubs', 'mulsubs', 'munsubs', 'mussubs', 'mwlsubs', 'mwrsubs', 'mynsubs', 'myvsubs', 'nahsubs', 'naisubs', 'napsubs', 'nausubs', 'navsubs', 'nblsubs', 'ndesubs', 'ndosubs', 'ndssubs', 'nepsubs', 'newsubs', 'niasubs', 'nicsubs', 'niusubs', 'nnosubs', 'nobsubs', 'nogsubs', 'nonsubs', 'norsubs', 'nqosubs', 'nsosubs', 'nubsubs', 'nwcsubs', 'nyasubs', 'nymsubs', 'nynsubs', 'nyosubs', 'nzisubs', 'ocisubs', 'ojisubs', 'orisubs', 'ormsubs', 'osasubs', 'osssubs', 'otasubs', 'otosubs', 'paasubs', 'pagsubs', 'palsubs', 'pamsubs', 'pansubs', 'papsubs', 'pausubs', 'peosubs', 'phisubs', 'phnsubs', 'plisubs', 'polsubs', 'ponsubs', 'porsubs', 'prasubs', 'prosubs', 'pussubs', 'quesubs', 'rajsubs', 'rapsubs', 'rarsubs', 'roasubs', 'rohsubs', 'romsubs', 'rumsubs', 'ronsubs', 'runsubs', 'rupsubs', 'russubs', 'sadsubs', 'sagsubs', 'sahsubs', 'saisubs', 'salsubs', 'samsubs', 'sansubs', 'sassubs', 'satsubs', 'scnsubs', 'scosubs', 'selsubs', 'semsubs', 'sgasubs', 'sgnsubs', 'shnsubs', 'sidsubs', 'sinsubs', 'siosubs', 'sitsubs', 'slasubs', 'slosubs', 'slksubs', 'slvsubs', 'smasubs', 'smesubs', 'smisubs', 'smjsubs', 'smnsubs', 'smosubs', 'smssubs', 'snasubs', 'sndsubs', 'snksubs', 'sogsubs', 'somsubs', 'sonsubs', 'sotsubs', 'spasubs', 'srdsubs', 'srnsubs', 'srpsubs', 'srrsubs', 'ssasubs', 'sswsubs', 'suksubs', 'sunsubs', 'sussubs', 'suxsubs', 'swasubs', 'swesubs', 'sycsubs', 'syrsubs', 'tahsubs', 'taisubs', 'tamsubs', 'tatsubs', 'telsubs', 'temsubs', 'tersubs', 'tetsubs', 'tgksubs', 'tglsubs', 'thasubs', 'tigsubs', 'tirsubs', 'tivsubs', 'tklsubs', 'tlhsubs', 'tlisubs', 'tmhsubs', 'togsubs', 'tonsubs', 'tpisubs', 'tsisubs', 'tsnsubs', 'tsosubs', 'tuksubs', 'tumsubs', 'tupsubs', 'tursubs', 'tutsubs', 'tvlsubs', 'twisubs', 'tyvsubs', 'udmsubs', 'ugasubs', 'uigsubs', 'ukrsubs', 'umbsubs', 'undsubs', 'urdsubs', 'uzbsubs', 'vaisubs', 'vensubs', 'viesubs', 'volsubs', 'votsubs', 'waksubs', 'walsubs', 'warsubs', 'wassubs', 'wensubs', 'wlnsubs', 'wolsubs', 'xalsubs', 'xhosubs', 'yaosubs', 'yapsubs', 'yidsubs', 'yorsubs', 'ypksubs', 'zapsubs', 'zblsubs', 'zensubs', 'zghsubs', 'zhasubs', 'zndsubs', 'zulsubs', 'zunsubs', 'zxxsubs', 'zzasubs']),
	])

	DictionarySeeds = OrderedDict([
		('Seed' , ['seed']),
	])

	DictionaryAge = OrderedDict([
		('Day' , ['day']),
	])

	DictionarySize = OrderedDict([
		('B' , ['b']),
		('KB' , ['kb', 'kib']),
		('MB' , ['mb', 'mib']),
		('GB' , ['gb', 'gib']),
		('TB' , ['tb', 'tib']),
	])

	DictionaryIgnore = OrderedDict([
		('Extras' , ['extra', 'extras']),
		('Soundtrack' , ['ost', 'soundtrack', 'soundtracks', 'thememusic', 'theme music', 'themesong', 'themesongs', 'theme song', 'theme songs', 'album', 'albums', 'mp3', 'flac']),
		('Trailer' , ['trailer', 'trailers', 'preview', 'previews']),
	])

	def __init__(self, name = None, title = None, year = None, season = None, episode = None, pack = None, link = None, quality = None, size = None, languageAudio = None, seeds = None, age = None, source = None):
		self.mInfo = None

		self.mName = None
		self.mNameProcessed = None
		self.mNameSplit = None
		self.mNameReduced = None

		self.mTitle = None
		self.mTitleProcessed = None
		self.mTitleSplit = None

		self.mYear = None
		self.mSeason = None
		self.mEpisode = None
		self.mPack = None

		self.mLocal = None
		self.mDirect = None
		self.mPremium = None
		self.mCached = None
		self.mLink = None
		self.mSize = None
		self.mEdition = None
		self.mDuration = None

		self.mVideoQuality = None
		self.mVideoCodec = None
		self.mVideoExtra = None

		self.mSubtitles = None

		self.mAudioLanguages = None
		self.mAudioDubbed = None
		self.mAudioChannels = None
		self.mAudioCodec = None

		self.mPrecheck = None
		self.mSeeds = None
		self.mAge = None

		self.load(name = name, title = title, year = year, season = season, episode = episode, pack = pack, link = link, quality = quality, size = size, languageAudio = languageAudio, seeds = seeds, age = age, source = source)

	@classmethod
	def showDialog(self, source, metadata):
		try:
			items = []
			unknown = 'Unknown'
			standard = 'Standard'
			local = 'Local'
			yes = 'Yes'
			no = 'No'

			stream = None
			if 'urlresolved' in source:
				stream = source['urlresolved']

			file = None
			if 'file' in source:
				# Remove non-ASCII characters, since Kodi can't display them and will not show the dialog.
				file = source['file'].encode('ascii', errors = 'ignore').strip()
			hash = None
			if 'hash' in source:
				try: hash = source['hash'].upper()
				except: hash = source['hash']

			title = tools.Media.titleUniversal(metadata = metadata, encode = True)
			meta = Metadata(name = file, title = title, source = source)

			pack = None
			if not meta.mPack == None:
				pack = yes if meta.mPack else no

			audioLanguages = meta.audioLanguages()
			if not audioLanguages or audioLanguages[0] == tools.Language.UniversalCode:
				audioLanguages = unknown
			else:
				audioLanguages = ', '.join([i[1] for i in meta.audioLanguages()])

			link = meta.link()
			link = network.Networker(link).link() # Clean link.
			if not link or link == '':
				link = stream

			theSource = ''
			if 'local' in source and source['local']:
				theSource = local
			elif not source['source'] == None and not source['source'] == '0':
				theSource = source['source']
			index = theSource.find('.')
			if index >= 0: theSource = theSource[:index]

			def splitLine(text, characters = 45):
				if text:
					return re.sub("(.{" + str(characters) + "})", "\\1\n", text, 0, re.DOTALL)
				else:
					return None

			# Item Details
			items.append(interface.Format.font('Item Details', bold = True, uppercase = True))
			items.append(interface.Format.font('Title: ', bold = True) + interface.Format.font(title))
			items.append(interface.Format.font('Edition: ', bold = True) + interface.Format.font(meta.edition() if meta.edition() else standard))
			if pack: items.append(interface.Format.font('Pack: ', bold = True) + interface.Format.font(pack))
			items.append(interface.Format.font('Size: ', bold = True) + interface.Format.font(meta.size(True) if meta.size() else unknown))
			items.append(interface.Format.font('File: ', bold = True) + interface.Format.font(file if file else unknown))
			items.append(interface.Format.font('Hash: ', bold = True) + interface.Format.font(hash if hash else unknown))

			# Video Details
			items.append('')
			items.append(interface.Format.font('Video Details', bold = True, uppercase = True))
			items.append(interface.Format.font('Quality: ', bold = True) + interface.Format.font(meta.videoQuality() if meta.videoQuality() else unknown))
			items.append(interface.Format.font('Codec: ', bold = True) + interface.Format.font(meta.videoCodec() if meta.videoCodec() else unknown))
			items.append(interface.Format.font('3D: ', bold = True) + interface.Format.font(yes if meta.videoExtra() == '3D' else no))

			# Audio Details
			items.append('')
			items.append(interface.Format.font('Audio Details', bold = True, uppercase = True))
			items.append(interface.Format.font('Language: ', bold = True) + interface.Format.font(audioLanguages))
			items.append(interface.Format.font('Dubbed: ', bold = True) + interface.Format.font(yes if meta.audioDubbed() else no))
			items.append(interface.Format.font('Codec: ', bold = True) + interface.Format.font(meta.audioCodec() if meta.audioCodec() else unknown))
			items.append(interface.Format.font('Channels: ', bold = True) + interface.Format.font(str(meta.audioChannels()) if meta.audioChannels() else unknown))

			# Subtitles
			items.append('')
			items.append(interface.Format.font('Subtitle Details', bold = True, uppercase = True))
			items.append(interface.Format.font('Subtitles: ', bold = True) + interface.Format.font(yes if meta.subtitles() else no))
			if meta.subtitles():
				items.append(interface.Format.font('Soft Coded: ', bold = True) + interface.Format.font(yes if 'soft' in meta.subtitles().lower() else no))
				items.append(interface.Format.font('Hard Coded: ', bold = True) + interface.Format.font(yes if 'hard' in meta.subtitles().lower() else no))

			# Hoster
			items.append('')
			items.append(interface.Format.font('Hoster Details', bold = True, uppercase = True))
			items.append(interface.Format.font('Provider: ', bold = True) + interface.Format.font(source['provider']))
			items.append(interface.Format.font('Source: ', bold = True) + interface.Format.font(theSource, capitalcase = True))
			items.append(interface.Format.font('Local: ', bold = True) + interface.Format.font(yes if meta.local() else no))
			items.append(interface.Format.font('Debrid: ', bold = True) + interface.Format.font(yes if 'debrid' in source and source['debrid'] else no))
			items.append(interface.Format.font('Direct: ', bold = True) + interface.Format.font(yes if meta.direct() else no))
			items.append(interface.Format.font('Cached: ', bold = True) + interface.Format.font(yes if meta.cached() else no))
			if meta.seeds(): items.append(interface.Format.font('Seeds: ', bold = True) + interface.Format.font(str(meta.seeds())))
			if meta.age(): items.append(interface.Format.font('Age: ', bold = True) + interface.Format.font(meta.age(True)))
			items.append(interface.Format.font('Link: ', bold = True) + interface.Format.font(link, italic = True))
			if stream: items.append(interface.Format.font('Stream: ', bold = True) + interface.Format.font(stream, italic = True))

			# Dialog
			interface.Dialog.select(items, title = 'Stream Details')
		except:
			tools.Logger.error()

	@classmethod
	def foreign(self, title, umlaut = False):
		return tools.Converter.unicode(string = title, umlaut = umlaut)

	@classmethod
	def videoResolutionQuality(self, width = 0, height = 0):
		threshold = 20 # Some videos are a bit smaller.
		if width:
			if width >= 7680 - threshold: return 'HD8K'
			elif width >= 6144 - threshold: return 'HD6K'
			elif width >= 3840 - threshold: return 'HD4K'
			elif width >= 2048 - threshold: return 'HD2K'
			elif width >= 1920 - threshold: return 'HD1080'
			elif width >= 1280 - threshold: return 'HD720'
			elif width >= 1: return 'SD'
		if height:
			if height >= 4320 - threshold: return 'HD8K'
			elif height >= 3160 - threshold: return 'HD6K'
			elif height >= 2160 - threshold: return 'HD4K'
			elif height >= 1200 - threshold: return 'HD2K' # Increase, because the same as HD1080.
			elif height >= 1080 - threshold: return 'HD1080'
			elif height >= 720 - threshold: return 'HD720'
			elif height >= 1: return 'SD'
		return None

	@classmethod
	def videoQualityResolution(self, quality):
		if quality == 'HD720': return 1280, 720
		elif quality == 'HD1080': return 1920, 1080
		elif quality == 'HD2K': return 2048, 1080
		elif quality == 'HD4K': return 3840, 2160
		elif quality == 'HD6K': return 6144, 3160
		elif quality == 'HD8K': return 7680, 4320
		else: return 720, 480

	@classmethod
	def videoQualityConvert(self, quality):
		quality = quality.lower()
		for key, value in self.DictionaryVideoQuality.iteritems():
			if quality == key.lower():
				return key
			else:
				if len(value) > 1 and isinstance(value[0], list) and not isinstance(value[0], basestring):
					 pass # Ignore SCR1080, SCR720, CAM1080, CAM720
				elif quality in value:
					return key
		return self.DefaultVideoQuality

	def videoQualityRange(self, quality, qualityFrom = None, qualityTo = None):
		if quality == None:
			return False

		quality = self.VideoQualityOrder.index(quality)
		qualityFrom = self.videoQualityIndex(qualityFrom)
		qualityTo = self.videoQualityIndex(qualityTo)

		# In case the qualities were passed in the wrong order.
		if qualityFrom > qualityTo:
			temporary = qualityFrom
			qualityFrom = qualityTo
			qualityTo = temporary

		if not qualityFrom == None and quality < qualityFrom:
			return False
		if not qualityTo == None and quality > qualityTo:
			return False
		return True

	def videoQualityIndex(self, quality):
		if quality == None or isinstance(quality, (int, long)):
			return quality
		else:
			return self.VideoQualityOrder.index(quality)

	def setVideoQuality(self, quality):
		self.mVideoQuality = self.__searchFind(quality, self.DictionaryVideoQuality)

	def setVideoCodec(self, codec):
		self.mVideoCodec = self.__searchFind(codec, self.DictionaryVideoCodec)

	def setVideo3D(self, video3d):
		if video3d == True:
			self.mVideoExtra = list(self.DictionaryVideoExtra)[0]
		else:
			self.mVideoExtra = self.__searchFind(video3d, self.DictionaryVideoExtra)

	def setAudioLanguages(self, languages):
		if isinstance(languages, list):
			self.mAudioLanguages = [tools.Language.language(i) for i in languages]
		else:
			self.mAudioLanguages = [tools.Language.language(languages)]

	def setAudioChannels(self, channels):
		if isinstance(channels, numbers.Number):
			channels = str(channels) + 'CH'
		self.mAudioChannels = self.__searchFind(channels, self.DictionaryAudioChannels)

	def setAudioCodec(self, codec):
		self.mAudioCodec = self.__searchFind(codec, self.DictionaryAudioCodec)

	def setSubtitles(self, subtitles):
		self.mSubtitles = self.__searchFind(subtitles, self.DictionarySubtitles)

	def setSubtitlesSoft(self, enable = True):
		if enable:
			self.mSubtitles = list(self.DictionarySubtitles)[1]

	def setSubtitlesHard(self, enable = True):
		if enable:
			self.mSubtitles = list(self.DictionarySubtitles)[0]

	def setLink(self, link):
		# Some scrapers like FilmPalast return a ID array (which is resolved later) instead of a link. In such a case, do not use it.
		if isinstance(link, basestring):
			self.mLink = link
		else:
			self.mLink = ''

	def setSize(self, size):
		# Size can be bytes or string.
		self.mSize = self.__loadSize(size)

	def setDuration(self, duration):
		if duration:
			if not isinstance(duration, basestring) or duration.isdigit():
				duration = int(duration)
				if duration > 0:
					self.mDuration = duration

	def setSeeds(self, seeds):
		self.mSeeds = seeds

	def setAge(self, age):
		self.mAge = age

	def videoQuality(self, kodi = False):
		if kodi:
			if self.mVideoQuality:
				return self.videoQualityResolution(self.mVideoQuality)
			return self.videoQualityResolution('SD')
		else:
			return self.mVideoQuality

	def videoCodec(self, kodi = False):
		if kodi and self.mVideoCodec:
			return self.mVideoCodec.lower()
		else:
			return self.mVideoCodec

	def videoExtra(self):
		return self.mVideoExtra

	def audioLanguages(self):
		return self.mAudioLanguages

	def audioDubbed(self):
		return not (self.mAudioDubbed == False or self.mAudioDubbed == None or self.mAudioDubbed == '')

	def audioChannels(self, kodi = False):
		if kodi and self.mAudioChannels:
			return int(self.mAudioChannels.replace('CH', ''))
		else:
			return self.mAudioChannels

	def audioCodec(self, kodi = False):
		if kodi and self.mAudioCodec:
			return self.mAudioCodec.replace('DD', 'AC3').lower()
		else:
			return self.mAudioCodec

	def subtitles(self):
		return self.mSubtitles

	def subtitlesIsSoft(self):
		if self.mSubtitles:
			return 'soft' in self.mSubtitles.lower()
		else:
			return False

	def subtitlesIsHard(self):
		if self.mSubtitles:
			return 'hard' in self.mSubtitles.lower()
		else:
			return False

	def local(self):
		return self.mLocal == True

	def direct(self):
		return self.mDirect == True

	def premium(self):
		return self.mPremium == True

	def cached(self):
		return self.mCached == True

	def link(self):
		return self.mLink

	def edition(self):
		return self.mEdition

	def size(self, format = False):
		if format:
			return self.__formatSize()
		else:
			return self.mSize

	def seeds(self, format = False):
		if format:
			return self.__formatSeeds()
		else:
			return self.mSeeds

	def age(self, format = False):
		if format:
			return self.__formatAge()
		else:
			return self.mAge

	def cached(self):
		return self.mCached

	def precheck(self):
		if self.mPrecheck == network.Networker.StatusOnline or self.mCached == True or self.mSeeds >= 10:
			return network.Networker.StatusOnline
		else:
			return self.mPrecheck

	def isEpisode(self):
		return (not self.mSeason == None and not self.mEpisode == None) or re.match('s\d{2,}e\d{2,}', self.mTitleProcessed) or re.match('s\d{2,}e\d{2,}', self.mNameProcessed)

	def isPack(self):
		return self.mPack == True

	def isHoster(self):
		return not self.isTorrent() and not self.isUsenet()

	def isTorrent(self):
		return not self.mSeeds == None

	def isUsenet(self):
		return not self.mAge == None

	# extended: adds metadata to title
	# prefix: adds Bubbles name to the front
	def title(self, extended = False, prefix = False):
		title = self.mTitle

		if prefix:
			title = '[' + tools.System.name().upper() + '] ' + title

		if extended:
			metadata = []

			if self.mVideoQuality: metadata.append(self.mVideoQuality)
			if self.mVideoExtra: metadata.append(self.mVideoExtra)
			if self.mEdition: metadata.append(self.mEdition)
			if self.mVideoCodec: metadata.append(self.mVideoCodec)
			audio = self.__formatAudio(format = False)
			if audio: metadata.append(audio)
			if self.mSubtitles: metadata.append(self.mSubtitles)

			if len(metadata) > 0:
				title += ' [' + ', '.join(metadata) + ']'

		return title

	# If sizeLimit == True, will use the default size limit.
	def information(self, format = False, sizeLimit = 0, precheck = False, information = InformationAll):
		values = []

		if information == self.InformationAll or information == self.InformationEssential:
			if precheck:
				check = self.precheck()
				if check == network.Networker.StatusOnline:
					values.append(interface.Format.font(' + ', bold = True, color = interface.Format.ColorExcellent))
				elif check == network.Networker.StatusOffline:
					values.append(interface.Format.font(' - ', bold = True, color = interface.Format.ColorBad))
				else:
					values.append(interface.Format.font(' = ', bold = True, color = interface.Format.ColorMedium))

			if self.mVideoQuality:
				if format: values.append(interface.Format.font(self.mVideoQuality, color = self.__colorVideoQuality(), bold = True, uppercase = True))
				else: values.append(self.mVideoQuality)

			special = None
			if self.mLocal == True: special = 'LOCAL'
			elif self.mPremium == True: special = 'PREMIUM'
			elif self.mCached == True: special = 'CACHED'
			elif self.mDirect == True: special = 'DIRECT'
			if not special == None:
				if format: values.append(interface.Format.font(special, color = interface.Format.ColorSpecial, bold = True, uppercase = True))
				else: values.append(special)

			if self.mPack:
				pack = 'PACK'
				if format: values.append(interface.Format.font(pack, color = interface.Format.ColorAlternative, bold = True, uppercase = True))
				else: values.append(pack)

		if information == self.InformationAll or information == self.InformationNonessential:
			if self.mVideoExtra:
				if format: values.append(interface.Format.font(self.mVideoExtra, bold = True, uppercase = True))
				else: values.append(self.mVideoExtra)

			if self.mEdition and not self.isEpisode():
				if format: values.append(interface.Format.font(self.mEdition, bold = True, capitalcase = True))
				else: values.append(self.mEdition)

			if self.mVideoCodec:
				if format: values.append(interface.Format.font(self.mVideoCodec, uppercase = True))
				else: values.append(self.mVideoCodec)

			audio = self.__formatAudio(format = format)
			if audio:
				if format: values.append(interface.Format.font(audio, uppercase = True))
				else: values.append(audio)

			if self.mSubtitles:
				if format: values.append(interface.Format.font(self.mSubtitles, color = self.__colorSubtitles()))
				else: values.append(self.mSubtitles)

			if sizeLimit == True: sizeLimit = self.IgnoreSize
			if self.mSize and self.mSize > sizeLimit:
				size = self.__formatSize()
				if size:
					if format: values.append(interface.Format.font(size, uppercase = True))
					else: values.append(size)

			seeds = self.__formatSeeds()
			if seeds:
				if format: values.append(interface.Format.font(seeds, color = self.__colorSeeds()))
				else: values.append(seeds)

			age = self.__formatAge()
			if age:
				if format: values.append(interface.Format.font(age, color = self.__colorAge()))
				else: values.append(age)

		values = interface.Format.fontSeparator().join(filter(None, values))
		return values

	def __matchClean(self, value):
		value = re.sub('(\.|\(|\[|\s)(\d{4}|S\d*E\d*|S\d*|3D)(\.|\)|\]|\s|)', '', value.upper())
		value = re.sub(r'[^\w]', '', value)
		return cleantitle.get(value).lower()

	def __match(self):
		# Match the parts of the title with the name, since self.__match() is not enough. Eg Detective Conan (anime) S19E01 gets True Detective episodes.
		if not self.__containsEpisode():
			return False
		if not self.__containsTitle():
			return False

		# Ignore this for now, since it filters out too much, like Taboo S01E01.
		#if not self.__matchTitle():
		#	return False

		return True

	def __matchTitle(self):
		value1 = self.__matchClean(self.mNameProcessed)
		value2 = self.__matchClean(self.mTitleProcessed)
		if SequenceMatcher(None, value1, value2).ratio() >= self.IgnoreDifference:
			return True
		elif len(value1) > len(value2) * 2:
			# Sometimes there are very long strings before or after the actual name, causing a non-match. Divide the string into 2 and check each part.
			# Only do this for long strings, becasue short string almost always give a good match if just a few characters match.
			split = -((-len(value1))//2)
			difference = self.IgnoreDifference
			if len(value2) < 30: # Increase the requirnments for short titles, because the typically have a high match rate.
				difference = min(0.8, difference * 2)
			return SequenceMatcher(None, value1[:split], value2).ratio() >= difference or SequenceMatcher(None, value1[split:], value2).ratio() >= difference
		return False

	def seasonNames(self, season = None):
		if season == None:
			return self.Seasons
		else:
			season = int(season)
			seasons = self.Seasons
			for i in range(seasons):
				seasons[i] = seasons[i] % season
		return seasons

	def seasonContains(self, title, season):
		if season == None: return True # For movies
		title = title.lower()
		processedTitle, splitTitle = self.__loadValue(title)
		splitTitle = set(splitTitle)
		season = int(season)
		for i in self.Seasons:
			processedSeason, splitSeason = self.__loadValue(i % season)
			if set(splitSeason).issubset(splitTitle) and not re.search(self.SeasonsExclude, title):
				return True
		return False

	def episodeNames(self, season = None, episode = None):
		if season == None or episode == None:
			return self.Episodes
		else:
			season = int(season)
			episode = int(episode)
			episodes = self.Episodes
			for i in range(episodes):
				episodes[i] = episodes[i] % (season, episode)
		return episodes

	def episodeContains(self, title, season, episode):
		if season == None or episode == None: return True # For movies
		processedTitle, splitTitle = self.__loadValue(title)
		splitTitle = set(splitTitle)
		season = int(season)
		episode = int(episode)
		for i in self.Episodes:
			processedEpisode, splitEpisode = self.__loadValue(i % (season, episode))
			if set(splitEpisode).issubset(splitTitle):
				return True
		return False

	def __containsEpisode(self):
		# Must always match the episode number.
		if self.mSeason == None or self.mEpisode == None: # Eg: movie, does not contain season/episode.
			return True

		splitName = set(self.mNameSplit)

		# Ignore for season packs:
		if self.mPack:
			for i in self.Seasons:
				processedSeason, splitSeason = self.__loadValue(i % self.mSeason)
				if set(splitSeason).issubset(splitName) and not re.search(self.SeasonsExclude, self.mTitleProcessed):
					return True
		else:
			for i in self.Episodes:
				processedEpisode, splitEpisode = self.__loadValue(i % (self.mSeason, self.mEpisode))
				if set(splitEpisode).issubset(splitName):
					return True

		return False

	def __containsTitle(self):
		total = len(self.mTitleSplit)
		count = 0
		for i in self.mTitleSplit:
			if i in self.mNameSplit:
				count += 1
		percentage = count / float(total)
		return percentage >= self.IgnoreContains

	def ignore(self, size = True):
		# Ignore if the title and name do not correspond.
		if not self.__match():
			return True

		for value in self.DictionaryIgnore.itervalues():
			if self.__searchContains(value):
				return True

		# Ignore small files.
		if size and self.mSize < self.IgnoreSize:
			return True

		# Ignore torrents with no seeds.
		if self.mSeeds == 0:
			return True

		return False

	def load(self, name = None, title = None, year = None, season = None, episode = None, pack = None, link = None, quality = None, size = None, languageAudio = None, seeds = None, age = None, source = None):
		try:
			if source:
				if name and not name == '':
					self.mName = name
				if isinstance(source, dict) and 'url' in source:
					self.setLink(source['url'])
					if name == None or name == '':
						self.mName = self.mLink.rsplit('/', 1)[-1]
				if not self.mName:
					self.mName = ''

				self.mTitle = title
				if not self.mTitle:
					self.mTitle = ''

				if 'year' in source:
					self.mYear = int(source['year'])

				if 'season' in source:
					self.mSeason = int(source['season'])

				if 'episode' in source:
					self.mEpisode = int(source['episode'])

				if 'pack' in source:
					self.mPack = bool(source['pack'])

				if 'local' in source:
					self.mLocal = source['local']
				else:
					self.mLocal = False

				if 'direct' in source:
					self.mDirect = source['direct']
				else:
					self.mDirect = False

				if 'premium' in source:
					self.mPremium = source['premium']
				else:
					self.mPremium = False

				if 'debridcache' in source:
					self.mCached = source['debridcache']
				else:
					self.mCached = False

				if not languageAudio == None:
					self.setAudioLanguages(languageAudio)
				elif 'language' in source:
					self.setAudioLanguages(source['language'])

				if isinstance(source, basestring):
					self.mInfo = source
				elif isinstance(source, dict) and 'info' in source:
					self.mInfo = source['info']

				if not self.mInfo or self.mInfo == '':
					self.mInfo = None
				else:
					self.mInfo = [i.lower() for i in self.mInfo.split(interface.Format.fontSeparator())]

				if 'precheck' in source:
					self.mPrecheck = source['precheck']

				if quality and not quality == '':
					self.mVideoQuality = self.videoQualityConvert(quality.replace(' ', '').lower())
				elif isinstance(source, dict) and 'quality' in source:
					self.mVideoQuality = self.videoQualityConvert(source['quality'].replace(' ', '').lower())

				self.__loadValues()
				self.__interpret(self.__match()) # Only extract the values from the name if it matches the title. Otherwise the link contains random characters which might actidentally match search keywords (eg: dts, or dd).
			else:
				self.mName = name
				if not self.mName:
					self.mName = ''
				self.mTitle = title
				if not self.mTitle:
					self.mTitle = ''

				self.mYear = None if year == None else int(year)
				self.mSeason = None if season == None else int(season)
				self.mEpisode = None if episode == None else int(episode)
				self.mPack = None if pack == None else bool(pack)

				self.setLink(link)
				self.setSize(size)
				self.setAudioLanguages(languageAudio)
				self.setSeeds(seeds)
				self.setAge(age)

				self.__loadValues()
				self.__extract()
		except:
			tools.Logger.error()

	# Loads from the HTTP and file headers.
	def loadHeaders(self, linkOrNetworker, timeout = 30):
		try:
			if isinstance(linkOrNetworker, basestring):
				linkOrNetworker = network.Networker(linkOrNetworker)
			self.loadHeadersHttp(linkOrNetworker, timeout = int(timeout / 3))
			if linkOrNetworker.check(content = True, retrieveHeaders = False) == network.Networker.StatusOnline: # Do not check metadata that is HTML or cannot be retrieved.
				self.loadHeadersFile(linkOrNetworker, timeout = timeout)
		except:
			pass

	# Loads from the HTTP headers.
	def loadHeadersHttp(self, linkOrNetworker, timeout = 30):
		try:
			if isinstance(linkOrNetworker, basestring):
				linkOrNetworker = network.Networker(linkOrNetworker)

			size = linkOrNetworker.headerSize()
			if size:
				if size > self.IgnoreSize:
					self.setSize(size)

			type = linkOrNetworker.headerType(timeout = timeout)
			name = linkOrNetworker.headerName(timeout = timeout)
			if not type and not name:
				name = None
			elif type and name:
				name += ' ' + type
			elif type:
				name = type
			else:
				name = ''

			self.mName = name
			self.__loadValues()
			self.__extract()
		except:
			pass

	# Loads from the file headers.
	def loadHeadersFile(self, linkOrNetworker, timeout = 30):
		try:
			if not isinstance(linkOrNetworker, basestring):
				linkOrNetworker = linkOrNetworker.link()

			meta = Extractor().extract(linkOrNetworker, timeout = timeout)

			if isinstance(linkOrNetworker, basestring):
				if tools.File.exists(linkOrNetworker):
					self.mSize = tools.File.size(linkOrNetworker)

			if meta:
				# File
				# Do this first, because value like video quality will be overwritten later.
				if not self.mName or self.mName == '':
					self.mName = ''
					if 'name' in meta:
						self.mName += meta['name']
					if 'mime' in meta:
						self.mName += ' ' + meta['mime']
					if not self.mName == '':
						self.__loadValues()
						self.__extract()
				if not self.mSize or self.mSize == 0:
					if 'size' in meta:
						self.mSize = meta['size']

				# Video
				if 'video' in meta:
					# Video Quality
					if 'width' in meta['video']: width = meta['video']['width']
					else: width = 0
					if 'height' in meta['video']: height = meta['video']['height']
					else: height = 0
					if width > 0 or height > 0:
						self.setVideoQuality(self.videoResolutionQuality(width, height))
					# Video Codec
					if 'codec' in meta['video']:
						self.setVideoCodec(meta['video']['codec'])

				# Audio
				if 'audio' in meta:
					# Audio Codec
					if 'codec' in meta['audio']:
						self.setAudioCodec(meta['audio']['codec'])
					# Audio Channels
					if 'channels' in meta['audio']:
						self.setAudioChannels(meta['audio']['channels'])

				# Subtitle
				if 'subtitle' in meta and meta['subtitle']:
					self.setSubtitlesSoft(True)
		except:
			pass

	def __loadValues(self):
		self.mNameProcessed, self.mNameSplit = self.__loadValue(self.mName)
		self.mTitleProcessed, self.mTitleSplit = self.__loadValue(self.mTitle)

		# This is needed, otherwise the audio channels are detected as 8CH in a string link "S10E07 1080p".
		self.mNameReduced = ' '.join(self.mNameSplit)
		for split in self.mTitleSplit:
			self.mNameReduced = self.mNameReduced.replace(split, '')
		self.mNameReduced = re.sub('s\d*e\d*|s\d*', '', self.mNameReduced)

	def __loadValue(self, value):
		if value:
			value = value.lower()
			value = client.replaceHTMLCodes(value)
			value = value.replace("\n", '') # Double quotes with escape characters.
			return value, re.split('\.|\,|\(|\)|\[|\]|\s|\-|\_|\+|\/', value)
		else:
			return '', []

	def __loadSize(self, size):
		if not size or isinstance(size, numbers.Number):
			return size
		elif size.replace(' ', '').isdigit():
			return int(size.replace(' ', ''))
		else:
			size = size.lower()
			bytes = 0

			units = list(self.DictionarySize)
			unitsAll = []
			for unit in units: unitsAll.extend(self.DictionarySize[unit])

			if any(i in unitsAll for i in size):
				bytes = self.__loadNumber(size)
				unit = re.sub('[^a-zA-Z]', '', size)
				if any(unit in i for i in self.DictionarySize[units[1]]): bytes *= 1024
				elif any(unit in i for i in self.DictionarySize[units[2]]): bytes *= 1048576
				elif any(unit in i for i in self.DictionarySize[units[3]]): bytes *= 1073741824
				elif any(unit in i for i in self.DictionarySize[units[4]]): bytes *= 1099511627776

			return bytes

	def __loadNumber(self, value):
		return float(re.sub('[^0-9\.]', '', value))

	def __searchInterpret(self, dictionary, returnInfo = False, endsWith = False):
		if self.mInfo:
			for key in dictionary.iterkeys():
				# Do this instead of [if key.lower() in self.mInfo:], because the audio tag contains the channels and codec.
				# NB: This won't work if one of the Dictionary keys are contained in another Dictionary's key.
				if returnInfo:
					if endsWith:
						for info in self.mInfo:
							if info.endswith(' ' + key.lower()):
								return info
					else:
						for info in self.mInfo:
							if key.lower() in info:
								return info
				else:
					if any(key.lower() in i for i in self.mInfo):
						return key
		return None

	def __searchFind(self, item, dictionary):
		if not item:
			return None
		item = item.lower()
		for key, value in dictionary.iteritems():
			for v in value:
				if item in v or v in item:
					return key
		return None

	def __searchExtract(self, dictionary):
		for key, value in dictionary.iteritems():
			if len(value) > 1 and isinstance(value[0], list) and not isinstance(value[0], basestring):
				contains = True
				for v in value:
					if not self.__searchContains(v):
						contains = False
						break
				if contains:
					return key
			else:
				if self.__searchContains(value):
					return key
		return None

	def __searchContains(self, values = []):
		# If a value contains a space, it will compare it against the full file name (not the split) and also try it with .,+-_
		#   Eg: '5 1' -> '5 1', '5.1', '5,1', '5+1', '5-1', '5_1'
		# If the value starts/ends with a space, it compares against the full file name, with the space trimmed.
		#   Eg: '5 ' -> '5'
		values = self.__searchRemove(values)
		for value in values:
			if value.startswith(' ') or value.endswith(' '):
				if value.replace(' ', '') in self.mNameReduced:
					return True
			elif ' ' in value:
				if any(i in self.mNameReduced for i in [value, value.replace(' ', '.'), value.replace(' ', ','), value.replace(' ', '+'), value.replace(' ', '-'), value.replace(' ', '_')]):
					return True
			elif value in self.mNameSplit:
				return True
		return None

	def __searchRemove(self, values = []):
		# Remove words from the values that are present in the title.
		values = [i.lower() for i in values]
		if self.mTitleSplit:
			for split in self.mTitleSplit:
				result = []
				for value in values:
					if not value == split:
						result.append(value)
				values = result
		return values

	def __searchLanguages(self, language = None):
		results = []
		try:
			if language == None:
				return results
			elif len(language) == 1 and not language[0] == None:
				result = tools.Language.language(language[0][0])
				if result == None or tools.Language.isUniversal(result[0]):
					languages = tools.Language.names(case = tools.Language.CaseLower)

					# Do not use a language that appears in the title, eg: "French Love"
					titleContains = False
					for l in languages:
						for t in self.mTitleSplit:
							if l == t:
								titleContains = True
								break
						if titleContains: break

					if not titleContains:
						for l in languages:
							for n in self.mNameSplit:
								if l == n:
									results.append(tools.Language.language(l))
				else:
					results = language
			elif len(language) > 1:
				results = [tools.Language.language(l[0]) for l in language]
		except:
			tools.Logger.error()

		return results

	def __interpret(self, extract = False):
		self.mEdition = self.__searchInterpret(self.DictionaryEdition)
		if extract and not self.mEdition: self.mEdition = self.__searchExtract(self.DictionaryEdition)

		if not self.mVideoQuality:
			self.mVideoQuality = self.__searchInterpret(self.DictionaryVideoQuality)
			if extract and not self.mVideoQuality:
				self.mVideoQuality = self.__searchExtract(self.DictionaryVideoQuality)
				if not self.mVideoQuality: self.mVideoQuality = self.DefaultVideoQuality

		self.mVideoCodec = self.__searchInterpret(self.DictionaryVideoCodec)
		if extract and not self.mVideoCodec: self.mVideoCodec = self.__searchExtract(self.DictionaryVideoCodec)

		self.mVideoExtra = self.__searchInterpret(self.DictionaryVideoExtra)
		if extract and not self.mVideoExtra: self.mVideoExtra = self.__searchExtract(self.DictionaryVideoExtra)

		self.mSubtitles = self.__searchInterpret(self.DictionarySubtitles)
		if extract and not self.mSubtitles: self.mSubtitles = self.__searchExtract(self.DictionarySubtitles)

		self.mAudioLanguages = self.__searchLanguages(self.mAudioLanguages)

		self.mAudioDubbed = self.__searchInterpret(self.DictionaryAudioDubbed)
		if extract and not self.mAudioDubbed: self.mAudioDubbed = self.__searchExtract(self.DictionaryAudioDubbed)

		self.mAudioChannels = self.__searchInterpret(self.DictionaryAudioChannels)
		if extract and not self.mAudioChannels: self.mAudioChannels = self.__searchExtract(self.DictionaryAudioChannels)

		self.mAudioCodec = self.__searchInterpret(self.DictionaryAudioCodec)
		if extract and not self.mAudioCodec: self.mAudioCodec = self.__searchExtract(self.DictionaryAudioCodec)

		size = self.__searchInterpret(self.DictionarySize, True, True)
		if size: self.setSize(size)

		self.mSeeds = self.__searchInterpret(self.DictionarySeeds, True)
		if self.mSeeds: self.mSeeds = int(self.__loadNumber(self.mSeeds))

		self.mAge = self.__searchInterpret(self.DictionaryAge, True)
		if self.mAge: self.mAge = int(self.__loadNumber(self.mAge))

		self.__processAudio()

	def __extract(self):
		self.mEdition = self.__searchExtract(self.DictionaryEdition)

		self.mVideoQuality = self.__searchExtract(self.DictionaryVideoQuality)
		if not self.mVideoQuality: self.mVideoQuality = self.DefaultVideoQuality

		self.mVideoCodec = self.__searchExtract(self.DictionaryVideoCodec)
		self.mVideoExtra = self.__searchExtract(self.DictionaryVideoExtra)

		self.mSubtitles = self.__searchExtract(self.DictionarySubtitles)

		self.mAudioLanguages = self.__searchLanguages(self.mAudioLanguages)
		self.mAudioDubbed = self.__searchExtract(self.DictionaryAudioDubbed)

		self.mAudioChannels = self.__searchExtract(self.DictionaryAudioChannels)
		self.mAudioCodec = self.__searchExtract(self.DictionaryAudioCodec)
		self.__processAudio()

	def __processAudio(self):
		if not self.mAudioChannels:
			if self.mAudioCodec == 'DD' or self.mAudioCodec == 'DTS':
				self.mAudioChannels = '6CH'
			elif self.mAudioCodec == 'AAC':
				self.mAudioChannels = '2CH'

	def __colorVideoQuality(self):
		qualities = list(self.DictionaryVideoQuality)
		if self.mVideoQuality == qualities[0]:
			return interface.Format.colorLighter(interface.Format.ColorBad, 40)
		elif self.mVideoQuality == qualities[1]:
			return interface.Format.colorLighter(interface.Format.ColorBad, 20)
		elif self.mVideoQuality == qualities[2]:
			return interface.Format.ColorBad
		elif self.mVideoQuality == qualities[3]:
			return interface.Format.colorLighter(interface.Format.ColorPoor, 40)
		elif self.mVideoQuality == qualities[4]:
			return interface.Format.colorLighter(interface.Format.ColorPoor, 20)
		elif self.mVideoQuality == qualities[5]:
			return interface.Format.ColorPoor
		elif self.mVideoQuality == qualities[12]:
			return interface.Format.ColorMedium
		elif self.mVideoQuality == qualities[11]:
			return interface.Format.ColorGood
		elif self.mVideoQuality == qualities[10]:
			return interface.Format.ColorExcellent
		else:
			return interface.Format.ColorUltra

	def __colorSubtitles(self):
		if list(self.DictionarySubtitles)[0] == self.mSubtitles:
			return interface.Format.ColorBad
		else:
			return None

	def __colorSeeds(self):
		colors = interface.Format.colorGradientIncrease(50)
		if self.mSeeds >= len(colors):
			return colors[-1]
		else:
			return colors[self.mSeeds]

	def __colorAge(self):
		colors = interface.Format.colorGradientDecrease(730)
		if self.mAge >= len(colors):
			return colors[-1]
		else:
			return colors[self.mAge]

	def __formatAudio(self, format = False):
		try:
			result = ''
			if self.mAudioDubbed:
				if format: result += ' ' + interface.Format.font(self.mAudioDubbed, color = interface.Format.ColorBad)
				else: result += ' ' + self.mAudioDubbed
			if self.mAudioLanguages:
				languages = []
				for l in self.mAudioLanguages:
					if l: languages.append(l[0].upper())
				if len(languages) > 1 or (len(languages) == 1 and not tools.Language.isUniversal(languages[0])):
					if len(languages) == 1:
						result += languages[0]
					else:
						label = tools.Settings.getInteger('interface.language.stream')
						if label == 0: result += ('-'.join(languages))
						else: result+= interface.Translation.string(35035)
					result += ' '
			if self.mAudioChannels:
				result += ' ' + self.mAudioChannels
			if self.mAudioCodec:
				result += ' ' + self.mAudioCodec
			if result == '':
				return None
			else:
				return result.strip()
		except:
			tools.Logger.error()

	def __formatSize(self):
		if self.mSize:
			units = list(self.DictionarySize)
			if self.mSize < 1024:
				sizeUnit = units[0]
				sizeValue = self.mSize
				sizePlaces = 0
			elif self.mSize < 1048576:
				sizeUnit = units[1]
				sizeValue = self.mSize / 1024.0
				sizePlaces = 0
			elif self.mSize < 1073741824:
				sizeUnit = units[2]
				sizeValue = self.mSize / 1048576.0
				sizePlaces = 0
			elif self.mSize < 1099511627776:
				sizeUnit = units[3]
				sizeValue = self.mSize / 1073741824.0
				sizePlaces = 1
			else:
				sizeUnit = units[4]
				sizeValue = self.mSize / 1099511627776.0
				sizePlaces = 2
			return ('%.*f %s') % (sizePlaces, sizeValue, sizeUnit)
		else:
			return None

	def __formatSeeds(self):
		if self.mSeeds:
			seeds = str(self.mSeeds) + ' ' + list(self.DictionarySeeds)[0]
			if self.mSeeds > 1: seeds += 's'
			return seeds
		else:
			return None

	def __formatAge(self):
		if self.mAge:
			age = str(self.mAge) + ' ' + list(self.DictionaryAge)[0]
			if self.mAge > 1: age += 's'
			return age
		else:
			return None


# Online resources:
#	MetaInfo: +- 50KB
#	FFmpeg: +- 300KB - 400KB
#	Manual: +- 250KB
#	Samba/Network: 3MB

class Extractor(object):

	CommandInitialized = False
	CommandMediainfo = None
	CommandFfmpeg = None

	SizeOnline = 256000 # 250KB
	SizeLocal = 5242880 # 5MB

	def __init__(self, sizeMaximum = SizeOnline): # sizeMaximum is the maximum size to retrive if the file is online.
		self.mTemporaryPath = None
		self.mSizeMaximum = sizeMaximum
		if self.mSizeMaximum <= sizeMaximum:
			self.mSizeChunk = int(math.floor(self.mSizeMaximum / 4))
		else:
			self.mSizeChunk = int(math.floor(self.mSizeMaximum / 8))

		if not self.CommandInitialized:
			self.CommandMediainfo = self.__detectMediainfo()
			if self.CommandMediainfo:
				self.CommandMediainfo += self.__parametersMediainfo()
			self.CommandFfmpeg = self.__detectFfmpeg()
			if self.CommandFfmpeg:
				self.CommandFfmpeg += self.__parametersFfmpeg()
			self.CommandInitialized = True

	def __del__(self):
		self.__stop()
		self.__delete()

	def __delete(self):
		if self.mTemporaryPath:
			return tools.File.delete(self.mTemporaryPath, force = True)
		return False

	def __emptyDictionary(self, dictionary):
		return len(dictionary) == 0

	def __concatenateDictionary(self, dictionary1, dictionary2, dictionary3):
		if not dictionary1: dictionary1 = {}
		if not dictionary2: dictionary2 = {}
		if not dictionary3: dictionary3 = {}
		return dict(dictionary3.items() + dictionary2.items() + dictionary1.items()) # Only updates values if non-exisitng. Updates from back to front.

	def __fullMetadata(self, metadata):
		return not metadata == None and 'video' in metadata and 'audio' in metadata

	def __execute(self, command, timeout = 30):
		try:
			self.mProcess = None
			self.mResult = None
			def run():
				try:
					self.mProcess = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
					self.mResult = self.mProcess.stdout.read().decode('utf-8')
				except:
					pass

			thread = threading.Thread(target = run)
			thread.start()
			thread.join(timeout)
			if thread.is_alive():
				try:
					self.__stop()
					thread.join()
				except:
					pass

			return self.mResult
		except:
			return None

	def __stop(self):
		try:
			processId = self.mProcess.pid
			self.mProcess.terminate()
			self.mProcess.kill()
			os.killpg(processId, signal.SIGKILL) # Force kill by OS, aka Ctrl-C.
		except:
			pass

	def __detectMediainfo(self):
		if 'MediaInfo --Help' in self.__execute('mediainfo'): # Nativley installed
			return 'mediainfo'
		else:
			prefix = None
			path = path = os.path.join(tools.System.pathBinaries(), 'resources', 'data', 'mediainfo')

			if sys.platform == 'win32' or sys.platform == 'win64' or sys.platform == 'windows':
				path = os.path.join(path, 'windows', 'mediainfo.exe')
			elif sys.platform == 'darwin' or sys.platform == 'mac' or sys.platform == 'macosx':
				path = os.path.join(path, 'mac', 'mediainfo')
			else:
				# LD_LIBRARY_PATH to load the libraries from same directory instead of common library path.
				bits, _ = platform.architecture()
				if '64' in bits:
					path = os.path.join(path, 'linux64')
					prefix = 'LD_LIBRARY_PATH=' + path
					path = os.path.join(path, 'mediainfo')
				else:
					path = os.path.join(path, 'linux32')
					prefix = 'LD_LIBRARY_PATH=' + path
					path = os.path.join(path, 'mediainfo')

			if os.path.exists(path):
				if prefix:
					path = prefix + ' ' + path
				if 'MediaInfo --Help' in self.__execute(path):
					return path
		return None

	def __detectFfmpeg(self):
		if 'ffprobe version' in self.__execute('ffprobe'): # Nativley installed
			return 'ffprobe'
		else:
			return None

	def __parametersMediainfo(self):
		return ' --Full "%s"'

	def __parametersFfmpeg(self):
		return ' -loglevel quiet -print_format json -show_format -show_streams -show_error "%s"'

	def __extractChunked(self, link, single = False, timeout = 30, network = False):
		result = None
		self.mTemporaryPath = tools.System.temporaryRandom(directory = 'metadata')

		result = None
		if network:
			tools.File.copy(link, self.mTemporaryPath, self.SizeLocal)
		else:
			neter = network.Networker(link)
			data = ''
			while len(data) < self.mSizeMaximum:
				dataNew = neter.data(start = len(data), size = self.mSizeChunk, timeout = timeout)
				if dataNew:
					data += dataNew
					f = open(self.mTemporaryPath, 'w+')
					f.write(data)
					f.close()

					result = self.extractMediainfo(self.mTemporaryPath, timeout = timeout)
					if not self.__fullMetadata(result):
						result = self.extractFfmpeg(self.mTemporaryPath, timeout = timeout)
						if not self.__fullMetadata(result):
							result = self.extractHachoir(self.mTemporaryPath)
					if self.__fullMetadata(result):
						break
				else:
					break
				if single:
					break

		if not self.__fullMetadata(result):
			result1 = self.extractMediainfo(self.mTemporaryPath, timeout = timeout)
			result2 = self.extractFfmpeg(self.mTemporaryPath, timeout = timeout)
			result3 = self.extractHachoir(self.mTemporaryPath)
			result = self.__concatenateDictionary(result1, result2, result3)

		# Will only show the info of the downloaded chunk, instead of the actual file.
		if 'size' in result:
			del result['size']
		if 'name' in result:
			del result['name']

		self.__delete()
		return result

	def extract(self, pathOrLink, timeout = 30):
		result = {}
		if not isinstance(pathOrLink, basestring):
			return result

		try:
			if tools.File.network(pathOrLink):
				result = self.__extractChunked(link = pathOrLink, network = True)
			else:
				isLink = pathOrLink.startswith('http:') or pathOrLink.startswith('https:') or pathOrLink.startswith('ftp:') or pathOrLink.startswith('ftps:')
				if isLink:
					# Do not use MediaInfo and FFmpeg both, since they are both slow. Rather fallback to manual.
					start = time.time()
					if self.CommandMediainfo:
						result = self.extractMediainfo(pathOrLink, timeout = timeout)
					elif self.CommandFfmpeg:
						result = self.extractMediainfo(pathOrLink, timeout = timeout)
					ellapsed = time.time() - start

					if not result or self.__emptyDictionary(result):
						timeout = int(timeout / 2)
						result = self.__extractChunked(pathOrLink, single = (ellapsed > timeout), timeout = timeout)

				else:
					result1 = self.extractMediainfo(pathOrLink, timeout = timeout)
					result2 = self.extractFfmpeg(pathOrLink, timeout = timeout)
					result3 = self.extractHachoir(pathOrLink)
					result = self.__concatenateDictionary(result1, result2, result3)
		except:
			pass
		return result

	def extractMediainfo(self, pathOrLink, timeout = 30):
		if not self.CommandMediainfo:
			return None
		try:
			data = self.__execute(self.CommandMediainfo % pathOrLink, timeout = timeout)
			return self.__parseMediainfo(data)
		except:
			return None

	def extractFfmpeg(self, pathOrLink, timeout = 30):
		if not self.CommandFfmpeg:
			return None
		try:
			data = self.__execute(self.CommandFfmpeg % pathOrLink, timeout = timeout)
			data = json.loads(data)
			return self.__parseFfmpeg(data)
		except:
			return None

	def extractHachoir(self, path):
		try:
			return self.__parseHachoir(path)
		except:
			return None

	def __parseMediainfo(self, data):
		try:
			info = {}

			resultGeneral = re.search('(General\s*\n([\s\S]*?).*\n\s*\n)', data, re.S)
			if resultGeneral :
				resultGeneral = resultGeneral.group(0)
				try:
					name = re.search("Complete name\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultGeneral, re.S)
					if name: info['name'] = name.group(1)
				except: pass
				try:
					container = re.search("Format\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultGeneral, re.S)
					info['container'] = container.group(1)
				except: pass
				try:
					size = re.search("File size\s*:\s*(\d+)\.?\d*.*\n", resultGeneral, re.S)
					if size: info['size'] = int(size.group(1))
				except: pass
				try:
					duration = re.search("Duration\s*:\s*(\d+)\.?\d*.*\n", resultGeneral, re.S)
					if duration: info['duration'] = int(int(duration.group(1)) / 1000)
				except: pass
				try:
					bitrate = re.search("Overall bit rate\s*:\s*(\d+)\.?\d*.*\n", resultGeneral, re.S)
					if bitrate: info['bitrate'] = int(bitrate.group(1))
				except: pass
				try:
					codec = re.search("Internet media type\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultGeneral, re.S)
					if codec: info['mime'] = codec.group(1)
				except: pass

			# Video

			resultVideo = re.search("(Video[\s\#\d]*\s*\n([\s\S]*?).*\n\s*\n)", data, re.S)
			if resultVideo:
				infoVideo = {}
				resultVideo = resultVideo.group(0)
				if not 'mime' in info or not info['mime']:
					try:
						codec = re.search("Internet media type\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultVideo, re.S)
						if codec: infoVideo['mime'] = codec.group(1)
					except: pass
				try:
					codec = re.search("Codec\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultVideo, re.S)
					if codec: infoVideo['codec'] = codec.group(1)
				except: pass
				try:
					bitrate = re.search("Bit rate\s*:\s*(\d+).*\n", resultVideo, re.S)
					if bitrate: infoVideo['bitrate'] = int(bitrate.group(1))
				except: pass
				try:
					width = re.search("Width\s*:\s*(\d+).*\n", resultVideo, re.S)
					if width: infoVideo['width'] = int(width.group(1))
				except: pass
				try:
					height = re.search("Height\s*:\s*(\d+).*\n", resultVideo, re.S)
					if height: infoVideo['height'] = int(height.group(1))
				except: pass
				try:
					aspectratio = re.search("Display aspect ratio\s*:\s*([\d\.]+).*\n", resultVideo, re.S)
					if aspectratio: infoVideo['aspectratio'] = round(float(aspectratio.group(1)), 3)
				except: pass
				try:
					framerate = re.search("Frame rate\s*:\s*([\d\.]+).*\n", resultVideo, re.S)
					if framerate: infoVideo['framerate'] = round(float(framerate.group(1)), 3)
				except: pass
				try:
					framecount = re.search("Frame count\s*:\s*(\d+)\.?\d*.*\n", resultVideo, re.S)
					if framecount: infoVideo['framecount'] = int(framecount.group(1))
				except: pass
				if not self.__emptyDictionary(infoVideo):
					info['video'] = infoVideo

			# Audio

			resultAudio = re.search("(Audio[\s\#\d]*\s*\n([\s\S]*?).*\n\s*\n)", data, re.S)
			if resultAudio:
				infoAudio = {}
				resultAudio = resultAudio.group(0)
				try:
					codec = re.search("Codec\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultAudio, re.S)
					if codec: infoAudio['codec'] = codec.group(1)
				except: pass
				try:
					bitrate = re.search("Bit rate\s*:\s*(\d+).*\n", resultAudio, re.S)
					if bitrate: infoAudio['bitrate'] = int(bitrate.group(1))
				except: pass
				try:
					channels = re.search("Channel\(s\)\s*:\s*(\d+).*\n",   resultAudio, re.S)
					if channels: infoAudio['channels'] = int(channels.group(1))
				except: pass
				try:
					samplerate = re.search("Sampling rate\s*:\s*([\w\_\-\\\/\@\. ]+).*\n", resultAudio, re.S)
					if samplerate: infoAudio['samplerate'] = int(samplerate.group(1))
				except: pass
				if not self.__emptyDictionary(infoAudio):
					info['audio'] = infoAudio

			# Subtitle
			if re.search("(Text[\s\#\d]*\s*\n([\s\S]*?).*\n\s*\n)", data, re.S):
				info['subtitle'] = True

			# Partial Files
			if not 'video' in info or not 'codec' in info['video'] and resultGeneral:
				if not 'video' in info: infoVideo = {}
				else: infoVideo = info['video']
				try:
					codec = re.search("Codec\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultGeneral, re.S)
					infoVideo['codec'] = codec.group(1)
				except: pass
				if not 'codec' in infoVideo or not infoVideo['codec']:
					try:
						codec = re.search("Format\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultGeneral, re.S)
						infoVideo['codec'] = codec.group(1)
					except: pass
				if not self.__emptyDictionary(infoVideo):
					info['video'] = infoVideo

			if self.__emptyDictionary(info):
				info = None
			return info
		except:
			return None

	def __parseFfmpeg(self, data):
		try:
			info = {}
			indexVideo = None
			indexAudio = None
			indexSubtitle = None

			try:
				for item in data['streams']:
					if item['codec_type'] == 'video':
						indexVideo = item['index']
						break
			except: pass

			try:
				for item in data['streams']:
					if item['codec_type'] == 'audio':
						indexAudio = item['index']
						break
			except: pass

			try:
				for item in data['streams']:
					if item['codec_type'] == 'subtitle':
						indexSubtitle = item['index']
						break
			except: pass

			# File

			try: info['name'] = os.path.basename(data['format']['filename'])
			except: pass
			try: info['container'] = data['format']['format_name']
			except: pass
			try: info['size'] = int(data['format']['size'])
			except: pass
			try: info['duration'] = int(data['format']['duration'])
			except: pass
			try: info['bitrate'] = int(data['format']['bit_rate'])
			except: pass

			# Video

			if not indexVideo == None:
				infoVideo = {}
				try: infoVideo['codec'] = data['streams'][indexVideo]['codec_name']
				except: pass
				try: infoVideo['bitrate'] = int(data['streams'][indexVideo]['bit_rate'])
				except: pass
				try: infoVideo['width'] = int(data['streams'][indexVideo]['width'])
				except: pass
				try: infoVideo['height'] = int(data['streams'][indexVideo]['height'])
				except: pass
				try:
					aspectratio = data['streams'][indexVideo]['display_aspect_ratio']
					aspectratio = aspectratio.split(':')
					aspectratio = float(aspectratio[0]) / float(aspectratio[1])
					aspectratio = round(aspectratio, 3)
					infoVideo['aspectratio'] = aspectratio
				except: pass
				try:
					framerate = data['streams'][indexVideo]['r_frame_rate']
					framerate = framerate.split('/')
					framerate = float(framerate[0]) / float(framerate[1])
					framerate = round(framerate, 3)
					infoVideo['framerate'] = framerate
				except: pass
				try: infoVideo['framecount'] = int(data['streams'][indexVideo]['nb_read_frames'])
				except: pass
				if not self.__emptyDictionary(infoVideo):
					info['video'] = infoVideo

			# Audio

			if not indexAudio == None:
				infoAudio = {}
				try: infoAudio['codec'] = data['streams'][indexAudio]['codec_name']
				except: pass
				try: infoAudio['bitrate'] = int(data['streams'][indexAudio]['bit_rate'])
				except: pass
				try: infoAudio['channels'] = int(data['streams'][indexAudio]['channels'])
				except: pass
				try: infoAudio['samplerate'] = int(data['streams'][indexAudio]['sample_rate'])
				except: pass
				if not self.__emptyDictionary(infoAudio):
					info['audio'] = infoAudio

			# Subtitle

			if not indexSubtitle == None:
				info['subtitle'] = True

			if self.__emptyDictionary(info):
				info = None
			return info
		except:
			return None

	def __parseHachoir(self, path):
		try:
			info = {}
			parser = createParser(unicode(path))
			if parser:
				try:
					metadata = extractMetadata(parser)
				except:
					metadata = None
				if metadata:

					# File

					for item in metadata:
						if item.key == 'filename':
							try: info['name'] = os.path.basename(item.values[0].value)
							except: pass
						elif item.key == 'title' and (not 'name' in info or not info['name'] or info['name'] == ''):
							try: info['name'] = item.values[0].value
							except: pass
						elif item.key == 'file_type':
							try: info['container'] = item.values[0].value
							except: pass
						elif item.key == 'mime_type':
							try: info['mime'] = item.values[0].value
							except: pass
						elif item.key == 'file_size':
							try: info['size'] = item.values[0].value
							except: pass
						elif item.key == 'duration':
							try: info['duration'] = int(item.values[0].value.total_seconds())
							except: pass
						elif item.key == 'bit_rate':
							try: info['bitrate'] = item.values[0].value
							except: pass

					try:
						groups = metadata.groups()
					except:
						groups = None

					if groups:
						for key, value in groups.iteritems():

							# Video

							if 'video' in key:
								infoVideo = {}
								for item in value:
									if item.key == 'compression':
										try: infoVideo['codec'] = item.values[0].value
										except: pass
									if item.key == 'bit_rate':
										try: infoVideo['bitrate'] = int(item.values[0].value)
										except: pass
									if item.key == 'width':
										try: infoVideo['width'] = int(item.values[0].value)
										except: pass
									if item.key == 'height':
										try: infoVideo['height'] = int(item.values[0].value)
										except: pass
									if item.key == 'aspect_ratio':
										try: infoVideo['aspectratio'] = item.values[0].value
										except: pass
									if item.key == 'frame_rate':
										try: infoVideo['framerate'] = round(item.values[0].value, 3)
										except: pass
								if not self.__emptyDictionary(infoVideo):
									info['video'] = infoVideo

							# Audio

							if 'audio' in key:
								infoAudio = {}
								for item in value:
									if item.key == 'compression':
										try: infoAudio['codec'] = item.values[0].value
										except: pass
									if item.key == 'bit_rate':
										try: infoAudio['bitrate'] = int(item.values[0].value)
										except: pass
									if item.key == 'nb_channel':
										try: infoAudio['channels'] = int(item.values[0].value)
										except: pass
									if item.key == 'sample_rate':
										try: infoAudio['samplerate'] = int(item.values[0].value)
										except: pass
								if not self.__emptyDictionary(infoAudio):
									info['audio'] = infoAudio

							# Subtitle

							if 'subtitle' in key:
								info['subtitle'] = True

			# Hachoir only closes files in Python 3, not in Python 2. Manually close it, otherwise the file cannot be deleted.
			# https://bitbucket.org/haypo/hachoir/issues/33/open-file-handles-never-closed
			parser.stream._input.close()

			if self.__emptyDictionary(info):
				info = None
			return info
		except:
			return None
