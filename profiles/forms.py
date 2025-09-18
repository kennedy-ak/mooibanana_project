# profiles/forms.py
from django import forms
from .models import Profile, ProfilePhoto

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'birth_date', 'study_field', 'study_year', 'school_name', 'interests', 'profile_picture', 'city', 'location', 'latitude', 'longitude']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'school_name': forms.TextInput(attrs={'placeholder': 'e.g., University of Ghana, KNUST, UCC'}),
            'interests': forms.TextInput(attrs={'placeholder': 'e.g., Football, Music, Photography'}),
            'city': forms.TextInput(attrs={'placeholder': 'e.g., Accra, Kumasi, Cape Coast'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Greater Accra Region, Ashanti Region'}),
            'latitude': forms.NumberInput(attrs={'placeholder': 'Latitude (optional)', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'placeholder': 'Longitude (optional)', 'step': 'any'}),
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

    school_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by school (e.g., University of Ghana)...',
            'class': 'form-control'
        })
    )

    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by city (e.g., Accra, Kumasi)...',
            'class': 'form-control'
        })
    )

    max_distance = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=500,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max distance (km)',
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

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class ProfilePhotoForm(forms.Form):
    photos = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        }),
        help_text='You can select multiple images (max 6 photos)'
    )