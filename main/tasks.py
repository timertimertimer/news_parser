from news_parser.celery import app
from .models import Article, Source
from .core import *




@app.task
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


@app.task
def parse_rbk():
    def parse_html(html_list):
        for html in html_list:
            soup = BeautifulSoup(html, 'html.parser')
            link = soup.find('link', {'rel': 'canonical'})['href']
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
                    publish_date = article.find(
                        'time', class_='article__header__date')['datetime']
                except TypeError:
                    publish_date = None

            category = article.find('a', class_=[
                'article__header__category', 'master-tags__channel']).text
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


@app.task
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
        parse_html(asyncio.run(get_html_from_every_page_async(links)))
    else:
        print("something went wrong with tass")
