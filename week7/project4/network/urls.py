from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("profile/<int:profile_id>/", views.profile, name="profile"),
    path("profile/<int:profile_id>/posts/", views.posts_user, name="posts_user"),
    path("posts/following/", views.posts_following, name="posts_following"),
    path("posts/all/", views.posts_all, name="posts_all"),
    path("follow_toggle/", views.follow_toggle, name="follow_toggle"),
    path("like/", views.like, name="like"),
    path("comment/", views.comment, name="comment"),
    path("posts/<int:post_id>/comments/", views.post_comments, name="post_comments"),
]
