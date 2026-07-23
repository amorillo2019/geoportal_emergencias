from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import UserLoginForm, UserProfileForm


class UserLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = UserLoginForm


@login_required
def profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("usuarios:perfil")
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, "usuarios/profile.html", {"form": form})
