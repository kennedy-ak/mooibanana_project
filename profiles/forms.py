# profiles/forms.py
from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'birth_date', 'study_field', 'study_year', 'interests', 'profile_picture', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'interests': forms.TextInput(attrs={'placeholder': 'e.g., Football, Music, Photography'}),
        }

class ProfileSearchForm(forms.Form):
    STUDY_CHOICES = [('', 'All Studies')] + Profile.STUDY_CHOICES

    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name...',
            'class': 'form-control'
        })
    )

    study_field = forms.ChoiceField(
        choices=STUDY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    interests = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by interests (e.g., football, music)...',
            'class': 'form-control'
        })
    )

    min_age = forms.IntegerField(
        required=False,
        min_value=18,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min age',
            'class': 'form-control'
        })
    )

    max_age = forms.IntegerField(
        required=False,
        min_value=18,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max age',
            'class': 'form-control'
        })
    )

    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by location...',
            'class': 'form-control'
        })
    )