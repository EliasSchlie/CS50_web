from django.contrib import admin
from .models import Listings, Bids, Comments, Category

class BidsInline(admin.TabularInline):
    model = Bids
    extra = 0

class CommentsInline(admin.TabularInline):
    model = Comments
    extra = 0

class ListingsAdmin(admin.ModelAdmin):
    inlines = [BidsInline, CommentsInline]
    list_display = ('title', 'category', 'active', 'owner')
    list_filter = ('category', 'active', 'owner')

admin.site.register(Listings, ListingsAdmin)
admin.site.register(Bids)
admin.site.register(Comments)
admin.site.register(Category)