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


from resources.lib.modules import trakt
from resources.lib.modules import cleantitle
from resources.lib.modules import cleangenre
from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import cache
from resources.lib.modules import playcount
from resources.lib.modules import workers
from resources.lib.modules import views
from resources.lib.modules import metacache

from resources.lib.indexers import episodes as episodesx

from resources.lib.extensions import tools
from resources.lib.extensions import interface

import os,sys,re,json,zipfile,StringIO,urllib,urllib2,urlparse,datetime

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))

action = params.get('action')


class seasons:

	def __init__(self, type = tools.Media.TypeShow, kids = tools.Selection.TypeUndefined):
		self.type = type

		self.kids = kids
		self.certificates = None
		self.restriction = 0

		if self.kidsOnly():
			self.certificates = []
			self.restriction = tools.Settings.getInteger('general.kids.restriction')
			if self.restriction >= 0:
				self.certificates.append('TV-Y')
			if self.restriction >= 1:
				self.certificates.append('TV-Y7')
			if self.restriction >= 2:
				self.certificates.append('TV-PG')
			if self.restriction >= 3:
				self.certificates.append('TV-14')
			self.certificates = ','.join(self.certificates).replace('-', '_').lower()
			self.certificates = '&certificates=us:' + self.certificates
		else:
			self.certificates = ''

		self.list = []

		self.lang = control.apiLanguage()['tvdb']
		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))
		self.today_date = (self.datetime).strftime('%Y-%m-%d')
		self.tvdb_key = 'MDk1NUY1N0Q5QTlENEZEQw=='

		self.trakt_user = control.setting('accounts.informants.trakt.user').strip()
		self.traktwatchlist_link = 'http://api-v2launch.trakt.tv/users/me/watchlist/seasons'
		self.traktlist_link = 'http://api-v2launch.trakt.tv/users/%s/lists/%s/items'
		self.traktlists_link = 'http://api-v2launch.trakt.tv/users/me/lists'

		self.tvdb_info_link = 'http://thetvdb.com/api/%s/series/%s/all/%s.zip' % (self.tvdb_key.decode('base64'), '%s', '%s')
		self.tvdb_by_imdb = 'http://thetvdb.com/api/GetSeriesByRemoteID.php?imdbid=%s'
		self.tvdb_by_query = 'http://thetvdb.com/api/GetSeries.php?seriesname=%s'
		self.imdb_by_query = 'http://www.omdbapi.com/?t=%s&y=%s'
		self.tvdb_image = 'http://thetvdb.com/banners/'
		self.tvdb_poster = 'http://thetvdb.com/banners/_cache/'

	def parameterize(self, action):
		if not self.type == None: action += '&type=%s' % self.type
		if not self.kids == None: action += '&kids=%d' % self.kids
		return action

	def kidsOnly(self):
		return self.kids == tools.Selection.TypeInclude

	def get(self, tvshowtitle, year, imdb, tvdb, idx=True):
		if control.window.getProperty('PseudoTVRunning') == 'True':
			return episodes().get(tvshowtitle, year, imdb, tvdb)

		if idx == True:
			self.list = cache.get(self.tvdb_list, 24, tvshowtitle, year, imdb, tvdb, self.lang)
			self.seasonDirectory(self.list)
			return self.list
		else:
			self.list = self.tvdb_list(tvshowtitle, year, imdb, tvdb, 'en')
			return self.list


	def seasonList(self, url):
		# Dirty implementation, but avoids rewritting everything from episodes.py.

		episodes = episodesx.episodes(type = self.type, kids = self.kids)
		self.list = cache.get(episodes.trakt_list, 0, url, self.trakt_user)
		self.list = self.list[::-1]

		episodes.list = self.list
		episodes.worker()
		self.list = episodes.list

		self.seasonDirectory(self.list)


	def userlists(self):
		episodes = episodesx.episodes(type = self.type, kids = self.kids)
		userlists = []

		try:
			if trakt.getTraktCredentialsInfo() == False: raise Exception()
			activity = trakt.getActivity()
		except:
			pass

		try:
			if trakt.getTraktCredentialsInfo() == False: raise Exception()
			self.list = []
			try:
				if activity > cache.timeout(episodes.trakt_user_list, self.traktlists_link, self.trakt_user): raise Exception()
				userlists += cache.get(episodes.trakt_user_list, 3, self.traktlists_link, self.trakt_user)
			except:
				userlists += cache.get(episodes.trakt_user_list, 0, self.traktlists_link, self.trakt_user)
		except:
			pass

		try:
			if trakt.getTraktCredentialsInfo() == False: raise Exception()
			self.list = []
			try:
				if activity > cache.timeout(episodes.trakt_user_list, self.traktlikedlists_link, self.trakt_user): raise Exception()
				userlists += cache.get(episodes.trakt_user_list, 3, self.traktlikedlists_link, self.trakt_user)
			except:
				userlists += cache.get(episodes.trakt_user_list, 0, self.traktlikedlists_link, self.trakt_user)
		except:
			pass

		self.list = []

		# Filter the user's own lists that were
		for i in range(len(userlists)):
			contains = False
			adapted = userlists[i]['url'].replace('/me/', '/%s/' % self.trakt_user)
			for j in range(len(self.list)):
				if adapted == self.list[j]['url'].replace('/me/', '/%s/' % self.trakt_user):
					contains = True
					break
			if not contains:
				self.list.append(userlists[i])

		for i in range(0, len(self.list)): self.list[i].update({'image': 'traktlists.png', 'action': self.parameterize('seasonList')})

		# Watchlist
		if trakt.getTraktCredentialsInfo():
		    self.list.insert(0, {'name' : interface.Translation.string(32033), 'url' : self.traktwatchlist_link, 'context' : self.traktwatchlist_link, 'image': 'traktwatch.png', 'action': self.parameterize('seasons')})

		episodes.addDirectory(self.list, queue = True)
		return self.list


	def tvdb_list(self, tvshowtitle, year, imdb, tvdb, lang, limit=''):
		try:
			if imdb == '0':
				try:
					imdb = trakt.SearchTVShow(urllib.quote_plus(tvshowtitle), year, full=False)[0]
					imdb = imdb.get('show', '0')
					imdb = imdb.get('ids', {}).get('imdb', '0')
					imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))

					if not imdb: imdb = '0'
				except:
					imdb = '0'

			if tvdb == '0' and not imdb == '0':
				url = self.tvdb_by_imdb % imdb

				result = client.request(url, timeout='10')

				try: tvdb = client.parseDOM(result, 'seriesid')[0]
				except: tvdb = '0'

				try: name = client.parseDOM(result, 'SeriesName')[0]
				except: name = '0'
				dupe = re.compile('[***]Duplicate (\d*)[***]').findall(name)
				if len(dupe) > 0: tvdb = str(dupe[0])

				if tvdb == '': tvdb = '0'


			if tvdb == '0':
				url = self.tvdb_by_query % (urllib.quote_plus(tvshowtitle))

				years = [str(year), str(int(year)+1), str(int(year)-1)]

				tvdb = client.request(url, timeout='10')
				tvdb = re.sub(r'[^\x00-\x7F]+', '', tvdb)
				tvdb = client.replaceHTMLCodes(tvdb)
				tvdb = client.parseDOM(tvdb, 'Series')
				tvdb = [(x, client.parseDOM(x, 'SeriesName'), client.parseDOM(x, 'FirstAired')) for x in tvdb]
				tvdb = [(x, x[1][0], x[2][0]) for x in tvdb if len(x[1]) > 0 and len(x[2]) > 0]
				tvdb = [x for x in tvdb if cleantitle.get(tvshowtitle) == cleantitle.get(x[1])]
				tvdb = [x[0][0] for x in tvdb if any(y in x[2] for y in years)][0]
				tvdb = client.parseDOM(tvdb, 'seriesid')[0]

				if tvdb == '': tvdb = '0'
		except:
			return


		try:
			if tvdb == '0': return

			url = self.tvdb_info_link % (tvdb, 'en')
			data = urllib2.urlopen(url, timeout=30).read()

			zip = zipfile.ZipFile(StringIO.StringIO(data))
			result = zip.read('%s.xml' % 'en')
			artwork = zip.read('banners.xml')
			zip.close()

			dupe = client.parseDOM(result, 'SeriesName')[0]
			dupe = re.compile('[***]Duplicate (\d*)[***]').findall(dupe)

			if len(dupe) > 0:
				tvdb = str(dupe[0]).encode('utf-8')

				url = self.tvdb_info_link % (tvdb, 'en')
				data = urllib2.urlopen(url, timeout=30).read()

				zip = zipfile.ZipFile(StringIO.StringIO(data))
				result = zip.read('%s.xml' % 'en')
				artwork = zip.read('banners.xml')
				zip.close()

			if not lang == 'en':
				url = self.tvdb_info_link % (tvdb, lang)
				data = urllib2.urlopen(url, timeout=30).read()

				zip = zipfile.ZipFile(StringIO.StringIO(data))
				result2 = zip.read('%s.xml' % lang)
				zip.close()
			else:
				result2 = result


			artwork = artwork.split('<Banner>')
			artwork = [i for i in artwork if '<Language>en</Language>' in i and '<BannerType>season</BannerType>' in i]
			artwork = [i for i in artwork if not 'seasonswide' in re.findall('<BannerPath>(.+?)</BannerPath>', i)[0]]


			result = result.split('<Episode>')
			result2 = result2.split('<Episode>')

			item = result[0] ; item2 = result2[0]

			episodes = [i for i in result if '<EpisodeNumber>' in i]
			episodes = [i for i in episodes if not '<SeasonNumber>0</SeasonNumber>' in i]
			episodes = [i for i in episodes if not '<EpisodeNumber>0</EpisodeNumber>' in i]

			seasons = [i for i in episodes if '<EpisodeNumber>1</EpisodeNumber>' in i]

			locals = [i for i in result2 if '<EpisodeNumber>' in i]

			result = '' ; result2 = ''

			if limit == '':
				episodes = []
			elif limit == '-1':
				seasons = []
			else:
				episodes = [i for i in episodes if '<SeasonNumber>%01d</SeasonNumber>' % int(limit) in i]
				seasons = []


			try: poster = client.parseDOM(item, 'poster')[0]
			except: poster = ''
			if not poster == '': poster = self.tvdb_image + poster
			else: poster = '0'
			poster = client.replaceHTMLCodes(poster)
			poster = poster.encode('utf-8')

			try: banner = client.parseDOM(item, 'banner')[0]
			except: banner = ''
			if not banner == '': banner = self.tvdb_image + banner
			else: banner = '0'
			banner = client.replaceHTMLCodes(banner)
			banner = banner.encode('utf-8')

			try: fanart = client.parseDOM(item, 'fanart')[0]
			except: fanart = ''
			if not fanart == '': fanart = self.tvdb_image + fanart
			else: fanart = '0'
			fanart = client.replaceHTMLCodes(fanart)
			fanart = fanart.encode('utf-8')

			if not poster == '0': pass
			elif not fanart == '0': poster = fanart
			elif not banner == '0': poster = banner

			if not banner == '0': pass
			elif not fanart == '0': banner = fanart
			elif not poster == '0': banner = poster

			try: status = client.parseDOM(item, 'Status')[0]
			except: status = ''
			if status == '': status = 'Ended'
			status = client.replaceHTMLCodes(status)
			status = status.encode('utf-8')

			try: studio = client.parseDOM(item, 'Network')[0]
			except: studio = ''
			if studio == '': studio = '0'
			studio = client.replaceHTMLCodes(studio)
			studio = studio.encode('utf-8')

			try: genre = client.parseDOM(item, 'Genre')[0]
			except: genre = ''
			genre = [x for x in genre.split('|') if not x == '']
			genre = ' / '.join(genre)
			if genre == '': genre = '0'
			genre = client.replaceHTMLCodes(genre)
			genre = genre.encode('utf-8')

			try: duration = client.parseDOM(item, 'Runtime')[0]
			except: duration = ''
			if duration == '': duration = '0'
			duration = client.replaceHTMLCodes(duration)
			duration = duration.encode('utf-8')

			try: rating = client.parseDOM(item, 'Rating')[0]
			except: rating = ''
			if rating == '': rating = '0'
			rating = client.replaceHTMLCodes(rating)
			rating = rating.encode('utf-8')

			try: votes = client.parseDOM(item, 'RatingCount')[0]
			except: votes = '0'
			if votes == '': votes = '0'
			votes = client.replaceHTMLCodes(votes)
			votes = votes.encode('utf-8')

			try: mpaa = client.parseDOM(item, 'ContentRating')[0]
			except: mpaa = ''
			if mpaa == '': mpaa = '0'
			mpaa = client.replaceHTMLCodes(mpaa)
			mpaa = mpaa.encode('utf-8')

			try: cast = client.parseDOM(item, 'Actors')[0]
			except: cast = ''
			cast = [x for x in cast.split('|') if not x == '']
			try: cast = [(x.encode('utf-8'), '') for x in cast]
			except: cast = []

			try: label = client.parseDOM(item2, 'SeriesName')[0]
			except: label = '0'
			label = client.replaceHTMLCodes(label)
			label = label.encode('utf-8')

			try: plot = client.parseDOM(item2, 'Overview')[0]
			except: plot = ''
			if plot == '': plot = '0'
			plot = client.replaceHTMLCodes(plot)
			plot = plot.encode('utf-8')
		except:
			pass


		for item in seasons:
			try:
				premiered = client.parseDOM(item, 'FirstAired')[0]
				if premiered == '' or '-00' in premiered: premiered = '0'
				premiered = client.replaceHTMLCodes(premiered)
				premiered = premiered.encode('utf-8')

				if status == 'Ended': pass
				elif premiered == '0': raise Exception()
				elif int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.today_date))): raise Exception()

				season = client.parseDOM(item, 'SeasonNumber')[0]
				season = '%01d' % int(season)
				season = season.encode('utf-8')

				thumb = [i for i in artwork if client.parseDOM(i, 'Season')[0] == season]
				try: thumb = client.parseDOM(thumb[0], 'BannerPath')[0]
				except: thumb = ''
				if not thumb == '': thumb = self.tvdb_image + thumb
				else: thumb = '0'
				thumb = client.replaceHTMLCodes(thumb)
				thumb = thumb.encode('utf-8')

				if thumb == '0': thumb = poster

				self.list.append({'season': season, 'tvshowtitle': tvshowtitle, 'label': label, 'year': year, 'premiered': premiered, 'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'cast': cast, 'plot': plot, 'imdb': imdb, 'tvdb': tvdb, 'poster': poster, 'banner': banner, 'fanart': fanart, 'thumb': thumb})
			except:
				pass


		for item in episodes:
			try:
				premiered = client.parseDOM(item, 'FirstAired')[0]
				if premiered == '' or '-00' in premiered: premiered = '0'
				premiered = client.replaceHTMLCodes(premiered)
				premiered = premiered.encode('utf-8')

				if status == 'Ended': pass
				elif premiered == '0': raise Exception()
				elif int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.today_date))): raise Exception()

				season = client.parseDOM(item, 'SeasonNumber')[0]
				season = '%01d' % int(season)
				season = season.encode('utf-8')

				episode = client.parseDOM(item, 'EpisodeNumber')[0]
				episode = re.sub('[^0-9]', '', '%01d' % int(episode))
				episode = episode.encode('utf-8')

				title = client.parseDOM(item, 'EpisodeName')[0]
				if title == '': title = '0'
				title = client.replaceHTMLCodes(title)
				title = title.encode('utf-8')

				try: thumb = client.parseDOM(item, 'filename')[0]
				except: thumb = ''
				if not thumb == '': thumb = self.tvdb_image + thumb
				else: thumb = '0'
				thumb = client.replaceHTMLCodes(thumb)
				thumb = thumb.encode('utf-8')

				if not thumb == '0': pass
				elif not fanart == '0': thumb = fanart.replace(self.tvdb_image, self.tvdb_poster)
				elif not poster == '0': thumb = poster

				try: rating = client.parseDOM(item, 'Rating')[0]
				except: rating = ''
				if rating == '': rating = '0'
				rating = client.replaceHTMLCodes(rating)
				rating = rating.encode('utf-8')

				try: director = client.parseDOM(item, 'Director')[0]
				except: director = ''
				director = [x for x in director.split('|') if not x == '']
				director = ' / '.join(director)
				if director == '': director = '0'
				director = client.replaceHTMLCodes(director)
				director = director.encode('utf-8')

				try: writer = client.parseDOM(item, 'Writer')[0]
				except: writer = ''
				writer = [x for x in writer.split('|') if not x == '']
				writer = ' / '.join(writer)
				if writer == '': writer = '0'
				writer = client.replaceHTMLCodes(writer)
				writer = writer.encode('utf-8')

				try:
					local = client.parseDOM(item, 'id')[0]
					local = [x for x in locals if '<id>%s</id>' % str(local) in x][0]
				except:
					local = item

				label = client.parseDOM(local, 'EpisodeName')[0]
				if label == '': label = '0'
				label = client.replaceHTMLCodes(label)
				label = label.encode('utf-8')

				try: episodeplot = client.parseDOM(local, 'Overview')[0]
				except: episodeplot = ''
				if episodeplot == '': episodeplot = '0'
				if episodeplot == '0': episodeplot = plot
				episodeplot = client.replaceHTMLCodes(episodeplot)
				try: episodeplot = episodeplot.encode('utf-8')
				except: pass

				self.list.append({'title': title, 'label': label, 'season': season, 'episode': episode, 'tvshowtitle': tvshowtitle, 'year': year, 'premiered': premiered, 'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': episodeplot, 'imdb': imdb, 'tvdb': tvdb, 'poster': poster, 'banner': banner, 'fanart': fanart, 'thumb': thumb})
			except:
				pass

		return self.list


	def seasonDirectory(self, items):
		if items == None or len(items) == 0: control.idle() ; sys.exit()

		sysaddon = sys.argv[0]

		syshandle = int(sys.argv[1])

		addonPoster, addonBanner = control.addonPoster(), control.addonBanner()

		addonFanart, settingFanart = control.addonFanart(), tools.Settings.getBoolean('interface.fanart')

		traktCredentials = trakt.getTraktCredentialsInfo()

		try: isOld = False ; control.item().getArt('type')
		except: isOld = True

		try: indicators = playcount.getSeasonIndicators(items[0]['imdb'])
		except: pass

		traktHas = trakt.getTraktIndicatorsInfo() == True
		watchedMenu = control.lang(32068).encode('utf-8') if traktHas else control.lang(32066).encode('utf-8')
		unwatchedMenu = control.lang(32069).encode('utf-8') if traktHas else control.lang(32067).encode('utf-8')

		unwatchedEnabled = tools.Settings.getBoolean('interface.tvshows.unwatched.enabled')
		unwatchedLimit = tools.Settings.getBoolean('interface.tvshows.unwatched.limit')

		queueMenu = control.lang(32065).encode('utf-8')

		traktManagerMenu = control.lang(32070).encode('utf-8')

		media = tools.Media()

		try: multi = [i['tvshowtitle'] for i in items]
		except: multi = []
		multi = len([x for y,x in enumerate(multi) if x not in multi[:y]])
		multi = True if multi > 1 else False

		for i in items:
			try:
				label = None
				try:
					label = media.title(tools.Media.TypeSeason, season = i['season'])
				except: pass
				if label == None:
					label = i['season']

				if multi == True and not label in i['tvshowtitle'] and not i['tvshowtitle'] in label:
					label = '%s - %s' % (i['tvshowtitle'], label)

				systitle = sysname = urllib.quote_plus(i['tvshowtitle'])

				imdb, tvdb, year, season = i['imdb'], i['tvdb'], i['year'], i['season']

				meta = dict((k,v) for k, v in i.iteritems() if not v == '0')
				meta.update({'mediatype': 'tvshow'})
				meta.update({'trailer': '%s?action=trailer&name=%s' % (sysaddon, sysname)})

				# Bubbles
				# Remove default time, since this might mislead users. Rather show no time.
				#if not 'duration' in i: meta.update({'duration': '60'})
				#elif i['duration'] == '0': meta.update({'duration': '60'})

				try: meta.update({'duration': str(int(meta['duration']) * 60)})
				except: pass
				try: meta.update({'genre': cleangenre.lang(meta['genre'], self.lang)})
				except: pass
				try: meta.update({'tvshowtitle': i['label']})
				except: pass
				try:
					# Year is the shows year, not the seasons year. Extract the correct year frpm the premier date.
					yearNew = i['premiered']
					yearNew = re.findall('(\d{4})', yearNew)[0]
					yearNew = yearNew.encode('utf-8')
					meta.update({'year': yearNew})
				except:
					pass

				try:
					if season in indicators:
						meta.update({'playcount': 1, 'overlay': 7})
						overlay = 7
					else:
						meta.update({'playcount': 0, 'overlay': 6})
						overlay = 6
				except:
					overlay = None


				url = self.parameterize('%s?action=episodes&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s&season=%s' % (sysaddon, systitle, year, imdb, tvdb, season))


				cm = []

				cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))

				if not traktHas:
					link = self.parameterize('%s?action=tvPlaycount&name=%s&imdb=%s&tvdb=%s&season=%s&query=7' % (sysaddon, systitle, imdb, tvdb, season))
					cm.append((watchedMenu, 'RunPlugin(%s)' % link))

					link = self.parameterize('%s?action=tvPlaycount&name=%s&imdb=%s&tvdb=%s&season=%s&query=6' % (sysaddon, systitle, imdb, tvdb, season))
					cm.append((unwatchedMenu, 'RunPlugin(%s)' % link))

				if traktCredentials == True:
					link = self.parameterize('%s?action=traktManager&tvdb=%s&season=%s' % (sysaddon, tvdb, season))
					cm.append((traktManagerMenu, 'RunPlugin(%s)' % link))

				if not self.kidsOnly() and control.setting('downloads.manual.enabled') == 'true':
					cm.append((control.lang(33585).encode('utf-8'), 'RunPlugin(%s?action=downloadsManager)' % (sysaddon)))

				if isOld == True:
					cm.append((control.lang2(19033).encode('utf-8'), 'Action(Info)'))


				item = control.item(label=label)

				if unwatchedEnabled and not overlay == None and not overlay == 7:
					try:
						count = playcount.getSeasonCount(imdb, season, unwatchedLimit)
						if count:
							item.setProperty('TotalEpisodes', str(count['total']))
							item.setProperty('WatchedEpisodes', str(count['watched']))
							item.setProperty('UnWatchedEpisodes', str(count['unwatched']))
					except:
						pass

				art = {}

				# First check thumbs, since they typically contains the seasons poster. The normal poster contains the show poster.
				poster = '0'
				if poster == '0' and 'poster3' in i: poster = i['thumb3']
				if poster == '0' and 'poster2' in i: poster = i['thumb2']
				if poster == '0' and 'poster' in i: poster = i['thumb']
				if poster == '0' and 'poster3' in i: poster = i['poster3']
				if poster == '0' and 'poster2' in i: poster = i['poster2']
				if poster == '0' and 'poster' in i: poster = i['poster']

				icon = '0'
				if icon == '0' and 'icon3' in i: icon = i['icon3']
				if icon == '0' and 'icon2' in i: icon = i['icon2']
				if icon == '0' and 'icon' in i: icon = i['icon']

				thumb = '0'
				if thumb == '0' and 'thumb3' in i: thumb = i['thumb3']
				if thumb == '0' and 'thumb2' in i: thumb = i['thumb2']
				if thumb == '0' and 'thumb' in i: thumb = i['thumb']

				banner = '0'
				if banner == '0' and 'banner3' in i: banner = i['banner3']
				if banner == '0' and 'banner2' in i: banner = i['banner2']
				if banner == '0' and 'banner' in i: banner = i['banner']

				fanart = '0'
				if settingFanart:
					if fanart == '0' and 'fanart3' in i: fanart = i['fanart3']
					if fanart == '0' and 'fanart2' in i: fanart = i['fanart2']
					if fanart == '0' and 'fanart' in i: fanart = i['fanart']

				clearlogo = '0'
				if clearlogo == '0' and 'clearlogo' in i: clearlogo = i['clearlogo']

				clearart = '0'
				if clearart == '0' and 'clearart' in i: clearart = i['clearart']

				if poster == '0': poster = addonPoster
				if icon == '0': icon = poster
				if thumb == '0': thumb = poster
				if banner == '0': banner = addonBanner
				if fanart == '0': fanart = addonFanart

				if not poster == '0' and not poster == None: art.update({'poster' : poster, 'tvshow.poster' : poster, 'season.poster' : poster})
				if not icon == '0' and not icon == None: art.update({'icon' : icon})
				if not thumb == '0' and not thumb == None: art.update({'thumb' : thumb})
				if not banner == '0' and not banner == None: art.update({'banner' : banner})
				if not clearlogo == '0' and not clearlogo == None: art.update({'clearlogo' : clearlogo})
				if not clearart == '0' and not clearart == None: art.update({'clearart' : clearart})
				if not fanart == '0' and not fanart == None: item.setProperty('Fanart_Image', fanart)

				item.setArt(art)
				item.addContextMenuItems(cm)
				item.setInfo(type='Video', infoLabels = meta)

				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				pass

		try: control.property(syshandle, 'showplot', items[0]['plot'])
		except: pass

		control.content(syshandle, 'seasons')
		control.directory(syshandle, cacheToDisc=True)
		views.setView('seasons', {'skin.estuary': 55, 'skin.confluence': 500})
