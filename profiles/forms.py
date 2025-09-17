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