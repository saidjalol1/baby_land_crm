from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import Province, Regions, Sale, Shop, Product, SaleItems, Transaction
from django.contrib import messages
from print_funcs.pdf_generator import generate_pdf, generate_check_pdf
import pdfkit
from django.template.loader import render_to_string
from django.http import HttpResponse
    
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

class ProductGetView(View):
    def get(self, request, *args, **kwargs):
        product = Product.objects.filter(id=self.kwargs["pk"]).values("id",'qr_code_id', 'name', "sale_price", "base_price").first()
        print(product)
        if product:
            return JsonResponse(product, safe=False)
        else:
            return JsonResponse({'error': 'Product not found'}, status=404)
        
class SaleItemView(View):
    def get(self, request, *args, **kwargs):
        product = SaleItems.objects.filter(id=self.kwargs["pk"]).values("id",'product', 'quantity').first()
        products = Product.objects.get(id = product["product"])
        context = {
            "id": product["id"],
            "product": products.qr_code_id,
            "quantity": product["quantity"]
        }
        print(product)
        if product:
            return JsonResponse(context, safe=False)
        else:
            return JsonResponse({'error': 'Product not found'}, status=404)

class SaleGetView(View):
    def get(self, request, *args, **kwargs):
        product = Sale.objects.filter(id=self.kwargs["pk"]).values("id",'debt').first()
        print(product)
        if product:
            return JsonResponse(product, safe=False)
        else:
            return JsonResponse({'error': 'Product not found'}, status=404)
        
        
@method_decorator(login_required, name='dispatch')
class ProvincesView(ListView):
    template_name = "markets/provinces.html"
    model = Province

@method_decorator(login_required, name='dispatch')
class ProvinceDetailView(DetailView):
    template_name = "markets/regions.html"
    model = Province
    context_object_name = 'province'

@method_decorator(login_required, name='dispatch')
class RegionDetailView(DetailView):
    template_name = "markets/shops.html"
    model = Regions
    context_object_name = 'region'

@method_decorator(login_required, name='dispatch')
class ShopDetailView(ListView):
    template_name = "markets/shop_detail.html"
    model = Sale
    paginate_by = 10

    def get_queryset(self):
        shop = Shop.objects.get(id=self.kwargs["pk"])
        return Sale.objects.filter(shop=shop).order_by('date_added')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = Shop.objects.get(id=self.kwargs["pk"])
        context['shop'] = shop
        

        sale_items = Sale.objects.filter(shop=shop).order_by('date_added')
        paginator_sale_items = Paginator(sale_items, self.paginate_by)
        page_number_sale_items = self.request.GET.get('page')
        page_obj_sale_items = paginator_sale_items.get_page(page_number_sale_items)
        
        context["items"] = page_obj_sale_items
        return context
    
    
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
   
    
@method_decorator(login_required, name='dispatch')  
class SaleView(ListView):
    template_name = "sale/sale.html"
    model = Sale
    paginate_by = 10
    context_object_name = 'object_list'
    
    def get_queryset(self):
        # Return the base queryset
        return Sale.objects.all()
    
    def get_context_data(self, **kwargs):
        context = {}
        sale_items = Sale.objects.all()
        paginator_sale_items = Paginator(sale_items, self.paginate_by)
        page_number_sale_items = self.request.GET.get('page_sale_items')
        page_obj_sale_items = paginator_sale_items.get_page(page_number_sale_items)
        context = {
            "provinces":Province.objects.all(),
            "regions": Regions.objects.all(),
            "shops":Shop.objects.all(),
            "object_list": page_obj_sale_items
        }
        
        return context
    
    def post(self, request):
        queryset = self.get_queryset()
        context = self.get_context_data()
        if "add" in request.POST:
            obj = Sale.objects.create(
                shop = Shop.objects.get(id=request.POST.get("shop"))
            )
            return redirect("main_app:sale")
        if "delete" in request.POST:
            obj = Sale.objects.get(id=request.POST.get("sale")).delete()
            return redirect("main_app:sale")
        if 'filtr' in request.POST:
            from_date = request.POST.get('from')
            till_date = request.POST.get('till')
            if from_date and till_date:
                queryset = queryset.filter(date_added__range=[from_date, till_date])
            context["object_list"] = queryset
            return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')  
class DebtView(ListView):
    template_name = "sale/debts.html"
    model = Sale
    paginate_by = 10
    context_object_name = 'object_list'
    
    def get_queryset(self):
        # Return the base queryset
        return Sale.objects.all()
    
    def get_context_data(self, **kwargs):
        context = {}
        sale_items = Sale.objects.filter(debt__gte = 0)
        paginator_sale_items = Paginator(sale_items, self.paginate_by)
        page_number_sale_items = self.request.GET.get('page_sale_items')
        page_obj_sale_items = paginator_sale_items.get_page(page_number_sale_items)
        context = {
            "provinces":Province.objects.all(),
            "regions": Regions.objects.all(),
            "shops":Shop.objects.all(),
            "object_list": page_obj_sale_items
        }
        
        return context
    
    def post(self, request):
        queryset = self.get_queryset()
        context = self.get_context_data()
        if "save" in request.POST:
            debt = request.POST.get("debt")
            sale = Sale.objects.get(id = request.POST.get("sale"))
            if sale.debt < int(debt):
                messages.warning(request, "Foydalanuvchining 2000 UZS qarzi bor holos")
            else:
                sale.debt -= int(debt)
                sale.payment += int(debt)
                sale.save()
                return redirect("main_app:debt")
        if 'filtr' in request.POST:
            from_date = request.POST.get('from')
            till_date = request.POST.get('till')
            if from_date and till_date:
                queryset = queryset.filter(date_added__range=[from_date, till_date])
            context["object_list"] = queryset
            return render(request, self.template_name, context)
        return render(request, self.template_name, context)
        
        
@method_decorator(login_required, name='dispatch')
def print_function(request, query_set):
    template_name = "sale/check_template.html"
    context = query_set
    return render(request, template_name, context)

@method_decorator(login_required, name='dispatch')
class SaleDetailView(DetailView):
    template_name = "sale/sale_detail.html"
    model = Sale
    context_object_name = 'sale'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        
        # Fetching sale items
        sale_items = SaleItems.objects.filter(sale=self.object)
        paginator_sale_items = Paginator(sale_items, self.paginate_by)
        page_number_sale_items = self.request.GET.get('page_sale_items')
        page_obj_sale_items = paginator_sale_items.get_page(page_number_sale_items)
        context["page_obj_sale_items"] = page_obj_sale_items
        
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()  # Manually set self.object
        context = self.get_context_data()
        if "edit" in request.POST:
            sale = self.get_object()
            product = request.POST.get("qr_code_id")
            amount = request.POST.get("amount")
            item = request.POST.get("item")
            obj = SaleItems.objects.get(id = item)
            obj.product = Product.objects.get(qr_code_id = product)
            obj.quantity = amount
            obj.save()
            obj_tr = Transaction.objects.create(
                    product = Product.objects.get(qr_code_id = obj.product.qr_code_id),
                    transaction_type = "add",
                    amount = obj.quantity
                )
            obj_tr2 = Transaction.objects.create(
                    product = Product.objects.get(qr_code_id = product),
                    transaction_type = "remove",
                    amount = amount
                )
            return redirect("main_app:sale_detail", pk=sale.pk)
        if "delete" in request.POST:
            sale = self.get_object()
            obj = SaleItems.objects.get(id=request.POST.get("sale"))
            obj_tr = Transaction.objects.create(
                    product = Product.objects.get(id= obj.product.id),
                    transaction_type = "add",
                    amount = obj.quantity
                )
            obj.delete()
            return redirect("main_app:sale_detail", pk=sale.pk)
        if "pdf" in request.POST:
            return print_function(request, context)
        if "add" in request.POST:
            sale = self.get_object()  # Assuming this retrieves the current sale object
            product = Product.objects.get(qr_code_id=request.POST.get("qr_code_id"))
            obj = SaleItems.objects.create(
                quantity = request.POST.get("amount"),
                product = product,
                sale = sale
            )
            obj_tr = Transaction.objects.create(
                    product = product,
                    transaction_type = "remove",
                    amount = request.POST.get("amount")
                )
            return redirect("main_app:sale_detail", pk=sale.pk)


@method_decorator(login_required, name='dispatch')
class StorageView(ListView):
    template_name = "storage/storage.html"
    model = Transaction
    context_object_name = 'products'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetching all products
        objs = []
        for i in Transaction.objects.all():
            pro = {
                "id": i.id,
                "product_id" : i.product.qr_code_id,
                "name" : i.product.name,
                "amount" : sum([ d.amount for d in Transaction.objects.filter(transaction_type = "add").filter(product__qr_code_id = i.product.qr_code_id)]) - sum([ d.amount for d in Transaction.objects.filter(transaction_type = "remove").filter(product__qr_code_id = i.product.qr_code_id)]),
                "sale_price" : i.product.sale_price,
                "base_price" : i.product.base_price,
                "overall" : sum([ d.amount for d in Transaction.objects.filter(transaction_type = "add").filter(product__qr_code_id = i.product.qr_code_id)]) * i.product.base_price,
            }
            objs.append(pro) if pro["product_id"] not in {j["product_id"] for j in objs} else None
        products = objs
        paginator_products = Paginator(products, self.paginate_by)
        page_number_products = self.request.GET.get('page_products')
        page_obj_products = paginator_products.get_page(page_number_products)
        
        context["page_obj_products"] = page_obj_products
        
        return context
    
    def post(self, request):
        if "add" in request.POST:
            amount = request.POST.get("amount")
            product_id = request.POST.get("product_id")
            try:
                product =  Product.objects.get(qr_code_id = product_id)
                obj = Transaction.objects.create(
                    product = product,
                    transaction_type = "add",
                    amount = amount
                )
            except Product.DoesNotExist:
                messages.warning(self.request, "Omborda bu Mahsulot mavjud emas")
        return redirect("main_app:storage")

@method_decorator(login_required, name='dispatch')
class StorageHistoryView(ListView):
    template_name = "storage/transactions.html"
    model = Transaction
    context_object_name = 'transactions'
    paginate_by = 10

    def get_queryset(self):
        return Transaction.objects.all()

    def get_context_data(self):
        context = {}
        
        # Fetching all products
        products = self.get_queryset()
        paginator_products = Paginator(products, self.paginate_by)
        page_number_products = self.request.GET.get('page_products')
        page_obj_products = paginator_products.get_page(page_number_products)
        
        context["page_obj_products"] = page_obj_products
        
        return context
    
    def post(self, request):
        if "add" in request.POST:
            amount = request.POST.get("amount")
            product_id = request.POST.get("product_id")
            try:
                product =  Product.objects.get(qr_code_id = product_id)
                obj = Transaction.objects.create(
                    product = product,
                    transaction_type = "add",
                    amount = amount
                )
            except Product.DoesNotExist:
                messages.warning(self.request, "Omborda bu Mahsulot mavjud emas")
        if 'filtr' in request.POST:
            context = self.get_context_data()
            queryset = self.get_queryset()
            from_date = request.POST.get('from')
            till_date = request.POST.get('till')
            if from_date and till_date:
                queryset = queryset.filter(date__range=[from_date, till_date])
            context["page_obj_products"] = queryset
            return render(request, self.template_name, context)
        return redirect("main_app:storage")

@method_decorator(login_required, name='dispatch')
class ProductsView(ListView):
    template_name = "storage/products.html"
    model = Product
    context_object_name = 'products'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetching all products
        products = Product.objects.all().order_by("-id")
        paginator_products = Paginator(products, self.paginate_by)
        page_number_products = self.request.GET.get('page_products')
        page_obj_products = paginator_products.get_page(page_number_products)
        
        context["page_obj_products"] = page_obj_products
        
        return context
    
    def post(self, request):
        if "delete" in request.POST:
            product = Product.objects.get(id = request.POST.get("product")).delete()
            return redirect("main_app:products")
        if "save" in request.POST:
            name = request.POST.get("name")
            product_id = request.POST.get("product")
            
            qr_code_id = request.POST.get("qr_code_id")
            sale_price = request.POST.get("sale_price")
            base_price = request.POST.get("base_price")
            product = Product.objects.get(id=product_id )
            product.name = name
            product.sale_price = sale_price
            product.base_price = base_price
            product.qr_code_id = qr_code_id
            product.save()
            return redirect("main_app:products")
        if "add" in request.POST:
            name = request.POST.get("name")
            amount = request.POST.get("amount")
            product_id = request.POST.get("product_id")
            sale_price = request.POST.get("sale_price")
            base_price = request.POST.get("base_price")
            try:
                product =  Product.objects.get(qr_code_id = product_id)
                messages.warning(self.request, "Omborda bu Mahsulot mavjud")
            except Product.DoesNotExist:
                obj = Product.objects.create(
                    name = name,
                    sale_price = sale_price,
                    base_price = base_price,
                    qr_code_id  = product_id,
                    amount = amount
                )
                tr = Transaction.objects.create(
                    product = obj,
                    transaction_type = "add",
                    amount = amount
                )
                print(tr)
            return redirect("main_app:products")


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
    

