from django import forms
from .models import Listings, Category

class ListingForm(forms.ModelForm):
    new_category = forms.CharField(required=False, label="Or create a new category")

    class Meta:
        model = Listings
        fields = ['title', 'description', 'starting_bid', 'image_url', 'category']

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        new_category = cleaned_data.get('new_category')

        if not category and not new_category:
            raise forms.ValidationError("Please select or create a category.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        new_category = self.cleaned_data.get('new_category')
        if new_category:
            category_obj, created = Category.objects.get_or_create(name=new_category)
            instance.category = category_obj
        if commit:
            instance.save()
        return instance

class CommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea(attrs={"rows": 4, "cols": 40}))