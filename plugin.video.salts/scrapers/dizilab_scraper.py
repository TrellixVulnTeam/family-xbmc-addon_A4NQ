"""
    SALTS XBMC Addon
    Copyright (C) 2014 tknorris

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
"""
import re
import urlparse

from salts_lib import kodi
from salts_lib import log_utils
from salts_lib import scraper_utils
from salts_lib.constants import FORCE_NO_MATCH
from salts_lib.constants import VIDEO_TYPES
import scraper
import xml.etree.ElementTree as ET

try:
    from xml.parsers.expat import ExpatError
except ImportError:
    class ExpatError(Exception): pass
try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    class ParseError(Exception): pass

BASE_URL = 'http://dizilab.com'

class Dizilab_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.EPISODE])

    @classmethod
    def get_name(cls):
        return 'Dizilab'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        label = '[%s] %s' % (item['quality'], item['host'])
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url and source_url != FORCE_NO_MATCH:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
    
            for match in re.finditer('{\s*file\s*:\s*"([^"]+)', html):
                stream_url = match.group(1)
                if 'dizlab' in stream_url.lower():
                    continue
                hoster = {'multi-part': False, 'host': self._get_direct_hostname(stream_url), 'class': self, 'quality': scraper_utils.gv_get_quality(stream_url), 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
                hosters.append(hoster)

        return hosters

    def get_url(self, video):
        return self._default_get_url(video)

    def _get_episode_url(self, show_url, video):
        episode_pattern = 'class="episode"\s+href="([^"]+/sezon-%s/bolum-%s)"' % (video.season, video.episode)
        title_pattern = 'class="episode-name"\s+href="(?P<url>[^"]+)">(?P<title>[^<]+)'
        return self._default_get_episode_url(show_url, video, episode_pattern, title_pattern)

    def search(self, video_type, title, year):
        results = []
        xml_url = urlparse.urljoin(self.base_url, '/diziler.xml')
        xml = self._http_get(xml_url, cache_limit=24)
        if xml:
            norm_title = scraper_utils.normalize_title(title)
            match_year = ''
            try:
                for element in ET.fromstring(xml).findall('.//dizi'):
                    name = element.find('adi')
                    if name is not None and norm_title in scraper_utils.normalize_title(name.text):
                        url = element.find('url')
                        if url is not None and (not year or not match_year or year == match_year):
                            result = {'url': scraper_utils.pathify_url(url.text), 'title': name.text, 'year': ''}
                            results.append(result)
            except (ParseError, ExpatError) as e:
                log_utils.log('Dizilab Search Parse Error: %s' % (e), log_utils.LOGWARNING)

        return results
