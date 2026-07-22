from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('v1/products/list', views.ProductListAPIView.as_view(), name='product-list'),
]