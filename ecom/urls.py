from django.contrib import admin
from django.urls import path, include
from . import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Template-based views (existing frontend)
    path('', include('store.urls')),
    path('cart/', include('cart.urls')),
    path('payment/', include('payment.urls')),

    # REST API (versioned)
    path('api/v1/', include('api.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
