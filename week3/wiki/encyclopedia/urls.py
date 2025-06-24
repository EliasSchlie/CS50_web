from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("search", views.search, name="search"),
    path("editor", views.editor, name="editor"),
    path("editor/<str:title>", views.editor, name="editor"),
    path("new_page", views.new_page, name="new_page"),
    path("random_page", views.random_page, name="random_page"),
    path("<str:title>", views.entry, name="entry"),
]
