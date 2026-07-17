"""
API Serializers — Data serialization and validation layer.

Design decisions:
- Separate List/Detail serializers for performance (list view doesn't need all fields)
- Nested serializers for related data
- Custom validation with error messages
- Read-only computed fields (avg_rating)
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from store.models import Product, Category, Profile, Rating
from payment.models import Order, OrderItem


# =============================================================================
# AUTH SERIALIZERS
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Public user representation — never expose sensitive data."""

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username']


class RegisterSerializer(serializers.ModelSerializer):
    """User registration with password confirmation."""
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name',
                  'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({
                'password2': 'Passwords do not match.'
            })
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'phone', 'address1', 'address2', 'city']


# =============================================================================
# CATEGORY SERIALIZERS
# =============================================================================

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        # Bỏ 'slug' vì Category model chưa có field slug
        fields = ['id', 'name', 'product_count']


# =============================================================================
# RATING SERIALIZERS
# =============================================================================

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'customer_name', 'rating', 'title', 'created_at']
        read_only_fields = ['id', 'created_at']


class RatingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new rating."""

    class Meta:
        model = Rating
        fields = ['rating', 'title']

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value


# =============================================================================
# PRODUCT SERIALIZERS
# =============================================================================

class ProductListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for product list views.
    Only includes essential fields for performance.
    Computed fields (avg_rating, rating_count) come from queryset annotations.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)
    # Bỏ discount_percent, is_on_sale vì Product chưa có original_price

    class Meta:
        model = Product
        # Bỏ slug, original_price, discount_percent, is_on_sale, stock
        # vì Product model hiện tại chưa có các field này
        fields = [
            'id', 'name', 'price',
            'image', 'category_name', 'brand_name',
            'avg_rating', 'rating_count',
            'is_active',
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for product detail view.
    Includes nested category and ratings.
    """
    category = CategorySerializer(read_only=True)
    ratings = RatingSerializer(many=True, read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)
    # Bỏ discount_percent, is_on_sale, recommended_products

    class Meta:
        model = Product
        # Bỏ slug, original_price, discount_percent, is_on_sale, stock,
        # recommended_products vì chưa có các field/Redis cache tương ứng
        fields = [
            'id', 'tiki_product_id', 'name',
            'price',
            'category', 'description', 'image',
            'brand_id', 'brand_name', 'is_active',
            'avg_rating', 'rating_count', 'ratings',
            'created_at', 'updated_at',
        ]


# =============================================================================
# ORDER SERIALIZERS
# =============================================================================

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.CharField(source='product.image', read_only=True)
    # Dùng IntegerField vì price trong model là IntegerField
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_image',
            'quantity', 'price', 'subtotal',
        ]
        read_only_fields = ['id', 'price']


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight order serializer for list views."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'full_name', 'amount_paid', 'status',
            'status_display', 'total_items', 'date_ordered',
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full order serializer with items."""
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'full_name', 'email', 'shipping_address',
            'amount_paid', 'status', 'status_display',
            'tracking_number', 'notes',
            'total_items', 'items',
            'date_ordered', 'date_updated',
        ]


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating a new order from the cart."""
    shipping_full_name = serializers.CharField(max_length=250)
    shipping_email = serializers.EmailField()
    shipping_address1 = serializers.CharField(max_length=255)
    shipping_address2 = serializers.CharField(max_length=255, required=False, default='')
    shipping_city = serializers.CharField(max_length=255)

    def validate_shipping_email(self, value):
        if not value:
            raise serializers.ValidationError('Email is required.')
        return value
