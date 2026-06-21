from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import User


def validate_uploaded_file(uploaded_file, allowed_extensions):
    if not uploaded_file:
        return

    extension = uploaded_file.name.rsplit('.', 1)[-1].lower()

    if extension not in allowed_extensions:
        allowed = ', '.join(sorted(allowed_extensions))
        raise ValidationError(f'Дозволені формати файлів: {allowed}.')

    if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
        max_size_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
        raise ValidationError(f'Максимальний розмір файлу: {max_size_mb} МБ.')


class RegisterUserForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': 'Логін',
            'email': 'Електронна пошта',
            'password1': 'Пароль',
            'password2': 'Підтвердження пароля',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'

        if commit:
            user.save()

        return user


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['avatar']
        labels = {
            'avatar': 'Аватар',
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        validate_uploaded_file(avatar, {'jpg', 'jpeg', 'png', 'webp'})
        return avatar