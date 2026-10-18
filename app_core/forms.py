from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Profile


class SignupForm(forms.Form):
    """Registration form with password confirmation and validation."""
    username = forms.CharField(
        max_length=150,
        min_length=3,
        widget=forms.TextInput(attrs={
            'placeholder': 'Username',
            'class': 'w-full px-4 py-3 border rounded-lg bg-white/70 text-gray-900 '
                     'placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
        }),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email',
            'class': 'w-full px-4 py-3 border rounded-lg bg-white/70 text-gray-900 '
                     'placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
        }),
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'id': 'password',
            'class': 'w-full px-4 py-3 border rounded-lg bg-white/70 text-gray-900 '
                     'placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
        }),
    )
    passwordc = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Password',
            'id': 'passwordc',
            'class': 'w-full px-4 py-3 border rounded-lg bg-white/70 text-gray-900 '
                     'placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
        }),
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not username.isalnum() and '_' not in username:
            raise ValidationError('Username may only contain letters, numbers, and underscores.')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email is already registered.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        passwordc = cleaned_data.get('passwordc')
        if password and passwordc and password != passwordc:
            self.add_error('passwordc', 'Passwords do not match.')
        return cleaned_data


class ProfileForm(forms.ModelForm):
    """Form for editing user profile settings."""

    class Meta:
        model = Profile
        fields = ['profileimg', 'bio', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full p-2 border rounded-lg bg-white/70 text-gray-900 '
                         'focus:ring-2 focus:ring-blue-400',
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-lg bg-white/70 text-gray-900 '
                         'focus:ring-2 focus:ring-blue-400',
            }),
            'profileimg': forms.ClearableFileInput(attrs={
                'accept': 'image/png, image/gif, image/jpeg',
                'class': 'mt-2 w-full text-center',
            }),
        }


class PostForm(forms.Form):
    """Form for uploading a new post."""
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'mp4'}
    MAX_SIZE_MB = 5

    image_upload = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'w-full p-2 border rounded-lg bg-white/70 text-gray-900 '
                     'focus:ring-2 focus:ring-blue-400',
        }),
    )
    caption = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Caption...',
            'class': 'w-full mt-2 p-2 border rounded-lg bg-white/70 text-gray-900 '
                     'focus:ring-2 focus:ring-blue-400',
        }),
    )

    def clean_image_upload(self):
        image = self.cleaned_data['image_upload']
        ext = image.name.rsplit('.', 1)[-1].lower() if '.' in image.name else ''
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f'Invalid file type "{ext}". Allowed: {", ".join(sorted(self.ALLOWED_EXTENSIONS))}'
            )
        if image.size > self.MAX_SIZE_MB * 1024 * 1024:
            raise ValidationError(f'File size must be under {self.MAX_SIZE_MB} MB.')
        return image


class SearchForm(forms.Form):
    """Simple search form."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search for username',
            'id': 'search-input',
            'class': 'px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 '
                     'focus:ring-blue-400 w-full',
        }),
    )
