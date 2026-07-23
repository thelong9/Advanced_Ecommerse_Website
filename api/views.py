from rest_framework import generics, viewsets
from store.models import Product, Category
from django.db.models import Avg, Count, Sum, Q
from .serializers import ProductListSerializer, ProductDetailSerializer, CategorySerializer

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Products

    Supports: filtering, searching, ordering, pagination

    GET api/v1/products/
    GET api/v1/products/{pk}
    """

    lookup_field = 'pk'

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_active=True)
            .select_related('category') # Optimizing for N+1 queries problem
            .annotate(
                avg_rating=Avg('ratings__rating'),
                rating_count=Count('ratings')
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Categories

    GET api/v1/categories/
    """

    serializer_class = CategorySerializer

    def get_queryset(self):
        return (
            Category.objects
            .annotate(
                product_count=Count('products', filter=Q(products__is_active=True))
            )
        )



