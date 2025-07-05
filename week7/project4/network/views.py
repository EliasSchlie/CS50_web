from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.paginator import Paginator

from .models import User, Post, Comment, LikeLog
from .methods import PostForm


def index(request, **kwargs):
    return render(request, "network/index.html")

@require_http_methods(["GET"])
def current_user(request):
    if request.user.is_authenticated:
        return JsonResponse(request.user.serialize(request.user))
    else:
        return JsonResponse({"error": "User not authenticated"}, status=401)

@require_http_methods(["GET", "POST"])
def posts(request, filter_by=None):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)
        data = json.loads(request.body)
        content = data.get("content")
        if not content:
            return JsonResponse({"error": "Content is required."}, status=400)
        post = Post.objects.create(user=request.user, content=content)
        return JsonResponse(post.serialize(request.user), status=201)

    if filter_by == "following":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)
        posts_list = Post.objects.filter(user__in=request.user.following.all()).order_by("-timestamp")
    elif filter_by:
        user = get_object_or_404(User, username=filter_by)
        posts_list = Post.objects.filter(user=user).order_by("-timestamp")
    else:
        posts_list = Post.objects.all().order_by("-timestamp")

    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return JsonResponse({
        "posts": [post.serialize(request.user) for post in page_obj.object_list],
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
        "next_page_number": page_obj.next_page_number() if page_obj.has_next() else None,
        "previous_page_number": page_obj.previous_page_number() if page_obj.has_previous() else None,
        "total_pages": paginator.num_pages,
        "current_page": page_obj.number
    })

@require_http_methods(["GET", "PUT", "DELETE"])
def post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == "PUT":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        # Handle liking/unliking a post
        if 'like' in data:
            if request.user in post.likes.all():
                post.likes.remove(request.user)
            else:
                post.likes.add(request.user)
            return JsonResponse(post.serialize(request.user))

        # Handle editing a post's content
        if 'content' in data:
            if post.user != request.user:
                return JsonResponse({"error": "You do not have permission to edit this post."}, status=403)
            post.content = data['content']
            post.save()
            return JsonResponse(post.serialize(request.user))

        return JsonResponse({"error": "Missing 'like' or 'content' in request body."}, status=400)

    elif request.method == "DELETE":
        if not request.user.is_authenticated or post.user != request.user:
            return JsonResponse({"error": "Permission denied."}, status=403)
        post.delete()
        return JsonResponse({"message": "Post deleted."}, status=204)
    
    # GET request
    else:
        return JsonResponse(post.serialize(request.user))

@require_http_methods(["GET"])
def profile(request, username):
    user = get_object_or_404(User, username=username)
    return JsonResponse(user.serialize(request.user))

@require_http_methods(["POST"])
def follow(request, username):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)
    user_to_follow = get_object_or_404(User, username=username)
    if request.user == user_to_follow:
        return JsonResponse({"error": "You cannot follow yourself."}, status=400)
    if user_to_follow in request.user.following.all():
        request.user.following.remove(user_to_follow)
        return JsonResponse({"status": "unfollowed"})
    else:
        request.user.following.add(user_to_follow)
        return JsonResponse({"status": "followed"})

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
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
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })
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

@require_http_methods(["POST"])
def comments(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)
    try:
        data = json.loads(request.body)
        post_id = data.get("post_id")
        content = data.get("content")
        if not post_id or not content:
            return JsonResponse({"error": "Post ID and content are required."}, status=400)
        post = get_object_or_404(Post, id=post_id)
        comment = Comment.objects.create(user=request.user, post=post, content=content)
        return JsonResponse(comment.serialize(), status=201)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(["GET"])
def post_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all().order_by("timestamp")
    return JsonResponse([comment.serialize() for comment in comments], safe=False)
