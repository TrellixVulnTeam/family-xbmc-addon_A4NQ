import xbmc
import re
import urllib
import json
import time
import operator

from resources.lib.externals.beautifulsoup import BeautifulSoup

from resources.lib.modules import client
from resources.lib.modules import workers
from resources.lib.extensions import interface
from resources.lib.extensions import tools
from resources.lib.extensions import debrid
from resources.lib.extensions import provider as providerx

# Verify account and provider access.

class Verification(object):

	# Keep order for sorting.
	StatusFailure = 0
	StatusLimited = 1
	StatusOperational = 2
	StatusDisabled = 3

	def __init__(self):
		self.mResults = []

	def verifyAccounts(self):
		type = 'accounts'
		try:
			progressDialog = interface.Dialog.progress(33018, title = 33018)
			progressDialog.update(0, self.__info(type, True))

			threads = self.__threads()
			[i.start() for i in threads]
			timeout = 30
			for i in range(0, timeout * 2):
				try:
					if xbmc.abortRequested == True: return sys.exit()
					try:
						if progressDialog.iscanceled(): break
						progressDialog.update(int((len([i for i in threads if i.is_alive() == False]) / float(len(threads))) * 50), self.__info(type, True))
					except:
						progressDialog.update(int((len([i for i in threads if i.is_alive() == False]) / float(len(threads))) * 50), self.__info(type, True))
					if all(i == False for i in [j.is_alive() for j in threads]): break
					time.sleep(0.5)
				except:
					pass

			# Run all thread a second & third time, because sometimes the request fails for some reason. Try a second time.
			# Do not run all threads at once, need some time inbetween the same requests.
			# Operational accounts are not checked again.

			threads = self.__threads()
			[i.start() for i in threads]
			timeout = 30
			for i in range(0, timeout * 2):
				try:
					if xbmc.abortRequested == True: return sys.exit()
					try:
						if progressDialog.iscanceled(): break
						progressDialog.update(int((len([i for i in threads if i.is_alive() == False]) / float(len(threads))) * 25) + 50, self.__info(type, True))
					except:
						progressDialog.update(int((len([i for i in threads if i.is_alive() == False]) / float(len(threads))) * 25) + 50, self.__info(type, True))
					if all(i == False for i in [j.is_alive() for j in threads]): break
					time.sleep(0.5)
				except:
					pass

			canceled = False
			threads = self.__threads()
			[i.start() for i in threads]
			timeout = 30
			for i in range(0, timeout * 2):
				try:
					if xbmc.abortRequested == True: return sys.exit()
					try:
						if progressDialog.iscanceled():
							canceled = True
							break
						progressDialog.update(int((len([i for i in threads if i.is_alive() == False]) / float(len(threads))) * 25) + 75, self.__info(type, True))
					except:
						progressDialog.update(int((len([i for i in threads if i.is_alive() == False]) / float(len(threads))) * 25) + 75, self.__info(type, True))
					if all(i == False for i in [j.is_alive() for j in threads]): break
					time.sleep(0.5)
				except:
					pass

			try: progressDialog.close()
			except: pass

			if not canceled:
				self.__showResults(type)
		except:
			tools.Logger.error()
			self.__showError(type)

	def verifyProviders(self):
		type = 'providers'
		try:
			from resources.lib.sources import sources

			progressDialog = interface.Dialog.progress(33019, title = 33019)
			progressDialog.update(0, self.__info(type, False))

			try: timeout = tools.Settings.getInteger('providers.timeout')
			except: timeout = 30

			# Add imdb for providers like YIFY who dependt on that.
			itemsMovies = [
				{'title' : 'Titanic', 'year' : '1997', 'imdb' : 'tt0120338'},
				{'title' : 'Avatar', 'year' : '2009', 'imdb' : 'tt0499549'},
				{'title' : 'Star Wars', 'year' : '1977', 'imdb' : 'tt0076759'},
				{'title' : 'Harry Potter', 'year' : '2001', 'imdb' : 'tt0241527'},
			]
			itemsShows = [
				{'tvshowtitle' : 'The Big Bang Theory', 'season' : '10', 'episode' : '1', 'imdb' : 'tt0898266'},
				{'tvshowtitle' : 'Game of Thrones', 'season' : '6', 'episode' : '10', 'imdb' : 'tt0944947'},
				{'tvshowtitle' : 'Rick and Morty', 'season' : '2', 'episode' : '10', 'imdb' : 'tt2861424'},
				{'tvshowtitle' : 'The Sopranos', 'season' : '6', 'episode' : '1', 'imdb' : 'tt0141842'}
			]

			sourcesObject = sources()
			sourcesObject.getConstants()
			hostDict = sourcesObject.hostDict
			hostprDict = sourcesObject.hostprDict

			providers = providerx.Provider.providers(enabled = False, local = False)
			threads = []

			for provider in providers:
				items = []
				if provider['group'] == providerx.Provider.GroupMovies:
					items = itemsMovies
				elif provider['group'] == providerx.Provider.GroupTvshows:
					items = itemsShows
				else:
					items = itemsMovies[:int(len(itemsMovies)/2)] + itemsShows[:int(len(itemsShows)/2)]
				threads.append(workers.Thread(self.__verifyProvider, provider, items, hostDict, hostprDict))

			canceled = False
			[i.start() for i in threads]
			for i in range(0, timeout * max(len(itemsMovies), len(itemsShows)) * 2):
				try:
					if xbmc.abortRequested == True: return sys.exit()
					if progressDialog.iscanceled():
						canceled = True
						break
					progressDialog.update(int((len([i for i in threads if i.is_alive() == False]) / float(len(threads))) * 100), self.__info(type, False))
					if all(i == False for i in [j.is_alive() for j in threads]): break
					time.sleep(0.5)
				except:
					pass

			# Providers still running.
			for i in range(len(threads)):
				if threads[i].is_alive():
					self.__append(providers[i]['name'], self.StatusFailure)

			try: progressDialog.close()
			except: pass

			if not canceled:
				self.__showResults(type)
		except:
			tools.Logger.error()
			self.__showError(type)

	def __verifyProvider(self, provider, items, hostDict, hostprDict):
		status = self.StatusFailure
		try:
			if provider['enabled']:
				object = provider['object']
				link = provider['link']
				if link:
					data = client.request(link, output = 'extended', error = True)
					success = data[0] and not data[0] == '' and (data[1].startswith('2') or data[1] == '403') # 403 for TorrentApi.
					if not success: # Just in case, try a second time.
						data = client.request(link, output = 'extended', error = True)
						success = data[0] and not data[0] == '' and (data[1].startswith('2') or data[1] == '403') # 403 for TorrentApi.
					if success:
						status = self.StatusLimited
						for item in items:
							linkProvider = urllib.urlencode(item)
							result = object.sources(linkProvider, hostDict, hostprDict)

							# In case the first domain fails, try the other ones in the domains list.
							if len(result) == 0 and tools.System.developers() and tools.Settings.getBoolean('scraping.mirrors.enabled'):
								checked = [link]
								for link in provider['links']:
									object.base_link = link
									result = object.sources(linkProvider, hostDict, hostprDict)
									if len(result) > 0:
										break

							if len(result) > 0:
								status = self.StatusOperational
								break
			else:
				status = self.StatusDisabled
		except:
			pass
		self.__append(provider['name'], status)

	def __info(self, type, inProgress, list = False):
		if inProgress:
			results = [i for i in self.mResults if not i['status'] == self.StatusFailure] # Because the second retry may solve this.
		else:
			results = self.mResults

		results = sorted(results, key=operator.itemgetter('status', 'name')) # Sort

		percentageOperational = 0
		percentageLimited = 0
		percentageFailure = 0
		percentageDisabled = 0
		if len(results) > 0:
			percentageFailure = int(round(len([i for i in results if i['status'] == self.StatusFailure]) / (len(results) / 100.0)))
			percentageLimited = int(round(len([i for i in results if i['status'] == self.StatusLimited]) / (len(results) / 100.0)))
			percentageDisabled = int(round(len([i for i in results if i['status'] == self.StatusDisabled]) / (len(results) / 100.0)))
			percentageOperational = 100 - percentageFailure - percentageLimited - percentageDisabled # Always calculate in case of rounding errors, must add up to 100.

		if list:
			list = []
			list.append(interface.Translation.string(33025) + ': ' + interface.Format.fontColor('%.0f%%' % percentageOperational, interface.Format.ColorExcellent))
			list.append(interface.Translation.string(33024) + ': ' + interface.Format.fontColor('%.0f%%' % percentageLimited, interface.Format.ColorMedium))
			list.append(interface.Translation.string(33023) + ': ' + interface.Format.fontColor('%.0f%%' % percentageFailure, interface.Format.ColorBad))
			list.append(interface.Translation.string(33022) + ': ' + interface.Format.fontColor('%.0f%%' % percentageDisabled, interface.Format.ColorUltra))
			list.append('')
			for result in results:
				list.append(result['name'] + ': ' + self.__color(result['status']))
			return list
		else:
			status = ''
			for result in results:
				status += interface.Format.fontNewline() + '     ' + result['name'] + ': ' + self.__color(result['status'])
			message = interface.Translation.string(33025) + ': ' + interface.Format.fontColor('%.0f%%' % percentageOperational, interface.Format.ColorExcellent)
			message += ', ' + interface.Translation.string(33024) + ': ' + interface.Format.fontColor('%.0f%%' % percentageLimited, interface.Format.ColorMedium)
			message += ', ' + interface.Translation.string(33023) + ': ' + interface.Format.fontColor('%.0f%%' % percentageFailure, interface.Format.ColorBad)
			message += ', ' + interface.Translation.string(33022) + ': ' + interface.Format.fontColor('%.0f%%' % percentageDisabled, interface.Format.ColorUltra)
			return message + status

	def __showResults(self, type):
		interface.Dialog.select(self.__info(type, False, list = True), title = 33020)

	def __showError(self, type):
		if type == 'accounts':
			message = interface.Translation.string(33026)
		elif type == 'providers':
			message = interface.Translation.string(33027)
		interface.Dialog.notification(message, icon = interface.Dialog.IconError, title = 33021)

	def __isUrl(self, url):
		return url.startswith('http://') or url.startswith('https://') or url.startswith('ftp://')

	def __threads(self):
		threads = []

		threads.append(workers.Thread(self._verifyAccountsFanart))

		threads.append(workers.Thread(self._verifyAccountsTrakt))
		threads.append(workers.Thread(self._verifyAccountsImdb))
		threads.append(workers.Thread(self._verifyAccountsTmdb))

		threads.append(workers.Thread(self._verifyAccountsPremiumize))
		threads.append(workers.Thread(self._verifyAccountsRealdebrid))
		threads.append(workers.Thread(self._verifyAccountsAlldebrid))
		threads.append(workers.Thread(self._verifyAccountsRapidPremium))
		threads.append(workers.Thread(self._verifyAccountsEasynews))

		threads.append(workers.Thread(self._verifyAccountsTorrentLeech))

		threads.append(workers.Thread(self._verifyAccountsNzbfinder))
		threads.append(workers.Thread(self._verifyAccountsUsenetcrawler))
		threads.append(workers.Thread(self._verifyAccountsNzbndx))
		threads.append(workers.Thread(self._verifyAccountsNzbgeek))

		threads.append(workers.Thread(self._verifyAccountsAlluc))

		threads.append(workers.Thread(self._verifyAccountsStreamlord))
		threads.append(workers.Thread(self._verifyAccountsMoviesplanet))
		threads.append(workers.Thread(self._verifyAccountsOroro))

		threads.append(workers.Thread(self._verifyAccountsSeriesever))

		threads.append(workers.Thread(self._verifyAccountsT411))

		return threads

	def __enabled(self, entry):
		return tools.Settings.getBoolean(entry)

	def __color(self, status):
		if status == self.StatusDisabled:
			return interface.Format.fontColor(interface.Translation.string(33022), interface.Format.ColorUltra)
		elif status == self.StatusFailure:
			return interface.Format.fontColor(interface.Translation.string(33023), interface.Format.ColorBad)
		elif status == self.StatusLimited:
			return interface.Format.fontColor(interface.Translation.string(33024), interface.Format.ColorMedium)
		elif status == self.StatusOperational:
			return interface.Format.fontColor(interface.Translation.string(33025), interface.Format.ColorExcellent)

	def __append(self, name, status):
		if any(i['name'] == name for i in self.mResults):
			for i in range(0, len(self.mResults)):
				if self.mResults[i]['name'] == name:
					if self.mResults[i]['status'] == self.StatusFailure:
						self.mResults[i]['status'] = status
					break
		else:
			self.mResults.append({'name' : name, 'status' : status})
		return status

	def __done(self, name):
		for result in self.mResults:
			if result['name'] == name and not result['status'] == self.StatusFailure:
				return True
		return False

	# NB: Only one _ in front of the function name, if two __, cannot be called settings.py
	def _verifyAccountsFanart(self, checkDisabled = True, key = None):
		name = 'Fanart'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.artwork.fanart.enabled'):
				if key == None: key = tools.Settings.getString('accounts.artwork.fanart.api')
				# Seems like FanartTv currently does not check the client key at all. Do some manual validation.
				if re.match('^[a-fA-F0-9]{32}$', key): # 32 character hash.
					link = 'http://webservice.fanart.tv/v3/movies/tt0076759?api_key=%s&client_key=%s' % ('NzY0YTY1MWJmZmE5YmM3OTRlNzY1OTkzZmY0ZGRkMjI='.decode('base64'), key)
					data = client.request(link)
					if data:
						data = json.loads(data)
						if 'name' in data:
							status = self.StatusOperational
						else:
							status = self.StatusFailure
					else:
						status = self.StatusFailure
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsTrakt(self, checkDisabled = True):
		name = 'Trakt'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.informants.trakt.enabled'):
				from resources.lib.modules import trakt
				data = trakt.verify()
				if data:
					status = self.StatusOperational
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsImdb(self, checkDisabled = True):
		name = 'IMDb'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.informants.imdb.enabled'):
				link = 'http://www.imdb.com/user/ur%s/watchlist' % tools.Settings.getString('accounts.informants.imdb.user').replace('ur', '')
				data = client.request(link)
				if data:
					indexStart = data.find('IMDbReactInitialState.push(') # Somtimes the page is not fully rendered yet and the JSON is still in a JS tag.
					if indexStart < 0: # Data was rendered into the HTML.
						data = BeautifulSoup(data)
						if len(data.find_all('div', class_ = 'error_code_404')) > 0:
							status = self.StatusFailure
						elif len(data.find_all('div', id = 'unavailable')) > 0:
							status = self.StatusLimited
						elif len(data.find_all('div', class_ = 'lister-widget')) > 0:
							status = self.StatusOperational
						else:
							status = self.StatusFailure
					else: # Data still in JS.
						indexStart += 27
						indexEnd = data.find(');', indexStart)
						data = json.loads(data[indexStart : indexEnd])
						if 'titles' in data and len(data['titles'].values()) > 0:
							status = self.StatusOperational
						else:
							status = self.StatusLimited
				else: # Wrong user ID, returns 404 error.
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsTmdb(self, checkDisabled = True):
		name = 'TMDb'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.informants.tmdb.enabled'):
				link = 'http://api.themoviedb.org/3/movie/tt0076759?api_key=%s' % tools.Settings.getString('accounts.informants.tmdb.api')
				data = client.request(link)
				if data:
					data = json.loads(data)
					if 'title' in data:
						status = self.StatusOperational
					else:
						status = self.StatusFailure
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsPremiumize(self, checkDisabled = True):
		name = 'Premiumize'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.debrid.premiumize.enabled'):
				old = debrid.Premiumize().accountVerifyOld()
				new = debrid.Premiumize().accountVerifyNew()
				if old and new:
					status = self.StatusOperational
				elif not old and not new:
					status = self.StatusFailure
				else:
					status = self.StatusLimited
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsRealdebrid(self, checkDisabled = True):
		name = 'RealDebrid'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.debrid.realdebrid.enabled'):
				if debrid.RealDebrid().accountVerify():
					status = self.StatusOperational
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsAlldebrid(self, checkDisabled = True):
		name = 'AllDebrid'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.debrid.alldebrid.enabled'):
				data = {'action': 'login', 'login_login': tools.Settings.getString('accounts.debrid.alldebrid.user'), 'login_password': tools.Settings.getString('accounts.debrid.alldebrid.pass')}
				link = 'http://alldebrid.com/register/?%s' % urllib.urlencode(data)
				data = client.request(link)
				if 'control panel' in data.lower():
					status = self.StatusOperational
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsRapidPremium(self, checkDisabled = True):
		name = 'RapidPremium'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.debrid.rapidpremium.enabled'):
				data = {'username': tools.Settings.getString('accounts.debrid.rapidpremium.user'), 'password': tools.Settings.getString('accounts.debrid.rapidpremium.api'), 'action': 'generate'}
				link = 'http://premium.rpnet.biz/client_api.php?%s' % urllib.urlencode(data)
				data = client.request(link)
				if data:
					data = json.loads(data)
					if 'error' in data and not data['error'][0] == 'Missing required parameter: links':
						status = self.StatusFailure
					else:
						status = self.StatusOperational
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsEasynews(self, checkDisabled = True):
		name = 'EasyNews'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.debrid.easynews.enabled'):
				if debrid.EasyNews().accountVerify():
					status = self.StatusOperational
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsTorrentLeech(self, checkDisabled = True):
		name = 'TorrentLeech'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.providers.torrentleech.enabled'):
				link = 'https://www.torrentleech.org/user/account/login/'
				data = urllib.urlencode({'username': tools.Settings.getString('accounts.providers.torrentleech.user'), 'password': tools.Settings.getString('accounts.providers.torrentleech.pass'), 'submit': 'submit'})
				cookie = client.request(link, post = data, output = 'cookie')
				if cookie and not cookie == '' and 'member_id' in cookie.lower():
					status = self.StatusOperational
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsNzbfinder(self, checkDisabled = True):
		name = 'NZBFinder'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.providers.nzbfinder.enabled'):
				link = 'https://nzbfinder.ws/api?o=json&t=movie&imdbid=0076759&apikey=%s' % tools.Settings.getString('accounts.providers.nzbfinder.api')
				data = client.request(link)
				if data:
					data = json.loads(data)
					if data and 'title' in data: # If an error, nzbfinder returns XML instead of JSON.
						status = self.StatusOperational
					else:
						status = self.StatusFailure
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsUsenetcrawler(self, checkDisabled = True):
		name = 'UsenetCrawler'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.providers.usenetcrawler.enabled'):
				link = 'https://www.usenet-crawler.com/login'
				data = urllib.urlencode({'username': tools.Settings.getString('accounts.providers.usenetcrawler.user'), 'password': tools.Settings.getString('accounts.providers.usenetcrawler.pass'), 'rememberme' : 'on', 'submit': 'Login'}) # Must have rememberme, otherwise cannot login (UsenetCrawler bug).
				cookie = client.request(link, post = data, output = 'cookie', close = False)
				if cookie and not cookie == '':
					result = client.request(link, post = data, cookie = cookie)
					if 'logout' in result.lower():
						status = self.StatusOperational
					else:
						status = self.StatusFailure
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			tools.Logger.error()
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsNzbndx(self, checkDisabled = True):
		name = 'NZBndx'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.providers.nzbndx.enabled'):
				link = 'https://www.nzbndx.com/login'
				headers = {'X-Requested-With': 'XMLHttpRequest'}
				data = urllib.urlencode({'username': tools.Settings.getString('accounts.providers.nzbndx.user'), 'password': tools.Settings.getString('accounts.providers.nzbndx.pass'), 'submit' : 'Login'})
				cookie = client.request(link, post = data, output = 'cookie', close = False)
				if cookie and not cookie == '' and 'phpsessid' in cookie.lower():
					# If success or failure, in both cases a session ID is returned. So check the returned HTML.
					result = client.request(link, post = data, cookie = cookie)
					if 'incorrect username or password' in result.lower():
						status = self.StatusFailure
					else:
						status = self.StatusOperational
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			tools.Logger.error()
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsNzbgeek(self, checkDisabled = True):
		name = 'NZBgeek'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.providers.nzbgeek.enabled'):
				link = 'https://api.nzbgeek.info/api?o=json&apikey=%s' % tools.Settings.getString('accounts.providers.nzbgeek.api')
				data = client.request(link)
				if not data == None and not data == '' and 'invalid api key' in data.lower():
					status = self.StatusFailure
				else:
					status = self.StatusOperational
			else:
				status = self.StatusDisabled
		except:
			tools.Logger.error()
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsAlluc(self, checkDisabled = True):
		name = 'Alluc'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.providers.alluc.enabled'):
				link = 'https://www.alluc.ee/api/search/download/?apikey=%s&query=dummy&count=1' % tools.Settings.getString('accounts.providers.alluc.api')
				result = client.request(link)
				result = json.loads(result)
				if 'status' in result and result['status'] == 'success':
					status = self.StatusOperational
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsStreamlord(self, checkDisabled = True):
		name = 'StreamLord'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.providers.streamlord.enabled'):
				link = 'http://www.streamlord.com/login.html'
				data = urllib.urlencode({'username': tools.Settings.getString('accounts.providers.streamlord.user'), 'password': tools.Settings.getString('accounts.providers.streamlord.pass'), 'submit': 'Login'})
				cookie = client.request(link, post = data, output = 'cookie')
				if cookie and not cookie == '':
					status = self.StatusOperational
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsMoviesplanet(self, checkDisabled = True):
		name = 'MoviesPlanet'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.providers.moviesplanet.enabled'):
				link = 'http://www.moviesplanet.is/login' # Do not use https, gives an internal server error.
				headers = {'X-Requested-With': 'XMLHttpRequest'}
				data = urllib.urlencode({'username': tools.Settings.getString('accounts.providers.moviesplanet.user'), 'password': tools.Settings.getString('accounts.providers.moviesplanet.pass'), 'action': 'login'})
				cookie = client.request(link, post = data, headers = headers, output = 'cookie')
				if cookie and not cookie == '':
					if 'guid' in cookie.lower():
						status = self.StatusOperational
					else:
						status = self.StatusLimited # Seems the MoviePlanet authentication does not work anymore and there is no way to get it working.
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsOroro(self, checkDisabled = True):
		name = 'Ororo'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.providers.ororo.enabled'):
				import base64
				link = 'https://ororo.tv/en/users/settings'
				headers = {'Authorization': 'Basic %s' % base64.b64encode('%s:%s' % (tools.Settings.getString('accounts.providers.ororo.user'), tools.Settings.getString('accounts.providers.ororo.pass'))), 'User-Agent': 'Bubbles for Kodi'}
				data = client.request(link, headers = headers)
				if data and tools.Settings.getString('accounts.providers.ororo.user') in data:
					status = self.StatusOperational
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsSeriesever(self, checkDisabled = True):
		name = 'SeriesEver'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.providers.seriesever.enabled'):
				link = 'http://seriesever.net/service/login'
				headers = {'X-Requested-With': 'XMLHttpRequest'}
				data = urllib.urlencode({'username': tools.Settings.getString('accounts.providers.seriesever.user'), 'password': tools.Settings.getString('accounts.providers.seriesever.pass')})
				cookie = client.request(link, post = data, headers = headers, output = 'cookie')
				cookie = str(cookie).lower()
				if cookie and not cookie == '' and 'ci_session' in cookie and 'username' in cookie:
					status = self.StatusOperational
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			status = self.StatusFailure
		return self.__append(name, status)

	def _verifyAccountsT411(self, checkDisabled = True):
		name = 'T411'
		if self.__done(name): return
		try:
			if not checkDisabled or self.__enabled('accounts.providers.t411.enabled'):
				link = 'https://api.t411.al/auth'
				data = urllib.urlencode({'username': tools.Settings.getString('accounts.providers.t411.user'), 'password': tools.Settings.getString('accounts.providers.t411.pass')})
				result = client.request(link, post = data)
				result = json.loads(result)
				if 'token' in result and not result['token'] == None and not result['token'] == '':
					status = self.StatusOperational
				else:
					status = self.StatusFailure
			else:
				status = self.StatusDisabled
		except:
			tools.Logger.error()
			status = self.StatusFailure
		return self.__append(name, status)
