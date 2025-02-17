# -*- coding: utf-8 -*-

'''
	Bubbles Add-on
	Copyright (C) 2016 Bubbles, Exodus

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


import re,unicodedata


def get(title):
	if title == None: return
	title = re.sub('&#(\d+);', '', title)
	title = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
	title = title.replace('&quot;', '\"').replace('&amp;', '&')
	title = re.sub('\n|([[].+?[]])|([(].+?[)])|\s(vs|v[.])\s|(:|;|-|"|,|\'|\_|\.|\?)|\s', '', title).lower()
	return title


def geturl(title):
	if title == None: return
	title = title.lower()

	# Bubbles
	#title = title.translate(None, ':*?"\'\.<>|&!,')
	try:
		# This gives a weird error saying that translate only takes 1 argument, not 2. However, the Python 2 documentation states 2, but 1 for Python 3.
		# This has most likley to do with titles being unicode (foreign titles)
		title = title.translate(None, ':*?"\'\.<>|&!,')
	except:
		for c in ':*?"\'\.<>|&!,':
			title = title.replace(c, '')

	title = title.replace('/', '-')
	title = title.replace(' ', '-')
	title = title.replace('--', '-')
	return title


def get_simple(title):
	if title == None: return
	title = title.lower()
	title = re.sub('(\d{4})', '', title)
	title = re.sub('&#(\d+);', '', title)
	title = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
	title = title.replace('&quot;', '\"').replace('&amp;', '&')
	title = re.sub('\n|\(|\)|\[|\]|\{|\}|\s(vs|v[.])\s|(:|;|-|"|,|\'|\_|\.|\?)|\s', '', title).lower()
	return title


def getsearch(title):
	if title == None: return
	title = title.lower()
	title = re.sub('&#(\d+);', '', title)
	title = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
	title = title.replace('&quot;', '\"').replace('&amp;', '&')
	title = re.sub('\\\|/|-|:|;|\*|\?|"|\'|<|>|\|', '', title).lower()
	return title


def query(title):
	if title == None: return
	title = title.replace('\'', '').rsplit(':', 1)[0]
	return title


def normalize(title):
	try:
		try: return title.decode('ascii').encode("utf-8")
		except: pass
		return str( ''.join(c for c in unicodedata.normalize('NFKD', unicode( title.decode('utf-8') )) if unicodedata.category(c) != 'Mn') )
	except:
		return title
