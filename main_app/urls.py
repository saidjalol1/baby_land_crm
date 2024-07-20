from django.urls import path

from django.contrib.auth.views import LogoutView
from .views import  StatisicsView,LoginView, ProvincesView, ProvinceDetailView, RegionDetailView

app_name = "main_app"

urlpatterns = [
    path("", StatisicsView.as_view(), name="main"),
    path("provinces/", ProvincesView.as_view(), name="provinces"),
    path("province/<int:pk>/regions/", ProvinceDetailView.as_view(), name="province_detail"),
    path("regions/<int:pk>/shops/", RegionDetailView.as_view(), name="region_detail"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]