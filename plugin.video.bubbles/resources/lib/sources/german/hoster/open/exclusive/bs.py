# -*- coding: utf-8 -*-

'''
	Bubbles Add-on
	Copyright (C) 2016 Viper2k4

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

import re, urllib, urlparse, json

from resources.lib.modules import cache
from resources.lib.modules import client
from resources.lib.modules import cleantitle


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['de']
		self.domains = ['bs.to']
		self.base_link = 'https://www.bs.to/'
		self.api_link = 'api/%s'

	def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, year):
		try:
			t = cleantitle.get(tvshowtitle)
			j_c = cache.get(self.__get_json, 12, "series")
			j = [i['id'] for i in j_c if t == cleantitle.get(i["series"])]
			if len(j) == 0:
				t = cleantitle.get(localtvshowtitle)
				j = [i['id'] for i in j_c if t == cleantitle.get(i["series"])]

			return 'series/%s/' % j[0]
		except:
			return

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if url == None: return
			return url + "%s/%s" % (season, episode)
		except:
			return

	def sources(self, url, hostDict, hostprDict):
		sources = []

		try:
			if url == None:
				return sources

			hostDict = [(i.rsplit('.', 1)[0], i) for i in hostDict]
			locDict = [i[0] for i in hostDict]
			locDict.append('openloadhd')

			j = self.__get_json(url)
			j = [i for i in j['links'] if 'links' in j]
			j = [(i['hoster'].lower(), i['id']) for i in j if i['hoster'].lower() in locDict]
			j = [(re.sub('hd$', '', i[0]), i[1], 'HD' if i[0].endswith('hd') else 'SD') for i in j]
			j = [([x[1] for x in hostDict if x[0] == i[0]][0], i[1], i[2]) for i in j]

			for hoster, url, quality in j:
				sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': ('watch/%s' % url), 'direct': False, 'debridonly': False})

			return sources
		except:
			return sources

	def resolve(self, url):
		try: return self.__get_json(url)['fullurl']
		except: return

	def __get_json(self, api_call):
		try:
			headers = bs_finalizer().get_header(api_call)
			result = client.request(urlparse.urljoin(self.base_link, self.api_link % api_call), headers=headers)
			return json.loads(result)
		except:
			return

#############################################################

import sys
import time
import json as j
import base64 as l1
import hmac as l11ll1
import hashlib as l1ll


# Bubbles - Removed, because of Exodus exclusive.

class bs_finalizer:
	def __init__(self):
		self.l1lll1 = sys.version_info[0] == 2
		self.l11 = 26
		self.l1l1l1 = 2048
		self.l11l = 7
		self.l1l1 = False

		try:
			self.l11l1l = self.l1111(u"XXXXXXXXXXXXXX")
			self.l1l111 = self.l1111(u"XXXXXXXXXXXXXX")
		except:
			pass

	def l1111(self, ll):
		l1ll11 = ord(ll[-1]) - self.l1l1l1
		ll = ll[:-1]

		if ll:
			l111l1 = l1ll11 % len(ll)
		else:
			l111l1 = 0

		if self.l1lll1:
			l111 = u''.join([unichr(ord(l1111l) - self.l1l1l1 - (l1l11l + l1ll11) % self.l11l) for l1l11l, l1111l in
							 enumerate(ll[:l111l1] + ll[l111l1:])])
		else:
			l111 = ''.join([unichr(ord(l1111l) - self.l1l1l1 - (l1l11l + l1ll11) % self.l11l) for l1l11l, l1111l in
							enumerate(ll[:l111l1] + ll[l111l1:])])

		if self.l1l1:
			return str(l111)
		else:
			return l111

	def get_header(self, string):
		return {self.l1111(u"XXXXXXXXXXXXXX"): self.l111ll(string), self.l1111(u"XXXXXXXXXXXXXX"): self.l1111(u"XXXXXXXXXXXXXX")}

	def l111ll(self, l1lll):
		l11l11 = int(time.time())
		l11lll = {self.l1111(u"XXXXXXXXXXXXXX"): self.l11l1l, self.l1111(u"XXXXXXXXXXXXXX"): l11l11,
				  self.l1111(u"XXXXXXXXXXXXXX"): self.l1l11(l11l11, l1lll)}
		return l1.b64encode(j.dumps(l11lll).encode(self.l1111(u"XXXXXXXXXXXXXX")))

	def l1l11(self, l11l11, l1l1l):
		l1ll1 = self.l1l111.encode(self.l1111(u'XXXXXXXXXXXXXX'))
		l1l1ll = str(l11l11) + self.l1111(u'XXXXXXXXXXXXXX') + str(l1l1l)
		l1l1ll = l1l1ll.encode(self.l1111(u'XXXXXXXXXXXXXX'))
		l1lllll = l11ll1.new(l1ll1, l1l1ll, digestmod=l1ll.sha256)
		return l1lllll.hexdigest()
