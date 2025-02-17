# -*- coding: utf-8 -*-

'''
    Exodus Add-on
    Copyright (C) 2016 lambda

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


import os,sys,re,json,urllib,urlparse,base64,datetime
import unicodedata
try: action = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))['action']
except: action = None

from resources.lib.modules import trakt
from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import cache
from resources.lib.modules import metacache
from resources.lib.modules import playcount
from resources.lib.modules import workers
from resources.lib.modules import views
from resources.lib.modules import favourites


class movies:
    def __init__(self):
        self.list = []

        self.tmdb_link = 'http://api.themoviedb.org'
        self.trakt_link = 'http://api-v2launch.trakt.tv'
        self.imdb_link = 'http://www.imdb.com'
		
        self.tmdb_key = control.setting('tmdb_apikey')
        if self.tmdb_key == '' or self.tmdb_key == None: self.tmdb_key = base64.b64decode('ZjdmNTE3NzU4NzdlMGJiNjcwMzUyMDk1MmIzYzc4NDA=')
		
        
        self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))
        self.systime = (self.datetime).strftime('%Y%m%d%H%M%S%f')
        self.trakt_user = re.sub('[^a-z0-9]', '-', control.setting('trakt.user').strip().lower())
        self.imdb_user = control.setting('imdb.user').replace('ur', '')
        self.tmdb_lang = 'en'
        self.today_date = (self.datetime).strftime('%Y-%m-%d')
        self.month_date = (self.datetime - datetime.timedelta(days = 30)).strftime('%Y-%m-%d')
        self.year_date = (self.datetime - datetime.timedelta(days = 365)).strftime('%Y-%m-%d')
        self.tmdb_info_link = 'http://api.themoviedb.org/3/movie/%s?api_key=%s&language=%s&append_to_response=credits,releases,external_ids' % ('%s', self.tmdb_key, self.tmdb_lang)
        self.imdb_by_query = 'http://www.omdbapi.com/?t=%s&y=%s'
        self.imdbinfo = 'http://www.omdbapi.com/?i=%s&plot=short&r=json'
        self.tmdbmovielist1_link = control.setting('tmdb.movielist_id1')		
        self.tmdbmovielist2_link = control.setting('tmdb.movielist_id2')		
        self.tmdbmovielist3_link = control.setting('tmdb.movielist_id3')		
        self.tmdbmovielist4_link = control.setting('tmdb.movielist_id4')		
        self.tmdbmovielist5_link = control.setting('tmdb.movielist_id5')		
        self.tmdbmovielist6_link = control.setting('tmdb.movielist_id6')		
        self.tmdbmovielist7_link = control.setting('tmdb.movielist_id7')		
        self.tmdbmovielist8_link = control.setting('tmdb.movielist_id8')		
        self.tmdbmovielist9_link = control.setting('tmdb.movielist_id9')		
        self.tmdbmovielist10_link = control.setting('tmdb.movielist_id10')		
		
        self.tmdb_image = 'http://image.tmdb.org/t/p/original'
        self.tmdb_poster = 'http://image.tmdb.org/t/p/w500'

		
		
        self.persons_link = 'http://api.themoviedb.org/3/search/person?&api_key=%s&query=%s&include_adult=false&page=1' % (self.tmdb_key, '%s')
        self.personlist_link = 'http://api.themoviedb.org/3/person/popular?&api_key=%s&page=%s' % (self.tmdb_key, '%s')
        self.genres_link = 'http://api.themoviedb.org/3/genre/movie/list?api_key=%s&language=%s' % (self.tmdb_key, self.tmdb_lang)
        self.certifications_link = 'http://api.themoviedb.org/3/certification/movie/list?&api_key=%s' % self.tmdb_key
        self.popular2_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie&languages=en&num_votes=1000,&production_status=released&groups=top_1000&sort=moviemeter,asc&count=40&start=1'
        self.search_link = 'http://api.themoviedb.org/3/search/movie?&api_key=%s&query=%s'
        self.popular_link = 'http://api.themoviedb.org/3/movie/popular?api_key=%s&page=1'
        self.views_link = 'http://api.themoviedb.org/3/movie/top_rated?&language=it&api_key=%s&page=1'
        self.featured_link = 'http://api.themoviedb.org/3/discover/movie?api_key=%s&primary_release_date.gte=date[365]&primary_release_date.lte=date[60]&page=1'
        self.person_link = 'http://api.themoviedb.org/3/discover/movie?api_key=%s&with_people=%s&primary_release_date.lte=date[0]&sort_by=primary_release_date.desc&page=1'
        self.genre_link = 'http://api.themoviedb.org/3/discover/movie?api_key=%s&with_genres=%s&primary_release_date.gte=date[365]&primary_release_date.lte=date[0]&page=1'
        self.certification_link = 'http://api.themoviedb.org/3/discover/movie?&api_key=%s&certification=%s&certification_country=US&primary_release_date.lte=date[0]&page=1'
        self.year_link = 'http://api.themoviedb.org/3/discover/movie?&api_key=%s&year=%s&primary_release_date.lte=date[0]&page=1'
        self.theaters_link = 'http://api.themoviedb.org/3/movie/now_playing?api_key=%s&page=1'
        self.boxoffice_link = 'http://www.imdb.com/search/title?&title_type=feature,tv_movie&sort=boxoffice_gross_us,desc&count=40&start=1'
        self.oscars_link = 'http://www.imdb.com/search/title?title_type=feature,tv_movie&groups=oscar_best_picture_winners&sort=year,desc&count=40&start=1'
        self.trending_link = 'http://api-v2launch.trakt.tv/movies/trending?&limit=40&page=1'
        self.premiere_link = 'http://api.themoviedb.org/3/discover/movie?api_key=%s&first_air_date.gte=%s&first_air_date.lte=%s&page=1' % ('%s', self.year_date, self.today_date)

        self.tmdbmarvel_link = 'http://api.themoviedb.org/3/list/11332?api_key=%s' % (self.tmdb_key)
        self.tmdboscars_link = 'http://api.themoviedb.org/3/list/11334?api_key=%s' % (self.tmdb_key)
        self.tmdbdisney_link = 'http://api.themoviedb.org/3/list/11338?api_key=%s' % (self.tmdb_key)
        self.tmdbxmas_link = 'http://api.themoviedb.org/3/list/12944?api_key=%s' % (self.tmdb_key)

		
        self.mycustomlist1_link = 'http://api.themoviedb.org/3/list/%s?api_key=%s' % (self.tmdbmovielist1_link, self.tmdb_key)
        self.mycustomlist2_link = 'http://api.themoviedb.org/3/list/%s?api_key=%s' % (self.tmdbmovielist2_link, self.tmdb_key)
        self.mycustomlist3_link = 'http://api.themoviedb.org/3/list/%s?api_key=%s' % (self.tmdbmovielist3_link, self.tmdb_key)
        self.mycustomlist4_link = 'http://api.themoviedb.org/3/list/%s?api_key=%s' % (self.tmdbmovielist4_link, self.tmdb_key)
        self.mycustomlist5_link = 'http://api.themoviedb.org/3/list/%s?api_key=%s' % (self.tmdbmovielist5_link, self.tmdb_key)
        self.mycustomlist6_link = 'http://api.themoviedb.org/3/list/%s?api_key=%s' % (self.tmdbmovielist6_link, self.tmdb_key)
        self.mycustomlist7_link = 'http://api.themoviedb.org/3/list/%s?api_key=%s' % (self.tmdbmovielist7_link, self.tmdb_key)
        self.mycustomlist8_link = 'http://api.themoviedb.org/3/list/%s?api_key=%s' % (self.tmdbmovielist8_link, self.tmdb_key)
        self.mycustomlist9_link = 'http://api.themoviedb.org/3/list/%s?api_key=%s' % (self.tmdbmovielist9_link, self.tmdb_key)
        self.mycustomlist10_link = 'http://api.themoviedb.org/3/list/%s?api_key=%s' % (self.tmdbmovielist10_link, self.tmdb_key)
		
		
        # self.traktlists_link = 'http://api-v2launch.trakt.tv/users/%s/lists' % self.trakt_user
        # self.traktlikedlists_link = 'http://api-v2launch.trakt.tv/users/likes/lists?limit=1000000'
        # self.traktlist_link = 'http://api-v2launch.trakt.tv/users/%s/lists/%s/items'
        # self.traktcollection_link = 'http://api-v2launch.trakt.tv/users/%s/collection/movies' % self.trakt_user
        # self.traktwatchlist_link = 'http://api-v2launch.trakt.tv/users/%s/watchlist/movies' % self.trakt_user
        # self.traktfeatured_link = 'http://api-v2launch.trakt.tv/recommendations/movies?limit=40'
        # self.trakthistory_link = 'http://api-v2launch.trakt.tv/users/%s/history/movies?limit=40&page=1' % self.trakt_user
        # self.imdblists_link = 'http://www.imdb.com/user/ur%s/lists?tab=all&sort=modified:desc&filter=titles' % self.imdb_user
        # self.imdblist_link = 'http://www.imdb.com/list/%s/?view=detail&sort=title:asc&title_type=feature,short,tv_movie,tv_special,video,documentary,game&start=1'
        # self.imdbwatchlist_link = 'http://www.imdb.com/user/ur%s/watchlist' % self.imdb_user


    def get(self, url, idx=True):
        try:
            try: url = getattr(self, url + '_link')
            except: pass

            try: u = urlparse.urlparse(url).netloc.lower()
            except: pass


            if u in self.tmdb_link and ('/user/' in url or '/list/' in url):
                self.list = self.tmdb_custom_list(url)
               
                self.worker()

            elif u in self.tmdb_link and not ('/user/' in url or '/list/' in url):
                self.list = cache.get(self.tmdb_list, 24, url)
                print ("LISTS TMDB", self.list)
                self.worker()
				
            elif u in self.trakt_link and '/users/' in url:
                try:
                    if url == self.trakthistory_link: raise Exception()
                    if not '/%s/' % self.trakt_user in url: raise Exception()
                    if trakt.getActivity() > cache.timeout(self.trakt_list, url): raise Exception()
                    self.list = cache.get(self.trakt_list, 720, url)
                except:
                    self.list = cache.get(self.trakt_list, 0, url)

                if '/%s/' % self.trakt_user in url:
                    self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a )', '', k['title'].lower()))

                if idx == True: self.worker()

            elif u in self.trakt_link:
                self.list = cache.get(self.trakt_list, 24, url)
                if idx == True: self.worker()


            elif u in self.imdb_link and ('/user/' in url or '/list/' in url):
                self.list = cache.get(self.imdb_list, 0, url)
                if idx == True: self.worker()

            elif u in self.imdb_link:
                self.list = cache.get(self.imdb_list, 24, url)
                if idx == True: self.worker()


            if idx == True: self.movieDirectory(self.list)
            return self.list
        except:
            pass


    def widget(self):
        setting = control.setting('movie.widget')
        if setting == '1':
            self.get(self.premiere_link)
        if setting == '2':
            self.get(self.trending_link)
        elif setting == '3':
            self.get(self.popular_link)
        elif setting == '4':
            self.get(self.theaters_link)
        elif setting == '5':
            self.get(self.views_link)
        else:
            self.get(self.featured_link)


    def search(self, query=None):
        try:
            if not control.infoLabel('ListItem.Title') == '':
                self.query = control.window.getProperty('%s.movie.search' % control.addonInfo('id'))

            elif query == None:
                t = control.lang(30201).encode('utf-8')
                k = control.keyboard('', t) ; k.doModal()
                self.query = k.getText() if k.isConfirmed() else None

            else:
                self.query = query

            if (self.query == None or self.query == ''): return

            control.window.setProperty('%s.movie.search' % control.addonInfo('id'), self.query)

            url = self.search_link % ('%s', urllib.quote_plus(self.query))
            self.list = cache.get(self.tmdb_list, 0, url)

            self.worker()
            self.movieDirectory(self.list)
            return self.list
        except:
            return


    def person(self, query=None):
        try:
            if query == None:
                t = control.lang(30201).encode('utf-8')
                k = control.keyboard('', t) ; k.doModal()
                self.query = k.getText() if k.isConfirmed() else None
            else:
                self.query = query

            if (self.query == None or self.query == ''): return

            url = self.persons_link % urllib.quote_plus(self.query)
            self.list = cache.get(self.tmdb_person_list, 0, url)

            for i in range(0, len(self.list)): self.list[i].update({'action': 'movies'})
            self.addDirectory(self.list)
            return self.list
        except:
            return


    def genres(self):
        try:
            url = self.genres_link
            url = re.sub('language=(fi|hr|no)', '', url)
            self.list = cache.get(self.tmdb_genre_list, 24, url)

            for i in range(0, len(self.list)): self.list[i].update({'image': 'genres.png', 'action': 'movies'})
            self.addDirectory(self.list)
            return self.list
        except:
            return


    def certifications(self):
        try:
            url = self.certifications_link
            self.list = cache.get(self.tmdb_certification_list, 24, url)

            for i in range(0, len(self.list)): self.list[i].update({'image': 'certificates.png', 'action': 'movies'})
            self.addDirectory(self.list)
            return self.list
        except:
            return


    def years(self):
        year = (self.datetime.strftime('%Y'))

        for i in range(int(year)-0, int(year)-50, -1): self.list.append({'name': str(i), 'url': self.year_link % ('%s', str(i)), 'image': 'years.png', 'action': 'movies'})
        self.addDirectory(self.list)
        return self.list


    def persons(self):
        personlists = []

        for i in range(1, 5):
            try:
                self.list = []
                personlists += cache.get(self.tmdb_person_list, 24, self.personlist_link % str(i))
            except:
                pass

        self.list = personlists
        for i in range(0, len(self.list)): self.list[i].update({'action': 'movies'})
        self.addDirectory(self.list)
        return self.list


    def userlists(self):
        try:
            userlists = []
            if trakt.getTraktCredentialsInfo() == False: raise Exception()
            activity = trakt.getActivity()
        except:
            pass

        try:
            if trakt.getTraktCredentialsInfo() == False: raise Exception()
            try:
                if activity > cache.timeout(self.trakt_user_list, self.traktlists_link): raise Exception()
                userlists += cache.get(self.trakt_user_list, 720, self.traktlists_link)
            except:
                userlists += cache.get(self.trakt_user_list, 0, self.traktlists_link)
        except:
            pass
        try:
            self.list = []
            if self.imdb_user == '': raise Exception()
            userlists += cache.get(self.imdb_user_list, 0, self.imdblists_link)
        except:
            pass
        try:
            self.list = []
            if trakt.getTraktCredentialsInfo() == False: raise Exception()
            try:
                if activity > cache.timeout(self.trakt_user_list, self.traktlikedlists_link): raise Exception()
                userlists += cache.get(self.trakt_user_list, 720, self.traktlikedlists_link)
            except:
                userlists += cache.get(self.trakt_user_list, 0, self.traktlikedlists_link)
        except:
            pass

        self.list = userlists
        for i in range(0, len(self.list)): self.list[i].update({'image': 'userlists.png', 'action': 'movies'})
        self.addDirectory(self.list, queue=True)
        return self.list


    def tmdb_list(self, url):
        next = url
        for i in re.findall('date\[(\d+)\]', url):
            url = url.replace('date[%s]' % i, (self.datetime - datetime.timedelta(days = int(i))).strftime('%Y-%m-%d'))

        try:
            result = client.request(url % self.tmdb_key)
            result = json.loads(result)
            items = result['results']
        except:
            return
        try:
            page = int(result['page'])
            total = int(result['total_pages'])
            if page >= total: raise Exception()
            url2 = '%s&page=%s' % (url.split('&page=', 1)[0], str(page+1))
            result = client.request(url2 % self.tmdb_key)
            result = json.loads(result)
            items += result['results']
        except:
            pass

        try:
            page = int(result['page'])
            total = int(result['total_pages'])
            if page >= total: raise Exception()
            if not 'page=' in url: raise Exception()
            next = '%s&page=%s' % (next.split('&page=', 1)[0], str(page+1))
            next = next.encode('utf-8')
        except:
            next = ''

        for item in items:
            try:
                title = item['title']
                # title = str(title)
                # title = re.sub(r'\ -',r'', title)
                # title =re.sub('+', ' ', title)
                # title =re.sub(':','', title)
                title = item['title']
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                year = item['release_date']
                year = re.compile('(\d{4})').findall(year)[-1]
                year = year.encode('utf-8')

                tmdb = item['id']
                tmdb = re.sub('[^0-9]', '', str(tmdb))
                tmdb = tmdb.encode('utf-8')

                poster = item['poster_path']
                if poster == '' or poster == None: raise Exception()
                else: poster = '%s%s' % (self.tmdb_poster, poster)
                poster = poster.encode('utf-8')

                fanart = item['backdrop_path']
                if fanart == '' or fanart == None: fanart = '0'
                if not fanart == '0': fanart = '%s%s' % (self.tmdb_image, fanart)
                fanart = fanart.encode('utf-8')

                premiered = item['release_date']
                try: premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
                except: premiered = '0'
                premiered = premiered.encode('utf-8')

                rating = str(item['vote_average'])
                if rating == '' or rating == None: rating = '0'
                rating = rating.encode('utf-8')

                votes = str(item['vote_count'])
                try: votes = str(format(int(votes),',d'))
                except: pass
                if votes == '' or votes == None: votes = '0'
                votes = votes.encode('utf-8')

                plot = item['overview']
                if plot == '' or plot == None: plot = '0'
                plot = client.replaceHTMLCodes(plot)
                plot = plot.encode('utf-8')

                tagline = re.compile('[.!?][\s]{1,2}(?=[A-Z])').split(plot)[0]
                try: tagline = tagline.encode('utf-8')
                except: pass

                self.list.append({'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'studio': '0', 'genre': '0', 'duration': '0', 'rating': rating, 'votes': votes, 'mpaa': '0', 'director': '0', 'writer': '0', 'cast': '0', 'plot': plot, 'tagline': tagline, 'code': '0', 'imdb': '0', 'tmdb': tmdb, 'tvdb': '0', 'poster': poster, 'banner': '0', 'fanart': fanart, 'next': next})
            except:
                pass

        return self.list


    def tmdb_custom_list(self, url):
        # print ("GENESIS REBORN LISTS", url)
        try:
            result = client.request(url)
            result = json.loads(result)
            items = result['items']
            # print ("GENESIS REBORN LISTS", items)
        except:
            return

        next = ''
        for item in items:
            try:
                title = item['title']
                # title = str(title)
                # title = re.sub(r'\ -',r'', title)
                # title =re.sub('+', ' ', title)
                # title =re.sub(':','', title)
                title = item['title']
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')
                # print ("GENESIS REBORN LISTS", title)

                year = item['release_date']
                year = re.compile('(\d{4})').findall(year)[-1]
                year = year.encode('utf-8')
                # print ("GENESIS REBORN LISTS", year)
                tmdb = item['id']
                tmdb = re.sub('[^0-9]', '', str(tmdb))
                tmdb = tmdb.encode('utf-8')
                # print ("GENESIS REBORN LISTS", tmdb)

                poster = item['poster_path']
                if poster == '' or poster == None: raise Exception()
                else: poster = '%s%s' % (self.tmdb_poster, poster)
                poster = poster.encode('utf-8')
                # print ("GENESIS REBORN LISTS", poster)

                fanart = item['backdrop_path']
                if fanart == '' or fanart == None: fanart = '0'
                if not fanart == '0': fanart = '%s%s' % (self.tmdb_image, fanart)
                fanart = fanart.encode('utf-8')
                # print ("GENESIS REBORN LISTS", fanart)

                premiered = item['release_date']
                try: premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
                except: premiered = '0'
                premiered = premiered.encode('utf-8')
                # print ("GENESIS REBORN LISTS", premiered)

                rating = str(item['vote_average'])
                if rating == '' or rating == None: rating = '0'
                rating = rating.encode('utf-8')
                # print ("GENESIS REBORN LISTS", rating)

                votes = str(item['vote_count'])
                try: votes = str(format(int(votes),',d'))
                except: pass
                if votes == '' or votes == None: votes = '0'
                votes = votes.encode('utf-8')
                # print ("GENESIS REBORN LISTS", votes)

                plot = item['overview']
                if plot == '' or plot == None: plot = '0'
                plot = client.replaceHTMLCodes(plot)
                plot = plot.encode('utf-8')
                # print ("GENESIS REBORN LISTS", plot)

                tagline = re.compile('[.!?][\s]{1,2}(?=[A-Z])').split(plot)[0]
                try: tagline = tagline.encode('utf-8')
                except: pass
                # print ("GENESIS REBORN LISTS", tagline)

                self.list.append({'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'studio': '0', 'genre': '0', 'duration': '0', 'rating': rating, 'votes': votes, 'mpaa': '0', 'director': '0', 'writer': '0', 'cast': '0', 'plot': plot, 'tagline': tagline, 'code': '0', 'imdb': '0', 'tmdb': tmdb, 'tvdb': '0', 'poster': poster, 'banner': '0', 'fanart': fanart, 'next': next})
            except:
                pass

        return self.list


		
		
    def in_progress(self):
        try:
            items = favourites.getProgress('movies')
            self.list = [i[1] for i in items]

            for i in self.list:
                if not 'name' in i: i['name'] = '%s (%s)' % (i['title'], i['year'])
                try: i['title'] = i['title'].encode('utf-8')
                except: pass
                try: i['name'] = i['name'].encode('utf-8')
                except: pass
                if not 'duration' in i: i['duration'] = '0'
                if not 'imdb' in i: i['imdb'] = '0'
                if not 'tmdb' in i: i['tmdb'] = '0'
                if not 'tvdb' in i: i['tvdb'] = '0'
                if not 'tvrage' in i: i['tvrage'] = '0'
                if not 'poster' in i: i['poster'] = '0'
                if not 'banner' in i: i['banner'] = '0'
                if not 'fanart' in i: i['fanart'] = '0'
				

            self.worker()
            
            self.movieDirectory(self.list)
        except:
            return
			
		
    def favourites(self):
        try:
            items = favourites.getFavourites('movies')
            self.list = [i[1] for i in items]

            for i in self.list:
                if not 'name' in i: i['name'] = '%s (%s)' % (i['title'], i['year'])
                try: i['title'] = i['title'].encode('utf-8')
                except: pass
                try: i['name'] = i['name'].encode('utf-8')
                except: pass
                if not 'duration' in i: i['duration'] = '0'
                if not 'imdb' in i: i['imdb'] = '0'
                if not 'tmdb' in i: i['tmdb'] = '0'
                if not 'tvdb' in i: i['tvdb'] = '0'
                if not 'tvrage' in i: i['tvrage'] = '0'
                if not 'poster' in i: i['poster'] = '0'
                if not 'banner' in i: i['banner'] = '0'
                if not 'fanart' in i: i['fanart'] = '0'
				

            self.worker()
            self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a )', '', k['title'].lower()))	            
            self.movieDirectory(self.list)
        except:
            return

    def tmdb_person_list(self, url):
        try:
            result = client.request(url)
            result = json.loads(result)
            items = result['results']
        except:
            return

        for item in items:
            try:
                name = item['name']
                name = name.encode('utf-8')

                url = self.person_link % ('%s', item['id'])
                url = url.encode('utf-8')

                image = '%s%s' % (self.tmdb_image, item['profile_path'])
                image = image.encode('utf-8')

                self.list.append({'name': name, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def tmdb_genre_list(self, url):
        try:
            result = client.request(url)
            result = json.loads(result)
            items = result['genres']
        except:
            return

        for item in items:
            try:
                name = item['name']
                name = name.encode('utf-8')

                url = self.genre_link % ('%s', item['id'])
                url = url.encode('utf-8')

                self.list.append({'name': name, 'url': url})
            except:
                pass

        return self.list


    def tmdb_certification_list(self, url):
        try:
            result = client.request(url)
            result = json.loads(result)
            items = result['certifications']['US']
        except:
            return

        for item in items:
            try:
                name = item['certification']
                name = name.encode('utf-8')

                url = self.certification_link % ('%s', item['certification'])
                url = url.encode('utf-8')

                self.list.append({'name': name, 'url': url})
            except:
                pass

        return self.list


    def trakt_list(self, url):
        try:
            q = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
            q.update({'extended': 'full,images'})
            q = (urllib.urlencode(q)).replace('%2C', ',')
            u = url.replace('?' + urlparse.urlparse(url).query, '') + '?' + q

            result = trakt.getTrakt(u)
            result = json.loads(result)

            items = []
            for i in result:
                try: items.append(i['movie'])
                except: pass
            if len(items) == 0:
                items = result
        except:
            return

        try:
            q = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
            p = str(int(q['page']) + 1)
            if p == '5': raise Exception()
            q.update({'page': p})
            q = (urllib.urlencode(q)).replace('%2C', ',')
            next = url.replace('?' + urlparse.urlparse(url).query, '') + '?' + q
            next = next.encode('utf-8')
        except:
            next = ''

        for item in items:
            try:
                title = item['title']
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                year = item['year']
                year = re.sub('[^0-9]', '', str(year))
                year = year.encode('utf-8')

                if int(year) > int((self.datetime).strftime('%Y')): raise Exception()

                tmdb = item['ids']['tmdb']
                if tmdb == None or tmdb == '': tmdb = '0'
                tmdb = re.sub('[^0-9]', '', str(tmdb))
                tmdb = tmdb.encode('utf-8')

                imdb = item['ids']['imdb']
                if imdb == None or imdb == '': raise Exception()
                imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))
                imdb = imdb.encode('utf-8')

                poster = '0'
                try: poster = item['images']['poster']['medium']
                except: pass
                if poster == None or not '/posters/' in poster: poster = '0'
                poster = poster.rsplit('?', 1)[0]
                poster = poster.encode('utf-8')

                banner = poster
                try: banner = item['images']['banner']['full']
                except: pass
                if banner == None or not '/banners/' in banner: banner = '0'
                banner = banner.rsplit('?', 1)[0]
                banner = banner.encode('utf-8')

                fanart = '0'
                try: fanart = item['images']['fanart']['full']
                except: pass
                if fanart == None or not '/fanarts/' in fanart: fanart = '0'
                fanart = fanart.rsplit('?', 1)[0]
                fanart = fanart.encode('utf-8')

                premiered = item['released']
                try: premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
                except: premiered = '0'
                premiered = premiered.encode('utf-8')

                genre = item['genres']
                genre = [i.title() for i in genre]
                if genre == []: genre = '0'
                genre = ' / '.join(genre)
                genre = genre.encode('utf-8')

                try: duration = str(item['runtime'])
                except: duration = '0'
                if duration == None: duration = '0'
                duration = duration.encode('utf-8')

                try: rating = str(item['rating'])
                except: rating = '0'
                if rating == None or rating == '0.0': rating = '0'
                rating = rating.encode('utf-8')

                try: votes = str(item['votes'])
                except: votes = '0'
                try: votes = str(format(int(votes),',d'))
                except: pass
                if votes == None: votes = '0'
                votes = votes.encode('utf-8')

                mpaa = item['certification']
                if mpaa == None: mpaa = '0'
                mpaa = mpaa.encode('utf-8')

                plot = item['overview']
                if plot == None: plot = '0'
                plot = client.replaceHTMLCodes(plot)
                plot = plot.encode('utf-8')

                try: tagline = item['tagline']
                except: tagline = None
                if tagline == None and not plot == '0': tagline = re.compile('[.!?][\s]{1,2}(?=[A-Z])').split(plot)[0]
                elif tagline == None: tagline = '0'
                tagline = client.replaceHTMLCodes(tagline)
                try: tagline = tagline.encode('utf-8')
                except: pass

                self.list.append({'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'studio': '0', 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': '0', 'writer': '0', 'cast': '0', 'plot': plot, 'tagline': tagline, 'code': imdb, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': poster, 'banner': banner, 'fanart': fanart, 'next': next})
            except:
                pass

        return self.list


    def trakt_user_list(self, url):
        try:
            result = trakt.getTrakt(url)
            items = json.loads(result)
        except:
            pass

        for item in items:
            try:
                try: item = item['list']
                except: pass

                name = item['name']
                name = client.replaceHTMLCodes(name)
                name = name.encode('utf-8')

                url = self.traktlist_link % (item['user']['username'].strip(), item['ids']['slug'])
                url = url.encode('utf-8')

                self.list.append({'name': name, 'url': url, 'context': url})
            except:
                pass

        self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a )', '', k['name'].lower()))
        return self.list


    def imdb_list(self, url):
        try:
            if url == self.imdbwatchlist_link:
                def imdb_watchlist_id(url):
                    return re.findall('/export[?]list_id=(ls\d*)', client.request(url))[0]
                url = cache.get(imdb_watchlist_id, 8640, url)
                url = self.imdblist_link % url

            result = client.request(url)

            result = result.replace('\n','')
            result = result.decode('iso-8859-1').encode('utf-8')

            items = client.parseDOM(result, 'tr', attrs = {'class': '.+?'})
            items += client.parseDOM(result, 'div', attrs = {'class': 'list_item.+?'})
        except:
            return

        try:
            next = client.parseDOM(result, 'span', attrs = {'class': 'pagination'})
            next += client.parseDOM(result, 'div', attrs = {'class': 'pagination'})
            name = client.parseDOM(next[-1], 'a')[-1]
            if 'laquo' in name: raise Exception()
            next = client.parseDOM(next, 'a', ret='href')[-1]
            next = url.replace(urlparse.urlparse(url).query, urlparse.urlparse(next).query)
            next = client.replaceHTMLCodes(next)
            next = next.encode('utf-8')
        except:
            next = ''

        for item in items:
            try:
                try: title = client.parseDOM(item, 'a')[1]
                except: pass
                try: title = client.parseDOM(item, 'a', attrs = {'onclick': '.+?'})[-1]
                except: pass
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                year = client.parseDOM(item, 'span', attrs = {'class': 'year_type'})[0]
                year = re.compile('(\d{4})').findall(year)[-1]
                year = year.encode('utf-8')

                if int(year) > int((self.datetime).strftime('%Y')): raise Exception()

                imdb = client.parseDOM(item, 'a', ret='href')[0]
                imdb = 'tt' + re.sub('[^0-9]', '', imdb.rsplit('tt', 1)[-1])
                imdb = imdb.encode('utf-8')

                poster = '0'
                try: poster = client.parseDOM(item, 'img', ret='src')[0]
                except: pass
                try: poster = client.parseDOM(item, 'img', ret='loadlate')[0]
                except: pass
                if not ('_SX' in poster or '_SY' in poster): poster = '0'
                poster = re.sub('_SX\d*|_SY\d*|_CR\d+?,\d+?,\d+?,\d*','_SX500', poster)
                poster = client.replaceHTMLCodes(poster)
                poster = poster.encode('utf-8')

                genre = client.parseDOM(item, 'span', attrs = {'class': 'genre'})
                genre = client.parseDOM(genre, 'a')
                genre = ' / '.join(genre)
                if genre == '': genre = '0'
                genre = client.replaceHTMLCodes(genre)
                genre = genre.encode('utf-8')

                try: duration = re.compile('(\d+?) mins').findall(item)[-1]
                except: duration = '0'
                duration = client.replaceHTMLCodes(duration)
                duration = duration.encode('utf-8')

                try: rating = client.parseDOM(item, 'span', attrs = {'class': 'rating-rating'})[0]
                except: rating = '0'
                try: rating = client.parseDOM(rating, 'span', attrs = {'class': 'value'})[0]
                except: rating = '0'
                if rating == '' or rating == '-': rating = '0'
                rating = client.replaceHTMLCodes(rating)
                rating = rating.encode('utf-8')

                try: votes = client.parseDOM(item, 'div', ret='title', attrs = {'class': 'rating rating-list'})[0]
                except: votes = '0'
                try: votes = re.compile('[(](.+?) votes[)]').findall(votes)[0]
                except: votes = '0'
                if votes == '': votes = '0'
                votes = client.replaceHTMLCodes(votes)
                votes = votes.encode('utf-8')

                try: mpaa = client.parseDOM(item, 'span', attrs = {'class': 'certificate'})[0]
                except: mpaa = '0'
                try: mpaa = client.parseDOM(mpaa, 'span', ret='title')[0]
                except: mpaa = '0'
                if mpaa == '' or mpaa == 'NOT_RATED': mpaa = '0'
                mpaa = mpaa.replace('_', '-')
                mpaa = client.replaceHTMLCodes(mpaa)
                mpaa = mpaa.encode('utf-8')

                director = client.parseDOM(item, 'span', attrs = {'class': 'credit'})
                director += client.parseDOM(item, 'div', attrs = {'class': 'secondary'})
                try: director = [i for i in director if 'Director:' in i or 'Dir:' in i][0]
                except: director = '0'
                director = director.split('With:', 1)[0].strip()
                director = client.parseDOM(director, 'a')
                director = ' / '.join(director)
                if director == '': director = '0'
                director = client.replaceHTMLCodes(director)
                director = director.encode('utf-8')

                cast = client.parseDOM(item, 'span', attrs = {'class': 'credit'})
                cast += client.parseDOM(item, 'div', attrs = {'class': 'secondary'})
                try: cast = [i for i in cast if 'With:' in i or 'Stars:' in i][0]
                except: cast = '0'
                cast = cast.split('With:', 1)[-1].strip()
                cast = client.replaceHTMLCodes(cast)
                cast = cast.encode('utf-8')
                cast = client.parseDOM(cast, 'a')
                if cast == []: cast = '0'

                plot = '0'
                try: plot = client.parseDOM(item, 'span', attrs = {'class': 'outline'})[0]
                except: pass
                try: plot = client.parseDOM(item, 'div', attrs = {'class': 'item_description'})[0]
                except: pass
                plot = plot.rsplit('<span>', 1)[0].strip()
                if plot == '': plot = '0'
                plot = client.replaceHTMLCodes(plot)
                plot = plot.encode('utf-8')

                tagline = re.compile('[.!?][\s]{1,2}(?=[A-Z])').split(plot)[0]
                try: tagline = tagline.encode('utf-8')
                except: pass

                self.list.append({'title': title, 'originaltitle': title, 'year': year, 'premiered': '0', 'studio': '0', 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': '0', 'cast': cast, 'plot': plot, 'tagline': tagline, 'code': imdb, 'imdb': imdb, 'tmdb': '0', 'tvdb': '0', 'poster': poster, 'banner': '0', 'fanart': '0', 'next': next})
            except:
                pass

        return self.list


    def imdb_user_list(self, url):
        try:
            result = client.request(url)
            result = result.decode('iso-8859-1').encode('utf-8')
            items = client.parseDOM(result, 'div', attrs = {'class': 'list_name'})
        except:
            pass

        for item in items:
            try:
                name = client.parseDOM(item, 'a')[0]
                name = client.replaceHTMLCodes(name)
                name = name.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = url.split('/list/', 1)[-1].replace('/', '')
                url = self.imdblist_link % url
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                self.list.append({'name': name, 'url': url, 'context': url})
            except:
                pass

        self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a )', '', k['name'].lower()))
        return self.list


    def worker(self):
        self.meta = []
        total = len(self.list)

        for i in range(0, total): self.list[i].update({'metacache': False})
        self.list = metacache.fetch(self.list, self.tmdb_lang)

        for r in range(0, total, 100):
            threads = []
            for i in range(r, r+100):
                if i <= total: threads.append(workers.Thread(self.super_info, i))
            [i.start() for i in threads]
            [i.join() for i in threads]

        self.list = [i for i in self.list]

        if len(self.meta) > 0: metacache.insert(self.meta)

    def super_info(self, i):
        try:
            if self.list[i]['metacache'] == True: raise Exception()
            print ("SUPERINFO INITIALIZED")

            try: tmdb = self.list[i]['tmdb']
            except: tmdb = '0'

            if not tmdb == '0': url = self.tmdb_info_link % tmdb
            
            else: raise Exception()

            item = client.request(url, timeout='10')
            item = json.loads(item)

            title = item['title']
            if not title == '0': self.list[i].update({'title': title})

            year = item['release_date']
            try: year = re.compile('(\d{4})').findall(year)[0]
            except: year = '0'
            if year == '' or year == None: year = '0'
            year = year.encode('utf-8')
            if not year == '0': self.list[i].update({'year': year})

            tmdb = item['id']
            if tmdb == '' or tmdb == None: tmdb = '0'
            tmdb = re.sub('[^0-9]', '', str(tmdb))
            tmdb = tmdb.encode('utf-8')
            if not tmdb == '0': self.list[i].update({'tmdb': tmdb})

            imdb = item['imdb_id']
            if imdb == '' or imdb == None: imdb = '0'
            imdb = imdb.encode('utf-8')
            if not imdb == '0' and "tt" in imdb: self.list[i].update({'imdb': imdb, 'code': imdb})

            poster = item['poster_path']
            if poster == '' or poster == None: poster = '0'
            if not poster == '0': poster = '%s%s' % (self.tmdb_poster, poster)
            poster = poster.encode('utf-8')
            if not poster == '0': self.list[i].update({'poster': poster})

            fanart = item['backdrop_path']
            if fanart == '' or fanart == None: fanart = '0'
            if not fanart == '0': fanart = '%s%s' % (self.tmdb_image, fanart)
            fanart = fanart.encode('utf-8')
            if not fanart == '0' and self.list[i]['fanart'] == '0': self.list[i].update({'fanart': fanart})

            premiered = item['release_date']
            try: premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
            except: premiered = '0'
            if premiered == '' or premiered == None: premiered = '0'
            premiered = premiered.encode('utf-8')
            if not premiered == '0': self.list[i].update({'premiered': premiered})

            studio = item['production_companies']
            try: studio = [x['name'] for x in studio][0]
            except: studio = '0'
            if studio == '' or studio == None: studio = '0'
            studio = studio.encode('utf-8')
            if not studio == '0': self.list[i].update({'studio': studio})

            genre = item['genres']
            try: genre = [x['name'] for x in genre]
            except: genre = '0'
            if genre == '' or genre == None or genre == []: genre = '0'
            genre = ' / '.join(genre)
            genre = genre.encode('utf-8')
            if not genre == '0': self.list[i].update({'genre': genre})

            try: duration = str(item['runtime'])
            except: duration = '0'
            if duration == '' or duration == None: duration = '0'
            duration = duration.encode('utf-8')
            if not duration == '0': self.list[i].update({'duration': duration})

            rating = str(item['vote_average'])
            if rating == '' or rating == None: rating = '0'
            rating = rating.encode('utf-8')
            if not rating == '0': self.list[i].update({'rating': rating})

            votes = str(item['vote_count'])
            try: votes = str(format(int(votes),',d'))
            except: pass
            if votes == '' or votes == None: votes = '0'
            votes = votes.encode('utf-8')
            if not votes == '0': self.list[i].update({'votes': votes})

            mpaa = item['releases']['countries']
            try: mpaa = [x for x in mpaa if not x['certification'] == '']
            except: mpaa = '0'
            try: mpaa = ([x for x in mpaa if x['iso_3166_1'].encode('utf-8') == 'US'] + [x for x in mpaa if not x['iso_3166_1'].encode('utf-8') == 'US'])[0]['certification']
            except: mpaa = '0'
            mpaa = mpaa.encode('utf-8')
            if not mpaa == '0': self.list[i].update({'mpaa': mpaa})

            director = item['credits']['crew']
            try: director = [x['name'] for x in director if x['job'].encode('utf-8') == 'Director']
            except: director = '0'
            if director == '' or director == None or director == []: director = '0'
            director = ' / '.join(director)
            director = director.encode('utf-8')
            if not director == '0': self.list[i].update({'director': director})

            writer = item['credits']['crew']
            try: writer = [x['name'] for x in writer if x['job'].encode('utf-8') in ['Writer', 'Screenplay']]
            except: writer = '0'
            try: writer = [x for n,x in enumerate(writer) if x not in writer[:n]]
            except: writer = '0'
            if writer == '' or writer == None or writer == []: writer = '0'
            writer = ' / '.join(writer)
            writer = writer.encode('utf-8')
            if not writer == '0': self.list[i].update({'writer': writer})

            cast = item['credits']['cast']
            try: cast = [(x['name'].encode('utf-8'), x['character'].encode('utf-8')) for x in cast]
            except: cast = []
            if len(cast) > 0: self.list[i].update({'cast': cast})

            plot = item['overview']
            if plot == '' or plot == None: plot = '0'
            plot = plot.encode('utf-8')
            if not plot == '0': self.list[i].update({'plot': plot})

            tagline = item['tagline']
            if (tagline == '' or tagline == None) and not plot == '0': tagline = re.compile('[.!?][\s]{1,2}(?=[A-Z])').split(plot)[0]
            elif tagline == '' or tagline == None: tagline = '0'
            try: tagline = tagline.encode('utf-8')
            except: pass
            if not tagline == '0': self.list[i].update({'tagline': tagline})

			############# IMDB INFOS #################	
            try:
				if not imdb == None or imdb == '0':
					url = self.imdbinfo % imdb
					
					item = client.request(url, timeout='10')
					item = json.loads(item)
				
					plot2 = item['Plot']
					if plot2 == '' or plot2 == None: plot = plot
					plot = plot.encode('utf-8')
					if not plot == '0': self.list[i].update({'plot': plot})
					

					rating2 = str(item['imdbRating'])
					if rating2 == '' or rating2 == None: rating = rating2
					rating = rating.encode('utf-8')
					if not rating == '0': self.list[i].update({'rating': rating})

					votes2 = str(item['imdbVotes'])
					try: votes2 = str(votes2)
					except: pass
					if votes2 == '' or votes2 == None: votes = votes2
					votes = votes.encode('utf-8')
					if not votes == '0': self.list[i].update({'votes': votes2})
            except:
				pass
            self.meta.append({'tmdb': tmdb, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.tmdb_lang, 'item': {'title': title, 'year': year, 'code': imdb, 'imdb': imdb, 'tmdb': tmdb, 'poster': poster, 'fanart': fanart, 'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': plot, 'tagline': tagline}})
        except:
            pass


    def movieDirectory(self, items):
        if items == None or len(items) == 0: control.idle() ; sys.exit()

        sysaddon = sys.argv[0]

        syshandle = int(sys.argv[1])

        addonPoster, addonBanner = control.addonPoster(), control.addonBanner()

        addonFanart, settingFanart = control.addonFanart(), control.setting('fanart')

        traktCredentials = trakt.getTraktCredentialsInfo()

        try: isOld = False ; control.item().getArt('type')
        except: isOld = True

        isEstuary = True if 'estuary' in control.skin else False

        isPlayable = 'true' if not 'plugin' in control.infoLabel('Container.PluginName') else 'false'

        indicators = playcount.getMovieIndicators()

        playbackMenu = control.lang(32063).encode('utf-8') if control.setting('hosts.mode') == '2' else control.lang(32064).encode('utf-8')

        # watchedMenu = control.lang(32068).encode('utf-8') if trakt.getTraktIndicatorsInfo() == True else control.lang(32066).encode('utf-8')

        # unwatchedMenu = control.lang(32069).encode('utf-8') if trakt.getTraktIndicatorsInfo() == True else control.lang(32067).encode('utf-8')

        watchedMenu = control.lang(32066).encode('utf-8')

        unwatchedMenu = control.lang(32067).encode('utf-8')
		
        queueMenu = control.lang(32065).encode('utf-8')

        traktManagerMenu = control.lang(32070).encode('utf-8')

        nextMenu = control.lang(32053).encode('utf-8')


        for i in items:
            try:
                if not 'originaltitle' in i: i['originaltitle'] = '%s' %(i['title'])
                label = '%s' % (i['title'])
                tmdb, imdb, title, year = i['tmdb'], i['imdb'], i['originaltitle'], i['year']

                sysname = urllib.quote_plus('%s (%s)' % (title, year))
                systitle = urllib.quote_plus(title)


                poster, banner, fanart = i['poster'], i['banner'], i['fanart']
                if banner == '0' and not fanart == '0': banner = fanart
                elif banner == '0' and not poster == '0': banner = poster
                if poster == '0': poster = addonPoster
                if banner == '0': banner = addonBanner


                meta = dict((k,v) for k, v in i.iteritems() if not v == '0')
                meta.update({'mediatype': 'movie'})
                meta.update({'trailer': '%s?action=trailer&name=%s' % (sysaddon, sysname)})
                
                if i['duration'] == '0': meta.update({'duration': '120'})
                try: meta.update({'duration': str(int(meta['duration']) * 60)})
                except: pass
                try: meta.update({'genre': cleangenre.lang(meta['genre'], self.lang)})
                except: pass
                if isEstuary == True:
                    try: del meta['cast']
                    except: pass
                if "tt" in imdb: sysmetalliq = "plugin://plugin.video.metalliq/movies/add_to_library_parsed/imdb/%s/direct.genesisreborn.q" % imdb
                elif not tmdb == "0" or tmdb == None: sysmetalliq = "plugin://plugin.video.metalliq/movies/add_to_library_parsed/tmdb/%s/direct.genesisreborn.q" % tmdb
                else: sysmetalliq = "0"
                sysmeta = urllib.quote_plus(json.dumps(meta))
                
                url_alt = '%s?action=play_alter&title=%s&year=%s&imdb=%s&meta=%s&t=%s' % (sysaddon, systitle, year, imdb, sysmeta, self.systime)

                url = '%s?action=play&title=%s&year=%s&imdb=%s&meta=%s&t=%s' % (sysaddon, systitle, year, imdb, sysmeta, self.systime)
                sysurl = urllib.quote_plus(url)

                path = '%s?action=play&title=%s&year=%s&imdb=%s' % (sysaddon, systitle, year, imdb)


                cm = []

                # cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))
                cm.append(('Genesis Reborn Trailer', 'RunPlugin(%s?action=trailer&name=%s)' % (sysaddon, sysname)))
                cm.append((playbackMenu, 'RunPlugin(%s?action=alterSources&url=%s&meta=%s)' % (sysaddon, urllib.quote_plus(url_alt), sysmeta)))
                if not action == 'movieFavourites':cm.append(('Add to Watchlist', 'RunPlugin(%s?action=addFavourite&meta=%s&content=movies)' % (sysaddon, sysmeta)))
                if action == 'movieFavourites': cm.append(('Remove From Watchlist', 'RunPlugin(%s?action=deleteFavourite&meta=%s&content=movies)' % (sysaddon, sysmeta)))
                if action == 'movieProgress': cm.append(('Remove From Progress', 'RunPlugin(%s?action=deleteProgress&meta=%s&content=movies)' % (sysaddon, sysmeta)))
                if not sysmetalliq == '0' or sysmetalliq == None:cm.append(('Add To Library', 'RunPlugin(%s)' % (sysmetalliq)))
		
				
                try:
                    overlay = int(playcount.getMovieOverlay(indicators, imdb))
                    if overlay == 7:
                        #cm.append((unwatchedMenu, 'RunPlugin(%s?action=moviePlaycount&imdb=%s&query=6)' % (sysaddon, imdb)))
                        meta.update({'playcount': 1, 'overlay': 7})
                    else:
                        #cm.append((watchedMenu, 'RunPlugin(%s?action=moviePlaycount&imdb=%s&query=7)' % (sysaddon, imdb)))
                        meta.update({'playcount': 0, 'overlay': 6})
                except:
                    pass

                # if traktCredentials == True:
                    # cm.append((traktManagerMenu, 'RunPlugin(%s?action=traktManager&name=%s&imdb=%s&content=movie)' % (sysaddon, sysname, imdb)))


                if isOld == True:
                    cm.append((control.lang2(19033).encode('utf-8'), 'Action(Info)'))

                item = control.item(label=label)

                item.setArt({'icon': poster, 'thumb': poster, 'poster': poster, 'banner': banner})

                if settingFanart == 'true' and not fanart == '0':
                    item.setProperty('Fanart_Image', fanart)
                elif not addonFanart == None:
                    item.setProperty('Fanart_Image', addonFanart)

                item.addContextMenuItems(cm)
                item.setProperty('IsPlayable', isPlayable)
                item.setInfo(type='Video', infoLabels = meta)

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)
            except:
                pass

        try:
            url = items[0]['next']
            if url == '': raise Exception()

            icon = control.addonNext()
            url = '%s?action=moviePage&url=%s' % (sysaddon, urllib.quote_plus(url))

            item = control.item(label=nextMenu)

            item.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'banner': icon})
            if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
        except:
            pass


        control.content(syshandle, 'movies')
        # control.do_block_check(False)
        control.directory(syshandle, cacheToDisc=True)
        views.setView('movies', {'skin.confluence': 500})



    def addDirectory(self, items, queue=False):
        if items == None or len(items) == 0: return

        sysaddon = sys.argv[0]
        isPlayable = False if control.setting('autoplay') == 'false' and control.setting('hosts.mode') == '1' else True
        addonFanart, addonThumb, artPath = control.addonFanart(), control.addonThumb(), control.artPath()

        for i in items:
            try:
                try: name = control.lang(i['name']).encode('utf-8')
                except: name = i['name']

                if i['image'].startswith('http://'): thumb = i['image']
                elif not artPath == None: thumb = os.path.join(artPath, i['image'])
                else: thumb = addonThumb

                url = '%s?action=%s' % (sysaddon, i['action'])
                try: url += '&url=%s' % urllib.quote_plus(i['url'])
                except: pass

                cm = []
				
                item = control.item(label=name, iconImage=thumb, thumbnailImage=thumb)
                item.addContextMenuItems(cm, replaceItems=False)
                if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)
                control.addItem(handle=int(sys.argv[1]), url=url, listitem=item, isFolder=True)
            except:
                pass

        control.directory(int(sys.argv[1]), cacheToDisc=True)

