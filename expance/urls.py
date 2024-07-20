from django.urls import path
from .views import ExpanceView
app_name = "expance_app"

urlpatterns = [
    path("", ExpanceView.as_view(), name="expance")
]