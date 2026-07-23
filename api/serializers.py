from rest_framework import serializers
from store.models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category - used for nested field in Product"""

    product_count = serializers.IntegerField(read_only=True)

    class Meta: 
        model = Category
        fields = ['id', 'name', 'product_count']

class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for Product - list"""

    # Parameter "source": take string input only
    # Field "category.name": take field "category" in class Product
    category_name = serializers.CharField(source='category.name', read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'tiki_product_id',
            'name',
            'price',
            'category_name',
            'image',
            'brand_name',
            'is_active',
            'avg_rating', 
            'rating_count',
        ]

class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for Product - details"""
    
    category = CategorySerializer(read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)


    class Meta:
        model = Product
        fields = [
            'tiki_product_id', 
            'name',
            'price',
            'category', 
            'description', 
            'image',
            'brand_id', 
            'brand_name', 
            'is_active',
            'avg_rating', 
            'rating_count', 
            'created_at', 
            'updated_at',
        ]