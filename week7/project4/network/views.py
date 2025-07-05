from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import User, Post, Comment, LikeLog
from .methods import PostForm


def index(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("login"))
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return HttpResponseRedirect(reverse("index"))
    else:
        form = PostForm()
    return render(request, "network/index.html", {"form": form, "posts": Post.objects.all().order_by('-timestamp')})

def profile(request, profile_id):
    profile = get_object_or_404(User, id=profile_id)
    return render(request, "network/user.html", {"profile": profile})

def posts_all(request):
    posts = Post.objects.all().order_by('-timestamp')
    data = [
        {
            'id': post.id,
            'user_id': post.user_id,
            'user__username': post.user.username,
            'content': post.content,
            'timestamp': post.timestamp,
            'likes_count': post.likes.count(),
        }
        for post in posts
    ]
    return JsonResponse(data, safe=False)

def posts_following(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    posts = Post.objects.filter(user__in=request.user.following.all()).order_by('-timestamp')
    data = [
        {
            'id': post.id,
            'user_id': post.user_id,
            'user__username': post.user.username,
            'content': post.content,
            'timestamp': post.timestamp,
            'likes_count': post.likes.count(),
        }
        for post in posts
    ]
    return JsonResponse(data, safe=False)

def posts_user(request, profile_id):
    user = get_object_or_404(User, id=profile_id)
    posts = Post.objects.filter(user=user).order_by('-timestamp')
    data = [
        {
            'id': post.id,
            'user_id': post.user_id,
            'user__username': post.user.username,
            'content': post.content,
            'timestamp': post.timestamp,
            'likes_count': post.likes.count(),
        }
        for post in posts
    ]
    return JsonResponse(data, safe=False)

def comment(request):
    if not request.user.is_authenticated or request.method != "POST":
        return JsonResponse({"error": "Authentication required."}, status=403)
    try:
        data = json.loads(request.body)
        post_id = data.get("post_id")
        if not post_id:
            return JsonResponse({"error": "No post_id provided."}, status=400)
        post = Post.objects.get(id=post_id)
        user = request.user
        comment = data.get("comment")
        if not comment:
            return JsonResponse({"error": "No comment provided."}, status=400)
        Comment.objects.create(post=post, user=user, content=comment)
        return JsonResponse({"success": True})
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def follow(request):
    if not request.user.is_authenticated or request.method != "POST":
        return JsonResponse({"error": "Authentication required."}, status=403)
    try:
        data = json.loads(request.body)
        profile_id = data.get("profile_id")
        if not profile_id:
            return JsonResponse({"error": "No profile_id provided."}, status=400)
        profile = User.objects.get(id=profile_id)
        user = request.user
        if user == profile:
            return JsonResponse({"error": "Cannot follow yourself."}, status=400)
        if user in profile.followers.all():
            profile.followers.remove(user)
            following = False
        else:
            profile.followers.add(user)
            following = True
        followers_count = profile.followers.count()
        return JsonResponse({"following": following, "followers_count": followers_count})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def like(request):
    if not request.user.is_authenticated or request.method != "POST":
        return JsonResponse({"error": "Authentication required."}, status=403)
    try:
        data = json.loads(request.body)
        post_id = data.get("post_id")
        if not post_id:
            return JsonResponse({"error": "No post_id provided."}, status=400)
        post = Post.objects.get(id=post_id)
        user = request.user
        if user in post.likes.all():
            post.likes.remove(user)
            liked = False
            LikeLog.objects.create(user=user, post=post, action="unlike")
        else:
            post.likes.add(user)
            liked = True
            LikeLog.objects.create(user=user, post=post, action="like")
        likes_count = post.likes.count()
        return JsonResponse({"liked": liked, "likes_count": likes_count})
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

def follow_toggle(request):
    if not request.user.is_authenticated or request.method != "POST":
        return JsonResponse({"error": "Authentication required."}, status=403)
    try:
        data = json.loads(request.body)
        profile_id = data.get("profile_id")
        if not profile_id:
            return JsonResponse({"error": "No profile_id provided."}, status=400)
        from .models import User
        profile = User.objects.get(id=profile_id)
        user = request.user
        if user == profile:
            return JsonResponse({"error": "Cannot follow yourself."}, status=400)
        if user in profile.followers.all():
            profile.followers.remove(user)
            following = False
        else:
            profile.followers.add(user)
            following = True
        followers_count = profile.followers.count()
        return JsonResponse({"following": following, "followers_count": followers_count})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def post_comments(request, post_id):
    comments = Comment.objects.filter(post_id=post_id).order_by('timestamp')
    return JsonResponse(list(comments.values('user__username', 'content', 'timestamp')), safe=False)
