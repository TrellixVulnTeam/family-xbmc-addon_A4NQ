# -*- coding: utf-8 -*-

'''
	Bubbles Addon
	Copyright (C) 2016 Exodus

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


import re,urllib,urlparse,json,base64,time

from resources.lib.modules import control
# [BUBBLESCODE]
#from resources.lib.modules import pyaes
from resources.lib.externals import pyaes
# [BUBBLESCODE]
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import directstream


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']
		self.domains = ['moviesplanet.is','moviesplanet.tv']
		self.base_link = 'https://www.moviesplanet.tv'
		self.search_link = '/ajax/search.php'
		# [BUBBLESCODE]
		self.enabled = control.setting('accounts.providers.moviesplanet.enabled') == 'true'
		self.user = control.setting('accounts.providers.moviesplanet.user')
		self.password = control.setting('accounts.providers.moviesplanet.pass')
		# [/BUBBLESCODE]

	def movie(self, imdb, title, localtitle, aliases, year):
		try:
			# [BUBBLESCODE]
			#if (self.user == '' or self.password == ''): raise Exception()
			if (not self.enabled or self.user == '' or self.password == ''): raise Exception()
			# [/BUBBLESCODE]

			t = cleantitle.get(title)

			u = urlparse.urljoin(self.base_link, self.search_link)

			p = {'q': title.rsplit(':', 1)[0], 'limit': '10', 'timestamp': int(time.time() * 1000), 'verifiedCheck': ''}
			p = urllib.urlencode(p)

			r = client.request(u, post=p, XHR=True)
			r = json.loads(r)

			r = [i for i in r if i['meta'].strip().split()[0].lower() == 'movie']
			r = [i['permalink'] for i in r if t == cleantitle.get(i['title'])][:2]
			r = [(i, urlparse.urljoin(self.base_link, i)) for i in r]
			r = [(i[0], client.request(i[1])) for i in r]
			r = [(i[0], i[1]) for i in r if not i[1] == None]
			r = [(i[0], re.sub('\s|<.+?>|</.+?>', '', i[1])) for i in r]
			r = [(i[0], re.findall('eleased:(\d{4})', i[1])) for i in r]
			r = [(i[0], i[1][0]) for i in r if i[1]]
			r = [i for i in r if year in i[1]]
			r = r[0][0]

			url = re.findall('(?://.+?|)(/.+)', r)[0]
			url = client.replaceHTMLCodes(url)
			url = url.encode('utf-8')
			return url
		except:
			return


	def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
		try:
			# [BUBBLESCODE]
			#if (self.user == '' or self.password == ''): raise Exception()
			if (not self.enabled or self.user == '' or self.password == ''): raise Exception()
			# [/BUBBLESCODE]

			t = cleantitle.get(tvshowtitle)

			u = urlparse.urljoin(self.base_link, self.search_link)

			p = {'q': tvshowtitle.rsplit(':', 1)[0], 'limit': '10', 'timestamp': int(time.time() * 1000), 'verifiedCheck': ''}
			p = urllib.urlencode(p)

			r = client.request(u, post=p, XHR=True)
			r = json.loads(r)

			r = [i for i in r if i['meta'].strip().split()[0].lower() == 'tv']
			r = [i['permalink'] for i in r if t == cleantitle.get(i['title'])][:2]
			r = [(i, urlparse.urljoin(self.base_link, i)) for i in r]
			r = [(i[0], client.request(i[1])) for i in r]
			r = [(i[0], i[1]) for i in r if not i[1] == None]
			r = [(i[0], re.sub('\s|<.+?>|</.+?>', '', i[1])) for i in r]
			r = [(i[0], re.findall('eleased:(\d{4})', i[1])) for i in r]
			r = [(i[0], i[1][0]) for i in r if i[1]]
			r = [i for i in r if year in i[1]]
			r = r[0][0]

			url = re.findall('(?://.+?|)(/.+)', r)[0]
			url = client.replaceHTMLCodes(url)
			url = url.encode('utf-8')
			return url
		except:
			return


	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			# [BUBBLESCODE]
			#if (self.user == '' or self.password == ''): raise Exception()
			if (not self.enabled or self.user == '' or self.password == ''): raise Exception()
			# [/BUBBLESCODE]

			if url == None: return

			url = '%s/season/%01d/episode/%01d' % (url, int(season), int(episode))
			url = client.replaceHTMLCodes(url)
			url = url.encode('utf-8')
			return url
		except:
			return


	def _gkdecrypt(self, key, str):
		try:
			key += (24 - len(key)) * '\0'
			decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationECB(key))
			str = decrypter.feed(str.decode('hex')) + decrypter.feed()
			str = str.split('\0', 1)[0]
			return str
		except:
			return


	def sources(self, url, hostDict, hostprDict):
		try:
			sources = []

			if url == None: return sources

			# [BUBBLESCODE]
			#if (self.user == '' or self.password == ''): raise Exception()
			if (not self.enabled or self.user == '' or self.password == ''): raise Exception()
			# [/BUBBLESCODE]
			
			login = urlparse.urljoin(self.base_link, '/login')
			post = {'username': self.user, 'password': self.password, 'returnpath': '/'}
			post = urllib.urlencode(post)

			headers = {'User-Agent':client.randomagent()}
			rlogin = client.request(login, headers=headers, post=post, output='extended')
			guid = re.findall('(.*?);\s', rlogin[2]['Set-Cookie'])[0]
			headers['Cookie'] += '; '+guid
			url = urlparse.urljoin(self.base_link, url)

			result = client.request(url, headers=headers)

			url = re.findall("embeds\[\d+\]\s*=\s*'([^']+)", result)[0]
			url = client.parseDOM(url, 'iframe', ret='src')[0]
			url = url.replace('https://', 'http://')

			links = []

			try:
				dec = re.findall('mplanet\*(.+)', url)[0]
				dec = dec.rsplit('&')[0]
				dec = self._gkdecrypt(base64.b64decode('MllVcmlZQmhTM2swYU9BY0lmTzQ='), dec)
				dec = directstream.google(dec)

				links += [(i['url'], i['quality'], 'gvideo') for i in dec]
			except:
				pass

			result = client.request(url, headers=headers)

			try:
				url = re.findall('src\s*=\s*(?:\'|\")(http.+?)(?:\'|\")', result)
				for i in url:
					try: links.append({'source': 'gvideo', 'quality': directstream.googletag(i)[0]['quality'], 'url': i})
					except: pass
			except:
				pass

			try:
				url = client.parseDOM(result, 'source', ret='src')
				url += re.findall('src\s*:\s*\'(.*?)\'', result)
				url = [i for i in url if '://' in i]
				links.append({'source': 'cdn', 'quality': 'HD', 'url': url[0]})
			except:
				pass

			# [BUBBLESCODE]
			#for i in links: sources.append({'source': i['source'], 'quality': i['quality'], 'language': 'en', 'url': i['url'], 'direct': True, 'debridonly': False})
			for i in links: sources.append({'source': i['source'], 'quality': i['quality'], 'language': 'en', 'url': i['url'], 'direct': True, 'debridonly': False, 'memberonly' : True})
			# [BUBBLESCODE]

			return sources
		except:
			return sources


	def resolve(self, url):
		try:
			url = client.request(url, output='geturl')
			return url
		except:
			return


