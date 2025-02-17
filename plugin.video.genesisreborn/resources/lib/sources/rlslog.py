# -*- coding: utf-8 -*-

'''
    
    

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



import re,urllib,urlparse,random
from resources.lib.modules import control
from resources.lib.modules import cleantitle
from resources.lib.modules import client
debridstatus = control.setting('debridsources')
from resources.lib.modules.common import  random_agent, quality_tag
from BeautifulSoup import BeautifulSoup
from schism_commons import quality_tag, google_tag, parseDOM, replaceHTMLCodes ,cleantitle_get, cleantitle_get_2, cleantitle_query, get_size, cleantitle_get_full

class source:
    def __init__(self):
        self.domains = ['releaselog.org']
        self.base_link = 'http://releaselog.org/index.php'
        self.search_link = '/search/%s+%s/feed/rss2/'
			
    def movie(self, imdb, title, year):
		self.genesisreborn_url = []
		try:
			if not debridstatus == 'true': raise Exception()			
			title = cleantitle.getsearch(title)
			cleanmovie = cleantitle.get(title)
			titlecheck = cleanmovie+year
			query = self.search_link % (urllib.quote_plus(title),year)
			query = self.base_link + query
			r = client.request(query)
			posts = client.parseDOM(r, 'item')	
			items = []
			for post in posts:
				try:
						
					t = client.parseDOM(post, 'title')[0]
					t = t.encode('utf-8')
					if not cleanmovie in cleantitle.get(t) and year in t.lower(): continue
					
					c = client.parseDOM(post, 'content.+?')[0]
					u = client.parseDOM(post, 'a', ret='href')
					
					if not u: raise Exception()
					u = [(t, i) for i in u]
					self.genesisreborn_url += u
					
				except:
					pass
			print ("RLSLOG PASSED", self.genesisreborn_url)		
			return self.genesisreborn_url

		except:
			return	
			
			
			
    def tvshow(self, imdb, tvdb, tvshowtitle, year):
        try:
            url = {'tvshowtitle': tvshowtitle, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return			

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        self.genesisreborn_url = []
        try:
			if not debridstatus == 'true': raise Exception()
			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = cleantitle.getsearch(title)
			cleanmovie = cleantitle.get(title)
			data['season'], data['episode'] = season, episode
			episodecheck = 'S%02dE%02d' % (int(data['season']), int(data['episode']))
			episodecheck = str(episodecheck).lower()
			query = 'S%02dE%02d' % (int(data['season']), int(data['episode']))
			query = self.search_link % (urllib.quote_plus(title),query)
			query = self.base_link +  query
			print ("WRZCRAFT SHOW", query)		
			
			r = client.request(query)
			posts = client.parseDOM(r, 'item')	
			for post in posts:
				try:
					t = client.parseDOM(post, 'title')[0]
					t = t.encode('utf-8')
					if not cleanmovie in cleantitle.get(t) and episodecheck in t.lower(): continue
					print ("RLSLOG PASSED", t)		
					c = client.parseDOM(post, 'content.+?')[0]
					u = client.parseDOM(post, 'a', ret='href')
					print ("RLSLOG 3", u)	
					if not u: raise Exception()
					u = [(t, i) for i in u]
					self.genesisreborn_url += u

				except:
					pass
			print ("RLSLOG PASSED", self.genesisreborn_url)		
			return self.genesisreborn_url
        except:
            return			
			
			
    def sources(self, url, hostDict, hostprDict):
        try:
			sources = []
			for title,url in self.genesisreborn_url:
				quality = "SD"
				quality = quality_tag(title)
				if "1080p" in url.lower(): quality = "1080p"
				elif "720p" in url.lower(): quality = "HD"

				
				info = ''
				if "hevc" in title.lower(): info = "HEVC"					
				if any(value in url for value in hostprDict):
					try:host = re.findall('([\w]+[.][\w]+)$', urlparse.urlparse(url.strip().lower()).netloc)[0]
					except: host = 'Videomega'
					url = client.replaceHTMLCodes(url)
					url = url.encode('utf-8')
					sources.append({'source': host, 'quality': quality, 'provider': 'Rlslog', 'url': url, 'info': info,'direct': False, 'debridonly': True})
			return sources
        except:
            return sources


    def resolve(self, url):

            return url