# social/forms.py
from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Form for creating and editing posts"""
    class Meta:
        model = Post
        fields = ['content', 'image', 'allow_comments']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Share your thoughts...',
                'maxlength': '5000'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'allow_comments': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'content': 'What\'s on your mind?',
            'image': 'Add an image (optional)',
            'allow_comments': 'Allow comments on this post'
        }


class CommentForm(forms.ModelForm):
    """Form for creating comments"""
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write a comment...',
                'maxlength': '1000'
            })
        }
        labels = {
            'content': ''
        }


class LikeAmountForm(forms.Form):
    """Form for specifying the number of likes to give"""
    amount = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'placeholder': 'Number of likes'
        })
    )
