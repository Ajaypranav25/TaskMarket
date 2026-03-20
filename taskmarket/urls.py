from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # Google OAuth + allauth internals
    path("accounts/", include("allauth.urls")),
    # Project routes
    path("", include("core.urls")),
]