from django.urls import path

from django.contrib.auth.views import LogoutView
from .views import  (StatisicsView,LoginView, ProvincesView, 
                     ProvinceDetailView, RegionDetailView, SaleView, 
                     SaleDetailView, GetRegionsView, GetShopsView, ShopDetailView, 
                     StorageView, ProductsView,StorageHistoryView,ProductGetView,SaleItemView, DebtView, SaleGetView)

app_name = "main_app"

urlpatterns = [
    path("", StatisicsView.as_view(), name="main"),
    
    path("provinces/", ProvincesView.as_view(), name="provinces"),
    path("province/<int:pk>/regions/", ProvinceDetailView.as_view(), name="province_detail"),
    path("regions/<int:pk>/shops/", RegionDetailView.as_view(), name="region_detail"),
    path('get-regions/', GetRegionsView.as_view(), name='get_regions'),
    path('get-shops/', GetShopsView.as_view(), name='get_shops'),
    
    path("sale/", SaleView.as_view(), name="sale"),
    path("sale/<int:pk>/", SaleDetailView.as_view(), name="sale_detail"),
    path("sale/get/<int:pk>/", SaleGetView.as_view(), name="sale_get"),
    path("sale/item/<int:pk>", SaleItemView.as_view(), name="sale_item_get"),
    path("shop/<int:pk>/", ShopDetailView.as_view(), name="shop_detail"),
  
    
    path("storage/", StorageView.as_view(), name="storage"),
    path("debt/", DebtView.as_view(), name="debt"),
    path("storage/products/", ProductsView.as_view(), name="products"),
    path("storage/history/", StorageHistoryView.as_view(), name="storage_history"),
    path('storage/products/<int:pk>', ProductGetView.as_view(), name='product_get'),
    
    
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]