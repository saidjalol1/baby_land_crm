from django.contrib import admin
from .models import Shop, Province, Regions, Product, Transaction

admin.site.register(Province)
admin.site.register(Regions)
admin.site.register(Product)
admin.site.register(Transaction)
admin.site.register(Shop)
