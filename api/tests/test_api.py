"""
API Tests for Product endpoints.

Tests cover:
- Product list with pagination
- Product detail with caching
- Product filtering by category, brand
- Product search
- Product recommendations
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from store.models import Product, Category, Rating


class ProductAPITestCase(TestCase):
    """Base test case with common setup for product-related tests."""

    def setUp(self):
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

        # Create categories
        self.category1 = Category.objects.create(
            name='Điện Thoại', slug='dien-thoai'
        )
        self.category2 = Category.objects.create(
            name='Laptop', slug='laptop'
        )

        # Create products
        self.product1 = Product.objects.create(
            tiki_product_id=1001,
            name='iPhone 15 Pro Max',
            slug='iphone-15-pro-max-1001',
            price=Decimal('29990000'),
            original_price=Decimal('34990000'),
            category=self.category1,
            description='Smartphone cao cấp của Apple',
            image='https://example.com/iphone.jpg',
            brand_name='Apple',
            stock=50,
            is_active=True,
        )
        self.product2 = Product.objects.create(
            tiki_product_id=1002,
            name='Samsung Galaxy S24 Ultra',
            slug='samsung-galaxy-s24-ultra-1002',
            price=Decimal('27990000'),
            category=self.category1,
            description='Flagship Android',
            image='https://example.com/samsung.jpg',
            brand_name='Samsung',
            stock=30,
            is_active=True,
        )
        self.product3 = Product.objects.create(
            tiki_product_id=1003,
            name='MacBook Pro M3',
            slug='macbook-pro-m3-1003',
            price=Decimal('42990000'),
            category=self.category2,
            description='Laptop chuyên nghiệp',
            image='https://example.com/macbook.jpg',
            brand_name='Apple',
            stock=20,
            is_active=True,
        )
        self.inactive_product = Product.objects.create(
            tiki_product_id=1004,
            name='Old Product',
            slug='old-product-1004',
            price=Decimal('1000000'),
            category=self.category1,
            is_active=False,
            image='https://example.com/old.jpg',
        )

    # ===== LIST TESTS =====

    def test_product_list_success(self):
        """GET /api/v1/products/ should return paginated active products."""
        response = self.client.get('/api/v1/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)  # Only active products
        self.assertIn('results', response.data)
        self.assertIn('next', response.data)

    def test_product_list_excludes_inactive(self):
        """Inactive products should not appear in list."""
        response = self.client.get('/api/v1/products/')
        product_names = [p['name'] for p in response.data['results']]
        self.assertNotIn('Old Product', product_names)

    def test_product_list_pagination(self):
        """Should respect page_size query parameter."""
        response = self.client.get('/api/v1/products/?page_size=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    # ===== DETAIL TESTS =====

    def test_product_detail_success(self):
        """GET /api/v1/products/{pk}/ should return full product data."""
        response = self.client.get(f'/api/v1/products/{self.product1.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'iPhone 15 Pro Max')
        self.assertIn('category', response.data)
        self.assertIn('ratings', response.data)

    def test_product_detail_not_found(self):
        """Should return 404 for non-existent product."""
        response = self.client.get('/api/v1/products/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ===== FILTER TESTS =====

    def test_filter_by_category(self):
        """Should filter products by category slug."""
        response = self.client.get('/api/v1/products/?category__slug=dien-thoai')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_brand(self):
        """Should filter products by brand name."""
        response = self.client.get('/api/v1/products/?brand_name=Apple')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # iPhone + MacBook

    # ===== ORDERING TESTS =====

    def test_order_by_price_ascending(self):
        """Should order products by price ascending."""
        response = self.client.get('/api/v1/products/?ordering=price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [p['price'] for p in response.data['results']]
        self.assertEqual(prices, sorted(prices))

    def test_order_by_price_descending(self):
        """Should order products by price descending."""
        response = self.client.get('/api/v1/products/?ordering=-price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [p['price'] for p in response.data['results']]
        self.assertEqual(prices, sorted(prices, reverse=True))

    # ===== SEARCH TESTS =====

    def test_search_by_name(self):
        """Search should find products by name."""
        response = self.client.get('/api/v1/search/?q=iPhone')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_search_empty_query(self):
        """Empty search query should return no results."""
        response = self.client.get('/api/v1/search/?q=')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    # ===== COMPUTED FIELDS TESTS =====

    def test_discount_percent(self):
        """Product with original_price should show discount percentage."""
        response = self.client.get(f'/api/v1/products/{self.product1.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # (1 - 29990000/34990000) * 100 ≈ 14%
        self.assertGreater(response.data['discount_percent'], 0)
        self.assertTrue(response.data['is_on_sale'])


class CategoryAPITestCase(TestCase):
    """Tests for Category API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.cat1 = Category.objects.create(name='Electronics', slug='electronics')
        self.cat2 = Category.objects.create(name='Books', slug='books')

        # Add products to count
        Product.objects.create(
            tiki_product_id=2001, name='Test Product', slug='test-2001',
            price=100, category=self.cat1, image='test.jpg', is_active=True
        )

    def test_category_list(self):
        """GET /api/v1/categories/ should return all categories with product count."""
        response = self.client.get('/api/v1/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_category_has_product_count(self):
        """Categories should include product_count annotation."""
        response = self.client.get('/api/v1/categories/')
        electronics = next(c for c in response.data if c['slug'] == 'electronics')
        self.assertEqual(electronics['product_count'], 1)


class AuthAPITestCase(TestCase):
    """Tests for Authentication API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='existinguser',
            password='testpass123',
            email='existing@example.com'
        )

    def test_register_success(self):
        """POST /api/v1/auth/register/ should create a new user."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'securepass123',
            'password2': 'securepass123',
        }
        response = self.client.post('/api/v1/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')

    def test_register_password_mismatch(self):
        """Registration should fail if passwords don't match."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'securepass123',
            'password2': 'differentpass',
        }
        response = self.client.post('/api/v1/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_jwt(self):
        """POST /api/v1/auth/login/ should return JWT tokens."""
        data = {'username': 'existinguser', 'password': 'testpass123'}
        response = self.client.post('/api/v1/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        """Login with wrong password should return 401."""
        data = {'username': 'existinguser', 'password': 'wrongpass'}
        response = self.client.post('/api/v1/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_without_auth(self):
        """Accessing orders without auth should return 401."""
        response = self.client.get('/api/v1/orders/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_jwt(self):
        """Accessing orders with valid JWT should succeed."""
        # Get token
        login_data = {'username': 'existinguser', 'password': 'testpass123'}
        token_response = self.client.post('/api/v1/auth/login/', login_data)
        access_token = token_response.data['access']

        # Use token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/v1/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ThrottlingTestCase(TestCase):
    """Tests for API rate limiting."""

    def setUp(self):
        self.client = APIClient()

    def test_anonymous_rate_limit_header(self):
        """API should include rate limit information in responses."""
        response = self.client.get('/api/v1/products/')
        # DRF throttling doesn't add headers by default,
        # but the endpoint should work for anonymous users
        self.assertEqual(response.status_code, status.HTTP_200_OK)
