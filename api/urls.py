from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

# Router auto-generates URL patterns for ViewSets
router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.CategoryViewSet, basename='category')

urlpatterns = [
    path('v1/', include(router.urls)),
]