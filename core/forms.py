from django import forms
from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['skills', 'resume', 'interests', 'availability', 'linkedin_url', 'github_url']

    def clean(self):
        cleaned_data = super().clean()
        skills = cleaned_data.get('skills')
        resume = cleaned_data.get('resume')

        if not skills and not resume:
            raise forms.ValidationError("Please provide skills or upload a resume.")

        return cleaned_data