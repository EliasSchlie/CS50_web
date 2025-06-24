from django.shortcuts import render
from django.shortcuts import redirect
import random
import markdown2
from . import util


def index(request):
    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries()
    })

def entry(request, title):
    content = util.get_entry(title)
    if content is None:
        entries = util.list_entries()
        entries = [entry for entry in entries if title in entry]
        return render(request, "encyclopedia/error.html", {
            "error_message": f"{title} not found",
            "entries": entries
        })
    
    return render(request, "encyclopedia/entry.html", {
        "entry_title": title,
        "entry_content": markdown2.markdown(content)
    })

def search(request):
    query = request.GET.get("q")
    return redirect("entry", title=query)

def new_page(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        if title and content:
            if title in util.list_entries():
                return render(request, "encyclopedia/error.html", {
                    "error_message": f"{title} already exists"
                })
            else:
                util.save_entry(title, content)
                return redirect("entry", title=title)
        else:
            return render(request, "encyclopedia/error.html", {
                "error_message": "Title and content are required"
            })
    else:
        return render(request, "encyclopedia/new_page.html")
    
def editor(request, title=None):
    if request.method == "GET" and title is None:
        title = request.GET.get("title")
        return redirect(f"editor/{title}")
    
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        if title and content:
            util.save_entry(title, content)
            return redirect("entry", title=title)
        else:
            return render(request, "encyclopedia/error.html", {
                "error_message": "Title and content are required"
            })
    else:
        return render(request, "encyclopedia/editor.html", {
            "title": title,
            "content": util.get_entry(title)
        })

def random_page(request):
    entries = util.list_entries()
    return redirect("entry", title=random.choice(entries))