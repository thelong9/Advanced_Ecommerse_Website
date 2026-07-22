from django.db import models
import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save

# Categories of Products
class Category(models.Model):
	name = models.CharField(max_length=50, db_index=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	# slug = models.SlugField(max_length=100, unique=True)  # SEO-friendly URL

	# def save(self, *args, **kwargs):
	# 	if not self.slug:
	# 		self.slug = slugify(self.name)
	# 	super().save(*args, **kwargs)

	def __str__(self):
		return self.name
		
	class Meta:
		verbose_name_plural = 'categories'
		ordering = ['name']


# Create Customer Profile
class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	date_modified = models.DateTimeField(auto_now=True)
	phone = models.CharField(max_length=20, blank=True)
	address1 = models.CharField(max_length=200, blank=True)
	address2 = models.CharField(max_length=200, blank=True)
	city = models.CharField(max_length=200, blank=True)	
	old_cart = models.CharField(max_length=200, blank=True, null=True)

	def __str__(self):
		return self.user.username
	
	# class Meta:
		# Remove because OneToOneField automatically has unique index
		# indexes = [
        # 	models.Index(fields=['user']),
        # ]

# Create a user Profile by default when user signs up
def create_profile(sender, instance, created, **kwargs):
	if created:
		user_profile = Profile(user=instance)
		user_profile.save()

# Automate the profile thing
post_save.connect(create_profile, sender=User)


# All of our Products
class Product(models.Model):
	tiki_product_id = models.IntegerField(unique=True, default=0)
	name = models.CharField(max_length=255, db_index=True)
	price = models.IntegerField(default=0)
	category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1, related_name='products')
	description = models.CharField(max_length=250, default='', blank=True, null=True)
	image = models.CharField(max_length=255)
	brand_id = models.IntegerField(default=0)
	brand_name = models.CharField(max_length=100, default='', db_index=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	# Note
	is_active = models.BooleanField(default=True, db_index=True)
	# Add Sale Stuff

	# def save(self, *args, **kwargs):
	# 	if not self.slug:
	# 		base_slug = slugify(self.name)
    #         # Ensure uniqueness by appending tiki_product_id
    #         self.slug = f"{base_slug}-{self.tiki_product_id}" if base_slug else f"product-{self.tiki_product_id}"
    #     super().save(*args, **kwargs)
	

	def __str__(self):
		# return self.name + ' - \n' + str(self.price) + ' - \n' + self.category.name+ ' - \n' + self.description + ' - \n' + self.image + ' - \n' + str(self.tiki_product_id)
		return self.name


class Rating(models.Model):
	product= models.ForeignKey(
		Product, on_delete=models.CASCADE, 
		to_field='tiki_product_id', related_name='ratings')
	title = models.CharField(max_length=100, default='')
	customer_id = models.IntegerField(default=0)
	rating = models.IntegerField(default=0)
	customer_name = models.CharField(max_length=100, default='')
	created_at = models.DateTimeField(auto_now_add=True, null=True)

	def __str__(self):
		return f"{self.customer_name}: {self.rating}/5 - {self.product}"

	# class Meta:
	# 	# Allow each customer can only rate a product once
	# 	constraints = [
	# 		models.UniqueConstraint(
	# 			fields=['product', 'customer_id'], # (product, customer_id) has to be unique
	# 			name='unique_customer_product_rating'
	# 		)
	# 	]
	
#Thêm rating và nối lại cho id sản phẩm match với id sp trong rating