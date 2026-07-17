"""
Custom pagination classes for the API.

StandardResultsSetPagination: Default pagination with configurable page size.
LargeResultsSetPagination: For endpoints that need larger page sizes.
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Default pagination: 20 items per page, max 100.
    Supports ?page_size=N query parameter for client-controlled page sizes.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    """For endpoints where larger result sets are appropriate (e.g., admin dashboards)."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
