from django.shortcuts import render
from django.db.models import Q
from .models import Article
from django.utils.timezone import make_aware
from datetime import datetime
from .core import parse_habr, parse_iz, parse_mk, parse_rbk, parse_tass

import time


def home(request):
    q = request.GET.get('q') if request.GET.get('q') else ''
    articles = Article.objects.filter(Q(source__icontains=q) |
                                      Q(link__icontains=q) |
                                      Q(title__icontains=q) |
                                      Q(category__icontains=q) |
                                      Q(description__icontains=q))
    sources = [source['source'] for source in Article.objects.order_by(
        'source').values('source').distinct()]

    context = {'articles': articles, 'sources': sources}
    return render(request, 'main/home.html', context)


def article(request, pk):
    article = Article.objects.get(id=pk)
    article.date = make_aware(datetime.fromtimestamp(article.date))
    sources = [source['source'] for source in Article.objects.order_by(
        'source').values('source').distinct()]
    context = {'article': article, 'sources': sources}
    return render(request, 'main/article.html', context)


def parse_articles(request):
    start = time.time()
    parse_habr()
    print('habr parsed for', time.time() - start, 'seconds')
    start = time.time()
    parse_iz()
    print('iz parsed for', time.time() - start, 'seconds')
    start = time.time()
    parse_mk()
    print('mk parsed for', time.time() - start, 'seconds')
    start = time.time()
    parse_rbk()
    print('rbk parsed for', time.time() - start, 'seconds')
    start = time.time()
    parse_tass()
    print('tass parsed for', time.time() - start, 'seconds')
    return render(request, 'main/success.html')
