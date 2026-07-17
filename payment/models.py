from django.db import models
from django.contrib.auth.models import User
from store.models import Product
from django.db.models.signals import post_save

class ShippingAddress(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
	shipping_full_name = models.CharField(max_length=255)
	shipping_email = models.CharField(max_length=255)
	shipping_address1 = models.CharField(max_length=255)
	shipping_address2 = models.CharField(max_length=255, null=True, blank=True)
	shipping_city = models.CharField(max_length=255)
	


	# Don't pluralize address
	class Meta:
		verbose_name_plural = "Shipping Address"

	def __str__(self):
		return f'Shipping Address - {str(self.id)}'

# Create a user Shipping Address by default when user signs up
def create_shipping(sender, instance, created, **kwargs):
	if created:
		user_shipping = ShippingAddress(user=instance)
		user_shipping.save()

# Automate the profile thing
post_save.connect(create_shipping, sender=User)



# Create Order Model
class Order(models.Model):

	class OrderStatus(models.TextChoices):
		PENDING = 'pending', 'Pending'
		CONFIRMED = 'confirmed', 'Confirmed'
		PROCESSING = 'processing', 'Processing'
		SHIPPED = 'shipped', 'Shipped'
		DELIVERED = 'delivered', 'Delivered'
		CANCELLED = 'cancelled', 'Cancelled'
		REFUNDED = 'refunded', 'Refunded'
	# Foreign Key
	user = models.ForeignKey(
		User, on_delete=models.CASCADE, null=True, blank=True,
        related_name='orders'
    )
	full_name = models.CharField(max_length=250)
	email = models.EmailField(max_length=250)
	shipping_address = models.TextField(max_length=15000)
	amount_paid = models.IntegerField(default=0)
	status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True
    )
	date_ordered = models.DateTimeField(auto_now_add=True)	
	date_updated = models.DateTimeField(auto_now=True)
	tracking_number = models.CharField(max_length=100, blank=True, default='')
	notes = models.TextField(blank=True, default='')

	def __str__(self):
		return f'Order #{self.id} - {self.full_name} - {self.get_status_display()}'
	
	@property
	def total_items(self):
		return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

	class Meta:
		ordering = ['-date_ordered']
		indexes = [
            models.Index(fields=['-date_ordered']),
            models.Index(fields=['user', '-date_ordered']),
            models.Index(fields=['status']),
        ]

# Create Order Items Model
class OrderItem(models.Model):
	# Foreign Keys
	order = models.ForeignKey(
		Order, on_delete=models.CASCADE, null=True,
		related_name='items'
	)
	product = models.ForeignKey(
		Product, on_delete=models.CASCADE, null=True,
		related_name='order_items'
	)
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

	quantity = models.PositiveBigIntegerField(default=1)
	price = models.IntegerField(default=0)

	@property
	def subtotal(self):
		return self.price * self.quantity

	def __str__(self):
		return f'Order Item #{self.id} - {self.product.name if self.product else "Deleted"} x{self.quantity}'

	class Meta:
		indexes = [
            models.Index(fields=['order']),
        ]