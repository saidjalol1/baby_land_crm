from django.contrib import admin
from .models import Shop, Province, Regions, Product, Transaction, Sale

admin.site.register(Province)
admin.site.register(Regions)
admin.site.register(Product)
admin.site.register(Transaction)
admin.site.register(Shop)
admin.site.register(Sale)
