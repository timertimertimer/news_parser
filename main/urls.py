from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('article/<str:pk>/', views.article, name="article"),
    path('parse_articles/', views.parse_articles, name="parse_articles")
]
