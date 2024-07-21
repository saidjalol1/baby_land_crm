from typing import Any
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import Province, Regions, Sale, Shop, Product, SaleItems

class GetRegionsView(View):
    def get(self, request):
        province_id = request.GET.get('province_id')
        regions = list(Regions.objects.filter(province_id=province_id).values('id', 'name'))
        return JsonResponse(regions, safe=False)

class GetShopsView(View):
    def get(self, request):
        region_id = request.GET.get('region_id')
        shops = list(Shop.objects.filter(region_id=region_id).values('id', 'name'))
        return JsonResponse(shops, safe=False)

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
    
    
class SaleView(ListView):
    template_name = "sale.html"
    model = Sale
    paginate_by = 10
    context_object_name = 'object_list'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["provinces"] = Province.objects.all()
        context["regions"] = Regions.objects.all()
        context["shops"] = Shop.objects.all()
        return context
    
    def post(self, request):
        if "add" in request.POST:
            obj = Sale.objects.create(
                shop = Shop.objects.get(id=request.POST.get("shop"))
            )
            return redirect("main_app:sale")
        if "delete" in request.POST:
            obj = Sale.objects.get(id=request.POST.get("sale")).delete()
            return redirect("main_app:sale")
    
class SaleDetailView(DetailView):
    template_name = "sale_detail.html"
    model = Sale
    context_object_name = 'sale'
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetching all products
        products = Product.objects.all()
        paginator_products = Paginator(products, self.paginate_by)
        page_number_products = self.request.GET.get('page_products')
        page_obj_products = paginator_products.get_page(page_number_products)
        
        # Fetching sale items
        sale_items = SaleItems.objects.filter(sale=self.object)
        paginator_sale_items = Paginator(sale_items, self.paginate_by)
        page_number_sale_items = self.request.GET.get('page_sale_items')
        page_obj_sale_items = paginator_sale_items.get_page(page_number_sale_items)
        
        context["page_obj_products"] = page_obj_products
        context["page_obj_sale_items"] = page_obj_sale_items
        
        return context


class StorageView(ListView):
    template_name = "storage.html"
    model = Product
    context_object_name = 'products'
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetching all products
        products = Product.objects.all()
        paginator_products = Paginator(products, self.paginate_by)
        page_number_products = self.request.GET.get('page_products')
        page_obj_products = paginator_products.get_page(page_number_products)
        
        context["page_obj_products"] = page_obj_products
        
        return context


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