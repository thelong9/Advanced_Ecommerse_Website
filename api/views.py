"""
API ViewSets — Business logic layer for the REST API.

Design decisions:
- ReadOnlyModelViewSet for products/categories (data comes from crawling, not user input)
- Separate list/detail serializers to optimize payload size
- select_related/prefetch_related to eliminate N+1 queries
- annotate() for computed fields (avg_rating, rating_count)
- Custom actions (@action) for recommendations and ratings
"""

import logging

from django.db.models import Avg, Count, Sum, Q
from django.contrib.auth.models import User

from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from django_filters.rest_framework import DjangoFilterBackend

from store.models import Product, Category, Rating
from payment.models import Order, OrderItem
from cart.cart import Cart

from .serializers import (
    ProductListSerializer, ProductDetailSerializer,
    CategorySerializer,
    RatingSerializer, RatingCreateSerializer,
    OrderListSerializer, OrderDetailSerializer, OrderCreateSerializer,
    UserSerializer, RegisterSerializer, ProfileSerializer,
    OrderItemSerializer,
)
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly
from .pagination import StandardResultsSetPagination, LargeResultsSetPagination

logger = logging.getLogger('api')


# =============================================================================
# PRODUCT API
# =============================================================================

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Products.

    Supports: filtering, searching, ordering, pagination.
    Uses select_related + annotate for query optimization.

    GET /api/v1/products/              — List all products
    GET /api/v1/products/{pk}/         — Product detail
    GET /api/v1/products/{pk}/ratings/ — Product ratings
    GET /api/v1/products/{pk}/recommend/ — Recommended products
    """
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # Đổi category__slug → category__name vì Category chưa có slug
    filterset_fields = ['category__name', 'brand_name', 'is_active']
    search_fields = ['name', 'description', 'brand_name']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
    lookup_field = 'pk'

    def get_queryset(self):
        """
        Optimized queryset:
        - select_related: eliminates N+1 for category
        - annotate: computes avg_rating and rating_count in SQL
        - filter: only active products
        """
        return Product.objects.filter(is_active=True)\
            .select_related('category')\
            .annotate(
                avg_rating=Avg('ratings__rating'),
                rating_count=Count('ratings')
            )

    def get_serializer_class(self):
        """Use lightweight serializer for list, full serializer for detail."""
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer

    @action(detail=True, methods=['get'])
    def ratings(self, request, pk=None):
        """
        GET /api/v1/products/{pk}/ratings/
        List all ratings for a specific product.
        """
        product = self.get_object()
        ratings = Rating.objects.filter(
            product_id=product.tiki_product_id
        ).order_by('-created_at')

        page = self.paginate_queryset(ratings)
        if page is not None:
            serializer = RatingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = RatingSerializer(ratings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def recommend(self, request, pk=None):
        """
        GET /api/v1/products/{pk}/recommend/
        Get recommended products (same category fallback).
        """
        product = self.get_object()
        # Fallback: same category products
        recommended = Product.objects.filter(
            category=product.category, is_active=True
        ).exclude(id=product.id).select_related('category').annotate(
            avg_rating=Avg('ratings__rating'),
            rating_count=Count('ratings')
        )[:8]
        serializer = ProductListSerializer(recommended, many=True)
        return Response(serializer.data)


# =============================================================================
# CATEGORY API
# =============================================================================

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Categories.

    GET /api/v1/categories/          — List all categories
    GET /api/v1/categories/{pk}/     — Category detail
    """
    serializer_class = CategorySerializer
    pagination_class = None  # Categories are few, no need for pagination

    def get_queryset(self):
        return Category.objects.annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).order_by('name')


# =============================================================================
# ORDER API
# =============================================================================

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Orders.

    GET    /api/v1/orders/        — List user's orders
    POST   /api/v1/orders/        — Create new order
    GET    /api/v1/orders/{pk}/   — Order detail
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users can only see their own orders."""
        return Order.objects.filter(user=self.request.user)\
            .prefetch_related('items__product')\
            .annotate(total_items=Sum('items__quantity'))

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderDetailSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new order from the user's cart.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = Cart(request)
        cart_products = cart.get_prods()
        quantities = cart.get_quants()
        total = cart.cart_total()

        if not cart_products:
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build shipping address string
        data = serializer.validated_data
        shipping_address = (
            f"{data['shipping_address1']}\n"
            f"{data.get('shipping_address2', '')}\n"
            f"{data['shipping_city']}"
        )

        # Create Order
        order = Order.objects.create(
            user=request.user,
            full_name=data['shipping_full_name'],
            email=data['shipping_email'],
            shipping_address=shipping_address,
            amount_paid=total,
            status=Order.OrderStatus.CONFIRMED,
        )

        # Create OrderItems
        for product in cart_products:
            qty = quantities.get(str(product.id), 1)
            OrderItem.objects.create(
                order=order,
                product=product,
                user=request.user,
                quantity=qty,
                price=product.price,
            )

        logger.info('API Order #%d created for user %s', order.id, request.user)

        # Return the created order
        output_serializer = OrderDetailSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


# =============================================================================
# AUTH API
# =============================================================================

class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Register a new user account.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info('New user registered via API: %s', user.username)
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET/PUT /api/v1/auth/profile/
    View or update the authenticated user's profile.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
