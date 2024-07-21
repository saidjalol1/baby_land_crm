from django.urls import path

from django.contrib.auth.views import LogoutView
from .views import  (StatisicsView,LoginView, ProvincesView, 
                     ProvinceDetailView, RegionDetailView, SaleView, 
                     SaleDetailView, GetRegionsView, GetShopsView)

app_name = "main_app"

urlpatterns = [
    path("", StatisicsView.as_view(), name="main"),
    path("provinces/", ProvincesView.as_view(), name="provinces"),
    path("province/<int:pk>/regions/", ProvinceDetailView.as_view(), name="province_detail"),
    path("regions/<int:pk>/shops/", RegionDetailView.as_view(), name="region_detail"),
    path("sale/", SaleView.as_view(), name="sale"),
    path("sale/<int:pk>/", SaleDetailView.as_view(), name="sale_detail"),
    
    path('get-regions/', GetRegionsView.as_view(), name='get_regions'),
    path('get-shops/', GetShopsView.as_view(), name='get_shops'),
    
    
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]