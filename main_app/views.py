from typing import Any
import datetime
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
from .models import Province, Regions, Sale, Shop, Product, SaleItems, Transaction, Payments, Barcodes
from django.contrib import messages
from print_funcs.pdf_generator import generate_pdf, generate_check_pdf
import pdfkit
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db.models import Sum
import calendar
import json

from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404


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
        context["debt"] = sum([ i.debt for i in sale_items])
        return context

    def post(self, request, *args, **kwargs):
        if "save" in request.POST:
            sale = Sale.objects.get(id = request.POST.get("sale"))
            if sale.get_amount() > 0:
                sale.payment = request.POST.get("payment")
                sale.debt = sale.get_amount() - int( request.POST.get("payment"))
                sale.save()
            else:
                return redirect("main_app:shop_detail",  pk=self.kwargs["pk"])
            return redirect("main_app:shop_detail",  pk=self.kwargs["pk"])
    
    
@method_decorator(login_required, name='dispatch')
class StatisicsView(View):
    template = "index.html"
    
    def get_context_data(self, **kwargs):
        this_month = datetime.datetime.now().month
        sale_items = SaleItems.objects.filter(sale__date_added__month=this_month)

        months = list(range(1, 13))
        sales = [0] * 12  # Initialize sales for each month with 0

        # Calculate sales for each month
        sales_by_month = SaleItems.objects.values('sale__date_added__month').annotate(total_sales=Sum('quantity'))
        for sale in sales_by_month:
            sales[sale['sale__date_added__month'] - 1] = sale['total_sales']

        month_names = [calendar.month_name[i] for i in months]

        most_sold_product = sale_items.values('product__name').annotate(total_quantity=Sum('quantity')).order_by('-total_quantity').first()
        most_bought_shop = Sale.objects.filter(date_added__month=this_month).values('shop__name').annotate(total_sales=Sum('items__quantity')).order_by('-total_sales').first()
        
        context = {
            "sale_month": sum([i.get_amount() for i in SaleItems.objects.filter(sale__date_added__month=this_month)]),
            "income_month": sum([i.get_income() for i in SaleItems.objects.filter(sale__date_added__month=this_month)]),
            "most_sold_product": most_sold_product['product__name'] if most_sold_product else None,
            "most_sold_quantity": most_sold_product['total_quantity'] if most_sold_product else 0,
            "most_bought_shop": most_bought_shop['shop__name'] if most_bought_shop else None,
            "most_bought_sales": most_bought_shop['total_sales'] if most_bought_shop else 0,
            "month_names": json.dumps(month_names),
            "sales": json.dumps(sales),
        }
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
        sale_items = Sale.objects.all().order_by("-id")
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
        if "save" in request.POST:
            sale = Sale.objects.get(id = request.POST.get("sale"))
            sale.payment = request.POST.get("payment")
            sale.debt = sale.get_amount() - int( request.POST.get("payment"))
            sale.save()
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
            sale = self.get_object()
            amount = request.POST.get("amount")
            product = Product.objects.get(qr_code_id=request.POST.get("qr_code_id"))
            overall_amount = sum([ d.amount for d in Transaction.objects.filter(transaction_type = "add").filter(product__qr_code_id = product.qr_code_id)]) - sum([ d.amount for d in Transaction.objects.filter(transaction_type = "remove").filter(product__qr_code_id = product.qr_code_id)])
            if overall_amount - int(amount) > 0:
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
            else:
                messages.warning(request, "Omborda yetarli mahsulot mavjud emas")
            return redirect("main_app:sale_detail", pk=sale.pk)

@method_decorator(login_required, name='dispatch')
class StorageView(ListView):
    template_name = "storage/storage.html"
    model = Transaction
    context_object_name = 'products'
    paginate_by = 10


    def get_queryset(self):
        # Return an empty queryset or the queryset you want
        return Transaction.objects.none()
    
    def get_context_data(self, **kwargs):
        context = {}
        
        # Fetching all products
        objs = []
        if "search" in self.request.GET:
            obj = Transaction.objects.filter(product__qr_code_id = self.request.GET.get("query")).order_by("-id")
            print(self.request.GET.get("query"))
            pro = {}
            if obj:
                pro = {
                    "id": obj.last().id,
                    "product_id" : obj.last().product.qr_code_id,
                    "name" : obj.last().product.name,
                    "amount" : sum([ d.amount for d in Transaction.objects.filter(transaction_type = "add").filter(product__qr_code_id = obj.last().product.qr_code_id)]) - sum([ d.amount for d in Transaction.objects.filter(transaction_type = "remove").filter(product__qr_code_id = obj.last().product.qr_code_id)]),
                    "sale_price" : obj.last().product.sale_price,
                    "base_price" : obj.last().product.base_price,
                    "overall" : (sum([ d.amount for d in Transaction.objects.filter(transaction_type = "add").filter(product__qr_code_id = obj.last().product.qr_code_id)]) * obj.last().product.base_price) - sum([ d.amount for d in Transaction.objects.filter(transaction_type = "remove").filter(product__qr_code_id = obj.last().product.qr_code_id)]) * obj.last().product.base_price,
                }
            objs.append(pro)
        else:
                for i in Transaction.objects.all().order_by("-id"):
                    pro = {
                        "id": i.id,
                        "product_id" : i.product.qr_code_id,
                        "name" : i.product.name,
                        "amount" : sum([ d.amount for d in Transaction.objects.filter(transaction_type = "add").filter(product__qr_code_id = i.product.qr_code_id)]) - sum([ d.amount for d in Transaction.objects.filter(transaction_type = "remove").filter(product__qr_code_id = i.product.qr_code_id)]),
                        "sale_price" : i.product.sale_price,
                        "base_price" : i.product.base_price,
                        "overall" : (sum([ d.amount for d in Transaction.objects.filter(transaction_type = "add").filter(product__qr_code_id = i.product.qr_code_id)]) * i.product.base_price) - sum([ d.amount for d in Transaction.objects.filter(transaction_type = "remove").filter(product__qr_code_id = i.product.qr_code_id)]) * i.product.base_price,
                    }
                    objs.append(pro) if pro["product_id"] not in {j["product_id"] for j in objs} else None
        products = objs
        paginator_products = Paginator(products, self.paginate_by)
        page_number_products = self.request.GET.get('page_products')
        page_obj_products = paginator_products.get_page(page_number_products)
        
        
        payment_objs = []
        for i in Payments.objects.all().order_by("-id"):
            p_obj = {
                "id": i.id,
                "amount" : i.amount,
                "date" : i.date,
            }
            payment_objs.append(p_obj) if p_obj["id"] not in {j["id"] for j in payment_objs} else None
        payments = payment_objs
        paginator_payments = Paginator(payments, self.paginate_by)
        page_number_payments = self.request.GET.get('page_payments')
        page_obj_payments = paginator_payments.get_page(page_number_payments)
        
        context["page_obj_products"] = page_obj_products
        context["payments"] = page_obj_payments
        try:
            if objs[0]:
                context["balance"] = sum([ i["overall"] for i in objs]) - sum([ i["amount"] for i in payments])
        except Exception as e:
            pass
        return context
    
    def post(self, request):
        context = self.get_context_data()
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
        if "add_payment" in request.POST:
            amount = request.POST.get("amount")
            date = request.POST.get("date")
            try:
                payment =  Payments.objects.create(
                    amount = amount,
                    date = date
                )
                messages.success(request, "To'lov qo'shildi")
            except Exception as e:
                messages.warning(self.request, e)
                
        if "search" in request.POST:
            try:
                obj = Transaction.objects.filter(product__qr_code_id = request.POST.get("search"))
                for i in obj:
                    tr = {
                        "id": i.id,
                        "product_id" : i.product.qr_code_id,
                        "name" : i.product.name,
                        "amount" : sum([ d.amount for d in Transaction.objects.filter(transaction_type = "add").filter(product__qr_code_id = i.product.qr_code_id)]) - sum([ d.amount for d in Transaction.objects.filter(transaction_type = "remove").filter(product__qr_code_id = i.product.qr_code_id)]),
                        "sale_price" : i.product.sale_price,
                        "base_price" : i.product.base_price,
                        "overall" : (sum([ d.amount for d in Transaction.objects.filter(transaction_type = "add").filter(product__qr_code_id = i.product.qr_code_id)]) * i.product.base_price) - sum([ d.amount for d in Transaction.objects.filter(transaction_type = "remove").filter(product__qr_code_id = i.product.qr_code_id)]) * i.product.base_price,
                    }
                if tr.amount > 0:
                    context["page_obj_products"] = tr
                    return self.render_to_response(context)
            except Transaction.DoesNotExist:
                messages.success(request, "Omborda Mahsulot mavjud emas")
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
    
@method_decorator(login_required, name='dispatch')
class Barcode(ListView):
    template_name = "qr_codes.html"
    model = Barcodes
    context_object_name = 'codes'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = {}
        
        # Fetching all products
        objs = []
        if "search" in self.request.GET:
            for i in Barcodes.objects.filter(number__icontains = self.request.GET.get("query")).order_by("-id"):
                pro = {
                    "id": i.id,
                    "number" : i.number
                }
                objs.append(pro) if pro["id"] not in {j["id"] for j in objs} else None
        else:
            for i in Barcodes.objects.all().order_by("-id"):
                pro = {
                    "id": i.id,
                    "number" : i.number
                }
                objs.append(pro) if pro["id"] not in {j["id"] for j in objs} else None
        products = objs
        paginator_products = Paginator(products, self.paginate_by)
        page_number_products = self.request.GET.get('page_products')
        page_obj_products = paginator_products.get_page(page_number_products)
    
        context["page_obj_products"] = page_obj_products
        return context
    
    def post(self, request):
        if "add" in request.POST:
            number = request.POST.get("ID")
            try:
                product =  Barcodes.objects.get(number = number)
                messages.warning(self.request, "Omborda bu barcode mavjud")
            except Barcodes.DoesNotExist:
                product =  Barcodes.objects.create(number = number)
                return redirect("main_app:barcode")
        if "delete" in request.POST:
            number = request.POST.get("ID")
            product =  Barcodes.objects.get(id = number)
            product.delete()
        return redirect("main_app:barcode")
    

@method_decorator(login_required, name='dispatch')
class SettingsView(View):
    template_name = "settings.html"
    def get(self, request):
        context = {}
        context["provinces"] = Province.objects.all()
        return render(request, self.template_name, context)
    
    def post(self, request):
        if "add" in request.POST:
            region = Regions.objects.get(id = request.POST.get("region"))
            shop_name = request.POST.get("name")
            shop_surname = request.POST.get("surname")
            shop =  Shop.objects.create(name = shop_name, last_name = shop_surname, region = region)
            messages.success(request, f"{shop_name}{shop_surname}- klient muvoffaqiyatli qo'shildi")
            
        if "addregion" in request.POST:
            province = Province.objects.get(id = request.POST.get("province"))
            region_name = request.POST.get("region_name")
            shop =  Regions.objects.create(name = region_name,  province = province)
            messages.success(request, f"{region_name} muvoffaqiyatli qo'shildi")
        return redirect("main_app:settings_app")

def barcode_image(request, barcode_id):
    barcode = get_object_or_404(Barcodes, pk=barcode_id)

    if not barcode.barcode_image:
        raise Http404("Barcode image does not exist.")

    # Open the image file
    with barcode.barcode_image.open('rb') as f:
        response = HttpResponse(f.read(), content_type='image/png')
        response['Content-Disposition'] = f'inline; filename="{barcode.number}.png"'
        return response