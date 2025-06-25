from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create_listing", views.create_listing, name="create_listing"),
    path("listing/<int:listing_id>", views.listing, name="listing"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("close_auction", views.close_auction, name="close_auction"),
    path("bid", views.bid, name="bid"),
    path("comment", views.comment, name="comment"),
    path("category", views.category, name="category_list"),
    path("category/<str:category>", views.category, name="category_detail"),
]
