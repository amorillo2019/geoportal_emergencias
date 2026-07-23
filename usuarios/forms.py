from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password

from .models import User


class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Correo electronico", widget=forms.EmailInput(attrs={"autofocus": True}))


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "email")
        widgets = {
            "email": forms.EmailInput(attrs={"readonly": True}),
        }


class UserPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Correo electronico")


class UserSetPasswordForm(SetPasswordForm):
    pass


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Contrasena", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contrasena", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone", "role", "is_staff", "is_active")

    def clean_password2(self):
        password = self.cleaned_data.get("password2")
        if self.cleaned_data.get("password1") != password:
            raise forms.ValidationError("Las contrasenas no coinciden.")
        validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
