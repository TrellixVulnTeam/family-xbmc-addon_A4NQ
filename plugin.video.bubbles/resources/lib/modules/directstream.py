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


import re,os,urllib,urlparse,json,binascii
from resources.lib.modules import client



def google(url):
	try:
		netloc = urlparse.urlparse(url.strip().lower()).netloc
		netloc = netloc.split('.google')[0]

		if netloc == 'docs' or netloc == 'drive':
			url = url.split('/preview', 1)[0]
			url = url.replace('drive.google.com', 'docs.google.com')

		headers = {'User-Agent': client.agent()}

		result = client.request(url, output='extended', headers=headers)

		try: headers['Cookie'] = result[2]['Set-Cookie']
		except: pass

		result = result[0]


		if netloc == 'docs' or netloc == 'drive':
			result = re.compile('"fmt_stream_map",(".+?")').findall(result)[0]
			result = json.loads(result)
			result = [i.split('|')[-1] for i in result.split(',')]
			result = sum([googletag(i) for i in result], [])


		elif netloc == 'photos':
			result = result.replace('\r','').replace('\n','').replace('\t','')
			result = re.compile('"\d*/\d*x\d*.+?","(.+?)"').findall(result)[0]

			result = result.replace('\\u003d','=').replace('\\u0026','&')
			result = re.compile('url=(.+?)&').findall(result)
			result = [urllib.unquote(i) for i in result]

			result = [googletag(i)[0] for i in result]


		elif netloc == 'picasaweb':
			id = re.compile('#(\d*)').findall(url)[0]

			result = re.search('feedPreload:\s*(.*}]}})},', result, re.DOTALL).group(1)
			result = json.loads(result)['feed']['entry']

			if len(result) > 1: result = [i for i in result if str(id) in i['link'][0]['href']][0]
			elif len(result) == 1: result = result[0]

			result = result['media']['content']
			result = [i['url'] for i in result if 'video' in i['type']]
			result = sum([googletag(i) for i in result], [])


		elif netloc == 'plus':
			id = (urlparse.urlparse(url).path).split('/')[-1]

			result = result.replace('\r','').replace('\n','').replace('\t','')
			result = result.split('"%s"' % id)[-1].split(']]')[0]

			result = result.replace('\\u003d','=').replace('\\u0026','&')
			result = re.compile('url=(.+?)&').findall(result)
			result = [urllib.unquote(i) for i in result]

			result = [googletag(i)[0] for i in result]


		url = []
		try: url += [[i for i in result if i['quality'] == '1080p'][0]]
		except: pass
		try: url += [[i for i in result if i['quality'] == 'HD'][0]]
		except: pass
		try: url += [[i for i in result if i['quality'] == 'SD'][0]]
		except: pass

		for i in url: i.update({'url': i['url'] + '|%s' % urllib.urlencode(headers)})

		if url == []: return
		return url
	except:
		return


def googletag(url):
	quality = re.compile('itag=(\d*)').findall(url)
	quality += re.compile('=m(\d*)$').findall(url)
	try: quality = quality[0]
	except: return []

	if quality in ['37', '137', '299', '96', '248', '303', '46']:
		return [{'quality': '1080p', 'url': url}]
	elif quality in ['22', '84', '136', '298', '120', '95', '247', '302', '45', '102']:
		return [{'quality': 'HD', 'url': url}]
	elif quality in ['35', '44', '135', '244', '94']:
		return [{'quality': 'SD', 'url': url}]
	elif quality in ['18', '34', '43', '82', '100', '101', '134', '243', '93']:
		return [{'quality': 'SD', 'url': url}]
	elif quality in ['5', '6', '36', '83', '133', '242', '92', '132']:
		return [{'quality': 'SD', 'url': url}]
	else:
		return []


def googlepass(url):
	try:
		try: headers = dict(urlparse.parse_qsl(url.rsplit('|', 1)[1]))
		except: headers = None
		url = client.request(url.split('|')[0], headers=headers, output='geturl')
		if 'requiressl=yes' in url: url = url.replace('http://', 'https://')
		else: url = url.replace('https://', 'http://')
		if headers: url += '|%s' % urllib.urlencode(headers)
		return url
	except:
		return



def vk(url):
	try:
		query = urlparse.parse_qs(urlparse.urlparse(url).query)

		try: oid, video_id = query['oid'][0], query['id'][0]
		except: oid, video_id = re.findall('\/video(.*)_(.*)', url)[0]

		sources_url = 'http://vk.com/al_video.php?act=show_inline&al=1&video=%s_%s' % (oid, video_id)
		html = client.request(sources_url)
		html = re.sub(r'[^\x00-\x7F]+', ' ', html)

		sources = re.findall('(\d+)x\d+.+?(http.+?\.m3u8.+?)n', html)

		if not sources:
			sources = re.findall('"url(\d+)"\s*:\s*"(.+?)"', html)

		sources = [(i[0], i[1].replace('\\', '')) for i in sources]
		sources = dict(sources)

		url = []
		try: url += [{'quality': 'HD', 'url': sources['720']}]
		except: pass
		try: url += [{'quality': 'SD', 'url': sources['540']}]
		except: pass
		try: url += [{'quality': 'SD', 'url': sources['480']}]
		except: pass
		if not url == []: return url
		try: url += [{'quality': 'SD', 'url': sources['360']}]
		except: pass
		if not url == []: return url
		try: url += [{'quality': 'SD', 'url': sources['240']}]
		except: pass
		if not url == []: return url
	except:
		return



def odnoklassniki(url):
	try:
		url = re.compile('//.+?/.+?/([\w]+)').findall(url)[0]
		url = 'http://ok.ru/dk?cmd=videoPlayerMetadata&mid=%s' % url

		result = client.request(url)
		result = re.sub(r'[^\x00-\x7F]+',' ', result)

		result = json.loads(result)['videos']

		try: hd = [{'quality': '1080p', 'url': i['url']} for i in result if i['name'] == 'full']
		except: pass
		try: hd += [{'quality': 'HD', 'url': i['url']} for i in result if i['name'] == 'hd']
		except: pass
		try: sd = [{'quality': 'SD', 'url': i['url']} for i in result if i['name'] == 'sd']
		except: pass
		try: sd += [{'quality': 'SD', 'url': i['url']} for i in result if i['name'] == 'low']
		except: pass
		try: sd += [{'quality': 'SD', 'url': i['url']} for i in result if i['name'] == 'lowest']
		except: pass
		try: sd += [{'quality': 'SD', 'url': i['url']} for i in result if i['name'] == 'mobile']
		except: pass

		url = hd + sd[:1]
		if not url == []: return url

	except:
		return



def cldmailru(url):
	try:
		v = url.split('public')[-1]

		r = client.request(url)
		r = re.sub(r'[^\x00-\x7F]+',' ', r)

		tok = re.findall('"tokens"\s*:\s*{\s*"download"\s*:\s*"([^"]+)', r)[0]

		url = re.findall('"weblink_get"\s*:\s*\[.+?"url"\s*:\s*"([^"]+)', r)[0]

		url = '%s%s?key=%s' % (url, v, tok)

		return url
	except:
		return



def yandex(url):
	try:
		cookie = client.request(url, output='cookie')

		r = client.request(url, cookie=cookie)
		r = re.sub(r'[^\x00-\x7F]+',' ', r)

		sk = re.findall('"sk"\s*:\s*"([^"]+)', r)[0]

		idstring = re.findall('"id"\s*:\s*"([^"]+)', r)[0]

		idclient = binascii.b2a_hex(os.urandom(16))

		post = {'idClient': idclient, 'version': '3.9.2', 'sk': sk, '_model.0': 'do-get-resource-url', 'id.0': idstring}
		post = urllib.urlencode(post)

		r = client.request('https://yadi.sk/models/?_m=do-get-resource-url', post=post, cookie=cookie)
		r = json.loads(r)

		url = r['models'][0]['data']['file']

		return url
	except:
		return
