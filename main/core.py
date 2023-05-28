"""Main functions for all sites"""
import os
import aiofiles
import aiohttp
import asyncio
import sqlite3
import requests
import urllib3
import re
import json
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime
from pytz import timezone
from .models import Article

urllib3.disable_warnings()

con = sqlite3.connect("db.sqlite3")
cur = con.cursor()

path = './saved_html'

skip_links = [
    'https://travel-guide.rbc.ru/',
    'special.kommersant.ru',
    'gallery'
]


def iso_to_unix(iso_string: str) -> int:
    dt = datetime.fromisoformat(iso_string)
    dt = dt.astimezone(timezone('UTC'))
    unix_time = dt.timestamp()
    return int(unix_time)


def format_string(s: str):
    if s:
        return s.strip().replace('\xa0', ' ').replace('&nbsp;', ' ').replace('"', '/').replace("'", "/")
    return s


def insert(link: str, source: str, title: str, date: str, category: str, description: str, text: list[str]):
    link = format_string(link)
    title = format_string(title)
    if date:
        date = iso_to_unix(date)
    category = format_string(category)
    description = format_string(description)
    text = '\n'.join([format_string(el) for el in list(filter(None, text))])
    query = f"""INSERT INTO main_article(link, source, title, date, category, description, text) VALUES
    ("{link}", "{title}", "{date}", "{category}", "{description}", "{text}");"""
    cur.execute(query)
    con.commit()


def is_skip_link(link: str) -> bool:
    for el in skip_links:
        if el in link:
            return True
    return False


def replace_slashes_in_link(link):
    return link.replace("/", "_")


def get_next_link_from_main_page(url, classes, headers=None, payload=None):
    if headers is None:
        headers = {
            'User-Agent': UserAgent().random
        }
    else:
        headers['User-Agent'] = UserAgent().random
    response = requests.get(url, headers=headers,
                            data=payload, timeout=20, verify=False)
    try:
        response.raise_for_status()
    except Exception as e:
        print(e)
        return
    soup = BeautifulSoup(response.content, 'html.parser')
    link = soup.find('a', {'class': classes})
    while link is not None:
        if link['href'] != 'https://tass.ru/' and not is_skip_link(link['href']):
            yield link['href']
        link = link.find_next('a', {'class': classes})


async def get_html_from_every_page_async(links: list, headers=None, payload=None):
    """Gets html from every page and saves"""
    if headers is None:
        headers = {
            'User-Agent': UserAgent().random
        }
    else:
        headers['User-Agent'] = UserAgent().random
    async with aiohttp.ClientSession() as session:
        tasks = []
        for link in links:
            if is_html_saved(link):
                continue
            tasks.append(asyncio.create_task(
                get_page_data(session, link, headers)))
        html_list = await asyncio.gather(*tasks)
    return html_list


async def get_html_from_every_page_and_save_async(links: list, headers=None, payload=None):
    """Gets html from every page and saves"""
    if headers is None:
        headers = {
            'User-Agent': UserAgent().random
        }
    else:
        headers['User-Agent'] = UserAgent().random
    async with aiohttp.ClientSession() as session:
        tasks = []
        for link in links:
            # if is_html_saved(link):
            #     continue
            task = asyncio.create_task(
                get_page_data_and_save(session, link, headers, payload))
            tasks.append(task)
        await asyncio.gather(*tasks)


def is_html_saved(link):
    if os.path.exists(f'{path}/{link}.html'):
        return True
    return False


async def get_page_data(session, link, headers=None, payload=None):
    async with session.get(link, ssl=False, headers=headers, data=payload) as response:
        try:
            response.raise_for_status()
        except Exception as e:
            print(e)
            return
        return await response.text()


async def get_page_data_and_save(session, link, headers=None, payload=None):
    async with session.get(link, ssl=False, headers=headers, data=payload) as response:
        response.raise_for_status()
        html = await response.text()
        await save_html_async(html, link)


async def save_html_async(html, link):
    """Saves the given html to a file"""
    link = replace_slashes_in_link(link)
    async with aiofiles.open(f"{path}/{link}.html", mode="w+", encoding="utf-8") as file:
        await file.write(html)


def get_content_from_saved_page():
    """Gets the content of a saved page"""
    for file in os.listdir(path):
        with open(f"{path}/{file}", "r", encoding="utf-8") as f:
            yield f.read()


def format_rows_and_save(link: str, source_name: str, title: str, date: str, category: str, description: str, text: list[str]):
    link = format_string(link)
    title = format_string(title)
    if date:
        date = iso_to_unix(date)
    category = format_string(category)
    description = format_string(description)
    text = '\n'.join([format_string(el) for el in list(filter(None, text))])
    if not Article.objects.filter(link=link).exists():
        article, created = Article.objects.get_or_create(
            link=link,
            source=source_name,
            title=title,
            date=date,
            category=category,
            description=description,
            text=text
        )
        article.save()


def parse_habr():
    def parse_html(html_list):
        for html in html_list:
            soup = BeautifulSoup(html, 'html.parser')
            link = soup.find('link', {'rel': 'canonical'})['href']
            description = soup.find('meta', {'name': 'description'})['content']
            article = soup.find('article')
            title = article.find('h1').text
            category = article.find(
                'div', class_='tm-article-snippet__hubs').text
            publish_date = article.find('time')['datetime']
            text = [el.text for el in article.find_all('p')]
            if not text:
                text = soup.find(
                    'div', {'class': 'tm-article-body'}).text.split('\n')
            format_rows_and_save(link, 'Хабр', title,
                                 publish_date, category, description, text)
    url = 'https://habr.com'
    classes = ['tm-title__link']
    links = [
        url + link for link in get_next_link_from_main_page(url + '/ru', classes)]
    if links:
        parse_html(asyncio.run(get_html_from_every_page_async(links)))
    else:
        print("something went wrong with habr")


def parse_iz():
    def parse_html(html_list):
        for html in html_list:
            soup = BeautifulSoup(html, 'html.parser')
            link = soup.find('link', {'rel': 'canonical'})['href']
            publish_date = soup.find('time')['datetime']
            category = soup.find('meta', {'property': 'article:section'})[
                'content']
            title = soup.find('title').text
            description = soup.find('meta', {'name': 'description'})['content']
            article = soup.find('article')
            text = [el.text for el in article.find_all('p')]
            format_rows_and_save(link, 'Известия', title,
                                 publish_date, category, description, text)
    url = "https://iz.ru/"
    classes = ['short-last-news__inside__list__item']
    headers = {
        'Cookie': '__ddg1_=cRfFnlv9eJ8anwW9m84D'
    }
    links = [
        url + link for link in get_next_link_from_main_page(url, classes, headers)]
    if links:
        parse_html(asyncio.run(get_html_from_every_page_async(links, headers)))
    else:
        print("something went wrong with iz")


def parse_mk():
    def parse_html(html_list):
        for html in html_list:
            soup = BeautifulSoup(html, 'html.parser')
            link = soup.find('link', {'rel': 'canonical'})['href']
            title = soup.find('title').text
            description = soup.find('meta', {'name': 'description'})['content']
            article = soup.find('div', class_='article-grid__content')
            publish_date = article.find('time')['datetime']
            category = article.find('a', class_='meta__item-link').text
            text = []
            for el in article.find('div', class_='article__body').find_all('p'):
                text.append(el.text)
            format_rows_and_save(link, 'Московский Комсомолец',
                                 title, publish_date, category, description, text)
    url = 'https://www.mk.ru/news/'
    classes = ['news-listing__item-link']
    links = [link for link in get_next_link_from_main_page(url, classes)]
    if links:
        parse_html(asyncio.run(get_html_from_every_page_async(links[:30])))
    else:
        print("something went wrong with mk")


def parse_rbk():
    def parse_html(html_list):
        for html in html_list:
            soup = BeautifulSoup(html, 'html.parser')
            try:
                link = soup.find('link', {'rel': 'canonical'})['href']
            except TypeError:
                with open('test.html', 'w', encoding="utf-8") as f:
                    f.write(html)
            if 'quote.ru' in link:
                quote(soup, link)
                continue
            title = soup.find('title').text
            description = soup.find('meta', {'name': 'description'})['content']
            article = soup.find('div', class_='article')
            try:
                time_str = article.find(
                    'div', class_='article__header__note').text.strip()
                date_obj = datetime.strptime(
                    time_str, "Опубликовано %d.%m.%Y, %H:%M")
                tz = timezone('Europe/Moscow')
                date_obj = tz.localize(date_obj)
                publish_date = date_obj.isoformat()
            except AttributeError:
                try:
                    publish_date = article.find('time', class_='article__header__date')['datetime']
                except TypeError:
                    publish_date = None

            category = article.find('a', class_=['article__header__category', 'master-tags__channel']).text
            text = []
            for el in article.find_all("p"):
                if el.find('div') is None:
                    text.append(el.text)
            format_rows_and_save(link, 'РБК', title,
                                 publish_date, category, description, text)

    def quote(soup, link):
        for article in soup.find_all('div', class_='MuiGrid-root MuiGrid-container MuiGrid-item quote-style-ijxrrd'):
            publish_date = article.find('time')['datetime']
            category = article.find(
                'div', class_='MuiGrid-root MuiGrid-item quote-style-o3aqx2').text
            title = article.find(
                'h1', class_='MuiTypography-root MuiTypography-h1 quote-style-t9x6ph').text
            description = article.find(
                'div', class_='MuiGrid-root quote-style-s7va7x').text
            text = list(map(lambda x: x.text,
                            article.find('div', class_='MuiGrid-root quote-style-1mtod11').find_all('p')))
            format_rows_and_save(link, 'РБК', title,
                                 publish_date, category, description, text)

    url = "https://www.rt.rbc.ru/"
    classes = ['main__big__link', 'main__feed__link']
    links = [link for link in get_next_link_from_main_page(url, classes)]
    if links:
        parse_html(asyncio.run(get_html_from_every_page_async(links)))
    else:
        print("something went wrong with rbc")


def parse_tass():
    def parse_html(html_list):
        for html in html_list:
            soup = BeautifulSoup(html, 'html.parser')
            link = soup.find('link', {'rel': 'canonical'})['href']
            title = soup.find('title').text
            description = re.sub(' +', ' ',
                                 soup.find('meta', {'name': 'description'})['content'].strip().replace('\n', ' '))
            publish_date = json.loads(soup.find_all('script', {'type': 'application/ld+json'})[-1].text.strip())[
                'datePublished']
            if 'https://nauka.tass.ru/' in link:
                article = soup.find('div', class_='article-inner')
                category = 'Наука'
                text = [el.text for el in article.find_all('p')]
                insert(link, title, publish_date, category, description, text)
                continue
            article = soup.find('article')
            try:
                category = soup.find(
                    'a', class_='materialMarks_mark__xjudQ').text
            except AttributeError:
                category = None
            text = list(map(lambda x: x.text,
                            article.find_all('p', class_='Paragraph_paragraph__nYCys')))
            text = list(filter(None, text))
            format_rows_and_save(link, 'ТАСС', title,
                                 publish_date, category, description, text)
    url = "https://tass.ru/"
    classes = ['tass_pkg_simple_card-K0P4w', 'tass_pkg_card_wrapper-r-hZB']
    links = [url + link for link in
             get_next_link_from_main_page(url, classes)]
    if links:
        try:
            parse_html(asyncio.run(get_html_from_every_page_async(links)))
        except Exception as e:
            print("something went wrong with tass")
            print(e)
    else:
        print("something went wrong with tass")
