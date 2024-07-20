from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.models import User
from .models import Province, Regions, Shop

@method_decorator(login_required, name='dispatch')
class ProvincesView(ListView):
    template_name = "provinces.html"
    model = Province

@method_decorator(login_required, name='dispatch')
class ProvinceDetailView(DetailView):
    template_name = "regions.html"
    model = Province
    context_object_name = 'province'

@method_decorator(login_required, name='dispatch')
class RegionDetailView(DetailView):
    template_name = "shops.html"
    model = Regions
    context_object_name = 'region'


@method_decorator(login_required, name='dispatch')
class StatisicsView(View):
    template = "index.html"
    
    def get_context_data(self, **kwargs):
        context = {}
        return context
    
    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template, context)

    def post(self, request):
        context = self.get_context_data()
        return render(request, self.template, context)
    

class LoginView(View):
    template_name = "register/pages-login.html"
        
    def get(self, request):
        context = {}
        return render(request, self.template_name, context)
    
    def post(self, request):
        context = {}
        if "login" in request.POST:
            username = request.POST.get("username")
            password = request.POST.get("password")
            
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect("main_app:main")
            else:
                context["error"] = "Parol Yoki Foydalanuvchi nomi Xato!"
                return render(request, self.template_name, context)
        return render(request, self.template_name, context)