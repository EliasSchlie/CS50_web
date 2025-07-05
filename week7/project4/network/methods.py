from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'What\'s on your mind?',
            'rows': 3
        }),
        label=''
    )

    class Meta:
        model = Post
        fields = ['content']
