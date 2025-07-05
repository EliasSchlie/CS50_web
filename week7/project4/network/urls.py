from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("following", views.index, name="following"),
    path("u/<str:username>", views.index, name="user"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),

    # API Routes
    path("api/users/me", views.current_user, name="current_user"),
    path("api/posts", views.posts, name="posts"),
    path("api/posts/<int:post_id>", views.post, name="post"),
    path("api/posts/<str:filter_by>", views.posts, name="posts_filtered"),
    path("api/users/<str:username>", views.profile, name="profile_api"),
    path("api/users/<str:username>/follow", views.follow, name="follow"),
    path("api/comments", views.comments, name="comments"),
    path("api/posts/<int:post_id>/comments", views.post_comments, name="post_comments"),
]
