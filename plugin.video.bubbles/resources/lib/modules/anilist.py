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

import json, urlparse, urllib

from resources.lib.modules import cache
from resources.lib.modules import client
from resources.lib.modules import cleantitle


def _getAniList(url):
	try:
		url = urlparse.urljoin('https://anilist.co', '/api%s' % url)
		return client.request(url, headers={'Authorization': '%s %s' % cache.get(_getToken, 1), 'Content-Type': 'application/x-www-form-urlencoded'})
	except:
		pass


def _getToken():
	result = urllib.urlencode({'grant_type': 'client_credentials', 'client_id': 'bubblesaddon-ocdew', 'client_secret': 'e2B2Phu3PL4WzVL179'})
	result = client.request('https://anilist.co/api/auth/access_token', post=result, headers={'Content-Type': 'application/x-www-form-urlencoded'}, error=True)
	result = json.loads(result)
	return result['token_type'], result['access_token']


def getAlternativTitle(title):
	try:
		t = cleantitle.get(title)

		r = _getAniList('/anime/search/%s' % title)
		r = [(i.get('title_romaji'), i.get('synonyms', [])) for i in json.loads(r) if cleantitle.get(i.get('title_english', '')) == t]
		r = [i[1][0] if i[0] == title and len(i[1]) > 0 else i[0] for i in r]
		r = [i.encode('utf-8') for i in r if i if i != title][0]
		return r
	except:
		pass
