"""
URL configuration for smart_warehouse project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    equipment_page,
    error_501,
    error_503,
    index,
    inventory_page,
    issue_page,
    login_page,
    notifications_page,
    profile_page,
    reports_page,
    return_page,
    session_login,
    session_logout,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('smart_warehouse.api_urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/login/', session_login, name='session_login'),
    path('auth/logout/', session_logout, name='session_logout'),
    path('', index, name='index'),
    path('equipment/', equipment_page, name='equipment'),
    path('issue/', issue_page, name='issue'),
    path('return/', return_page, name='return'),
    path('inventory/', inventory_page, name='inventory'),
    path('reports/', reports_page, name='reports'),
    path('notifications/', notifications_page, name='notifications'),
    path('login/', login_page, name='login'),
    path('profile/', profile_page, name='profile'),
    path('501/', error_501, name='error_501'),
    path('503/', error_503, name='error_503'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'smart_warehouse.views.error_403'
handler404 = 'smart_warehouse.views.error_404'
handler500 = 'smart_warehouse.views.error_500'
