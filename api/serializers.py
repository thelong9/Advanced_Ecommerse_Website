from rest_framework import serializers
from store.models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category - used for nested field in Product"""

    class Meta: 
        model = Category
        fields = ['id', 'name']

class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for Product - list"""

    category = CategorySerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'tiki_product_id',
            'name',
            'price',
            'category',
            'image',
            'brand_name',
            'is_active',
            # 'avg_rating', 
            # 'rating_count',
        ]