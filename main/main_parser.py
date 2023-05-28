from core import *


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
                    'div', {'xmlns': 'http://www.w3.org/1999/xhtml'}).text.split('\n')
            insert(link, title, publish_date, category, description, text)

    url = 'https://habr.com'
    classes = ['tm-title__link']
    links = [
        url + link for link in get_next_link_from_main_page(url + '/ru', classes)]
    if links:
        parse_html(asyncio.run(get_html_from_every_page_async(links)))
    else:
        print("something went wrong")


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
            insert(link, title, publish_date, category, description, text)
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
        print("something went wrong")


def parse_kommersant():
    
