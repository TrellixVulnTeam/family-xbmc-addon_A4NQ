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

import re,urllib,urlparse,xbmc
from resources.lib.modules import client
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import network
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source:

	def __init__(self):
		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['torrentleech.org']
		self.base_link = 'https://www.torrentleech.org'
		self.login_link = '/user/account/login/'
		self.search_link = '/torrents/browse/index/query/%s/categories/%s/orderby/seeders/order/desc/page/%d'
		self.category_movie = '1,8,9,11,37,43,14,12,13,41,15,29,36'
		self.category_show = '2,26,32,44,27'

		self.enabled = tools.Settings.getBoolean('accounts.providers.torrentleech.enabled')
		self.username = tools.Settings.getString('accounts.providers.torrentleech.user')
		self.password = tools.Settings.getString('accounts.providers.torrentleech.pass')

	def movie(self, imdb, title, localtitle, year):
		try:
			url = {'imdb': imdb, 'title': title, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return

	def tvshow(self, imdb, tvdb, tvshowtitle, localtitle, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if url == None: return
			url = urlparse.parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urllib.urlencode(url)
			return url
		except:
			return

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None:
				raise Exception()

			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			year = int(data['year']) if 'year' in data and not data['year'] == None else None
			season = int(data['season']) if 'season' in data and not data['season'] == None else None
			episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
			pack = data['pack'] if 'pack' in data else False

			category = self.category_show if 'tvshowtitle' in data else self.category_movie

			if 'tvshowtitle' in data:
				if pack: query = '%s %d' % (title, season)
				else: query = '%s S%02dE%02d' % (title, season, episode)
			else:
				query = '%s %d' % (title, year)
			query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)
			querySplit = query.split()

			# Login
			if self.enabled and self.username and not self.username == '' and self.password and not self.password == '':
				login = self.base_link + self.login_link
				post = urllib.urlencode({'username': self.username, 'password': self.password, 'submit': 'submit'})
				cookie = client.request(login, post = post, output = 'cookie', close = False)
				response = client.request(login, post = post, cookie = cookie, output = 'extended')
				headers = {'User-Agent': response[3]['User-Agent'], 'Cookie': response[3]['Cookie']}
			else:
				cookie = None
				headers = None

			url = urlparse.urljoin(self.base_link, self.search_link)

			page = 1
			added = False
			firstLink = None

			timerEnd = tools.Settings.getInteger('scraping.providers.timeout') - 8
			timer = tools.Time(start = True)

			while True:
				# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
				if timer.elapsed() > timerEnd:
					break

				urlNew = url % (urllib.quote_plus(query), urllib.quote_plus(category), page)
				html = BeautifulSoup(client.request(urlNew, cookie = cookie))

				page += 1
				added = False

				htmlTable = html.find_all('table', id = 'torrenttable')[0].find_all('tbody')[0]
				htmlRows = htmlTable.find_all('tr', recursive = False) # Do not search further down the tree (just the direct children), because that will also retrieve the header row.

				for i in range(len(htmlRows)):
					htmlRow = htmlRows[i]

					# Name
					htmlName = htmlRow.find_all('td', class_ = 'name', recursive = False)[0]
					htmlName = htmlName.find_all('span', class_ = 'title', recursive = False)[0]
					htmlName = htmlName.find_all('a')[0].getText().strip()

					# Link
					htmlLink = htmlRow.find_all('td', class_ = 'quickdownload', recursive = False)[0]
					htmlLink = htmlLink.find_all('a')[0]['href']

					# Continuing with page will always show the torrents of the last page.
					# Stop once the first link is the same.
					if i == 0:
						if firstLink == htmlLink:
							break
						firstLink = htmlLink

					if not headers == None:
						htmlLink += '|' + urllib.urlencode(headers)

					# Size
					htmlSize = htmlRow.find_all('td')[4].getText().strip()

					# Seeds
					htmlSeeds = htmlRow.find_all('td', class_ = 'seeders')[0].getText().strip()

					# Metadata
					meta = metadata.Metadata(name = htmlName, title = title, year = year, season = season, episode = episode, pack = pack, link = htmlLink, size = htmlSize, seeds = htmlSeeds)

					# Ignore
					if meta.ignore(True):
						continue

					# Add
					sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'info' : meta.information(), 'file' : htmlName})
					added = True

				if not added: # Last page reached with a working torrent
					break

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
