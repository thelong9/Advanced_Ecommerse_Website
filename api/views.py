# from rest_framwork import generics, viewsets
# from store.models import Product
# from .serializers import ProductListSerializer

# class ProductViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     API endpoint for Products

#     Supports: filtering, searching, ordering, pagination

#     GET api/v1/products/
#     """

#     serializer_class = ProductListSerializer

#     def get_queryset(self):
#         return (
#             Product.objects
#             .filter(is_active=True)
#             .select_related('category') # Optimizing for N+1 queries problem
#             .order_by('-create_at')
#         )


from rest_framework import generics
from store.models import Product
from .serializers import ProductListSerializer


class ProductListAPIView(generics.ListAPIView):
    """
    API endpoint trả về danh sách sản phẩm.

    GET /api/v1/products/list
    - Chỉ trả về sản phẩm đang active
    - Sắp xếp theo ngày tạo mới nhất
    - Hỗ trợ pagination (mặc định 20 items/page)
    """
    serializer_class = ProductListSerializer

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_active=True)
            .select_related('category')  # Tối ưu N+1 query
            .order_by('-created_at')
        )
