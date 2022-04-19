from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
from urllib.parse import urlparse
import asyncio
import aiohttp
from aiohttp import ClientConnectorError

from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import View


class Index(TemplateView):
    template_name = 'index.html'


class Scraper(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._origin_url = None
        self._ua = UserAgent()
        self._session = None
        self._search_link = 0
        self._max_retrieved = False
        self._total_links = 0

    def get(self, request):
        if request.method == 'GET':
            url = request.GET.get('url')
            page = request.GET.get('page')

            try:
                self._search_link = int(page)
            except (TypeError, ValueError) as e:
                print(e)

            context = asyncio.run(self.async_get(url))

            if page:
                if 'status' not in context:
                    context.update({'status': 200, 'total': self._total_links})

                return JsonResponse(context)

            if context.get('status') == 400:
                return HttpResponseBadRequest('Bad Request')

            return render(request, 'search.html', context)

        return HttpResponseBadRequest('Bad Request')

    async def async_get(self, url):
        if not url.startswith('http'):
            url = 'https://' + url

        async with aiohttp.ClientSession() as session:
            self._session = session
            self._origin_url = self._url_parser(url)
            response = await self._fetch(url)

            if response is None:
                return {'message': 'Bad Request', 'status': 400}

            headers, values = await self._grab_url_data(response)

            if self._max_retrieved:
                return {'message': 'Bad Request', 'status': 400, 'total': self._total_links}

        context = {'table': {'headers': headers, 'values': values}}
        return context

    # make request
    async def _fetch(self, url, res_type='text'):
        headers = {'User-Agent': self._ua.random}

        try:
            async with self._session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None

                if res_type == 'text':
                    return await response.text()
                elif res_type == 'json':
                    return await response.json()
        except (TimeoutError, ClientConnectorError):
            return None

    # get url metadata from api
    async def _grab_url_data(self, text):
        html = bs(text, 'html.parser')
        a = html.find_all('a')
        a = [tag for tag in a if tag.get('href')]
        meta_head = []
        full_links_data = []
        tasks = []
        self._max_retrieved = False
        self._total_links = len(a)

        if self._search_link > len(a):
            self._max_retrieved = True
            return [], []

        for link in a[self._search_link:self._search_link + 1]:
            url = link.get('href')
            parsed_url = self._url_parser(url)

            if url:
                if not parsed_url['scheme']:
                    url = f"https://{self._origin_url['origin']}{url}"

                url_info = self._grab_url_metadata(url)

                if url_info:
                    tasks.append(asyncio.create_task(url_info))

        metadata = await asyncio.gather(*tasks)
        for meta in metadata:
            if meta:
                meta_head, meta_value = meta
                full_links_data.extend(meta_value)

        return meta_head, full_links_data

    async def _grab_url_metadata(self, url):
        response = await self._fetch(
            f'https://api.domainsdb.info/v1/domains/search?domain={url}',
            res_type='json'
        )

        url_meta = self._format_meta(url, response)
        return url_meta

    @staticmethod
    def _url_parser(url):
        parsed_uri = urlparse(url)
        return {
            'scheme': parsed_uri.scheme,
            'origin': parsed_uri.netloc
        }

    # prepare metadata for rendering
    @staticmethod
    def _format_meta(url, url_info):
        if not url_info or 'message' in url_info.keys():
            return None

        meta_head = ['url']
        meta_values = []

        meta_head.extend(url_info['domains'][0].keys())

        for meta in url_info['domains']:
            values = [url]

            for value in meta.values():
                # if current column is dictionary
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    value = [val.get('exchange') for val in value]

                values.append(value)

            meta_values.append(values)

        return meta_head, meta_values
