from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import User, Listings, Bids, Comments, Category
from .forms import ListingForm, CommentForm

def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listings.objects.all()
    })

def listing(request, listing_id):
    listing = Listings.objects.get(pk=listing_id)
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "watchlist": request.user.watchlist.all() if request.user.is_authenticated else None,
        "bids": Bids.objects.filter(listing=listing) if len(Bids.objects.filter(listing=listing)) > 0 else None,
        "comment_form": CommentForm()
    })

@login_required
def comment(request):
    listing_id = request.POST["listing_id"]
    listing = Listings.objects.get(pk=listing_id)
    comment_form = CommentForm(request.POST)
    if comment_form.is_valid():
        comment = comment_form.cleaned_data["comment"]
        new_comment = Comments(comment=comment, user=request.user, listing=listing) 
        new_comment.save()
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))

@login_required
def watchlist(request):
    if request.method == "POST":
        listing_id = request.POST["listing_id"]
        listing = Listings.objects.get(pk=listing_id)
        user = request.user
        if request.POST["action"] == "Add to Watchlist":
            user.watchlist.add(listing)
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "watchlist": request.user.watchlist.all() if request.user.is_authenticated else None
            })
        elif request.POST["action"] == "Remove from Watchlist":
            user.watchlist.remove(listing)
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "watchlist": request.user.watchlist.all() if request.user.is_authenticated else None
            })
    else:
        return render(request, "auctions/watchlist.html", {
            "watchlist": request.user.watchlist.all() if request.user.is_authenticated else None
        })

@login_required
def close_auction(request):
    listing_id = request.POST["listing_id"]
    listing = Listings.objects.get(pk=listing_id)
    listing.active = False
    listing.save()
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))

@login_required
def bid(request):
    listing_id = request.POST["listing_id"]
    listing = Listings.objects.get(pk=listing_id)
    bids = Bids.objects.filter(listing=listing)
    bid = float(request.POST["bid"])
    if (len(bids) == 0 and bid > listing.starting_bid) or (len(bids) > 0 and bid > max([bid.amount for bid in bids])):
        new_bid = Bids(amount=bid, user=request.user, listing=listing)
        new_bid.save()
        messages.success(request, "Bid placed successfully.")
    elif len(bids) > 0:
        messages.error(request, "Bid must be greater than the current highest bid.")
    else:
        messages.error(request, "Bid must be greater than the starting bid.")
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))

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
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


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
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/create_listing.html", {
                "form": form
            })
    else:
        return render(request, "auctions/create_listing.html", {
            "form": ListingForm()
        })
    
def category(request, category=None):
    if category:
        category_obj = Category.objects.get(name=category)
        listings = Listings.objects.filter(category=category_obj, active=True)
        return render(request, "auctions/category.html", {
            "category": category_obj,
            "listings": listings
        })
    else:
        categories = Category.objects.all()
        return render(request, "auctions/categories.html", {
            "categories": categories
        })