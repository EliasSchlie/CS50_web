from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('greet/<str:name>', views.greet, name='greet'),
    path('index', views.index, name='index'),
]