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

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import source_utils


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['de']
		self.domains = ['streamkiste.tv']
		self.base_link = 'http://streamkiste.tv'
		self.search_link = '/livesearch.php?keyword=%s&nonce=%s'
		self.drop_link = '/drop.php'

	def movie(self, imdb, title, localtitle, year):
		try:
			url = self.__search(title, year)
			if not url and title != localtitle: url = self.__search(localtitle, year)
			return url
		except:
			return

	# code is equal to 1kino
	def sources(self, url, hostDict, hostprDict):
		sources = []

		try:
			if url == None:
				return sources

			url = urlparse.urljoin(self.base_link, url)

			r = client.request(url)
			r = client.parseDOM(r, 'div', attrs={'id': 'stream-container'})[0]

			r = re.compile('<div id="stream-h">.*?</li>.*?</div>\s*</div>', re.IGNORECASE | re.DOTALL).findall(r)
			r = [(client.parseDOM(i, 'div', attrs={'id': 'mirror-head'}),
				  client.parseDOM(i, 'div', attrs={'id': 'stream-links'})
				  ) for i in r]
			r = [(i[0][0], i[1]) for i in r if len(i[0]) > 0]
			r = [(re.findall('.+\|(.+)', i[0]), i[1]) for i in r]
			r = [(i[0][0].strip(), i[1]) for i in r if len(i[0]) > 0]

			for name, links in r:
				quality, info = source_utils.get_release_quality(name)

				links = [(client.parseDOM(i, 'a', ret='href'), client.parseDOM(i, 'a')) for i in links]
				links = [(i[0][0], i[1][0].lower().strip()) for i in links if len(i[0]) > 0 and len(i[1]) > 0]

				info = ' | '.join(info)

				for link, hoster in links:
					valid, hoster = source_utils.is_host_valid(hoster, hostDict)
					if not valid: continue

					sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': link, 'info': info, 'direct': False, 'debridonly': False, 'checkquality': True})

			return sources
		except:
			return sources

	def resolve(self, url):
		try:
			url = client.request(url, output='geturl')
			if self.base_link not in url:
				return url
		except:
			return

	def __search(self, title, year):
		try:
			r = client.request(self.base_link)
			r = re.findall('sL10n\s*=\s*({.*?});', r)[0]
			r = json.loads(r)['nonce']

			query = self.search_link % (urllib.quote_plus(cleantitle.query(title)), r)
			query = urlparse.urljoin(self.base_link, query)

			t = cleantitle.get(title)
			y = ['%s' % str(year), '%s' % str(int(year) + 1), '%s' % str(int(year) - 1), '0']

			r = client.request(query)
			r = json.loads(r)
			r = [(i, r[i].get('url', ''), r[i].get('title', ''), r[i].get('extra', {}).get('names', ''), r[i].get('extra', {}).get('date', '0')) for i in r]
			r = [(i[0], i[1], client.replaceHTMLCodes(i[2]), client.replaceHTMLCodes(i[3]), i[4]) for i in r]
			r = sorted(r, key=lambda i: int(i[4]), reverse=True)  # with year > no year
			r = [i[1] for i in r if (t == cleantitle.get(i[2]) or t == cleantitle.get(i[3])) and i[4] in y][0]

			url = re.findall('(?://.+?|)(/.+)', r)[0]
			url = client.replaceHTMLCodes(url)
			url = url.encode('utf-8')

			return url
		except:
			return
