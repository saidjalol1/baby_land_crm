from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("main_app.urls", namespace="main_app")),
    path("expance", include("expance.urls", namespace="expance_app"))
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
