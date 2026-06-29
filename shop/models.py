import datetime
import os
import uuid
from datetime import timedelta

from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import get_object_or_404, render


# --- Helper Functions ---
def getFileName(instance, filename):
    """Generates a unique filename using timestamp to avoid conflicts.
    Replaced ':' with '-' for cross-OS filename compatibility."""
    now_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"{now_time}_{filename}"
    return os.path.join('uploads/', new_filename)


# --- Models ---

class DeliveryPincode(models.Model):
    pincode = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.pincode


class Catagory(models.Model):  # Fixed spelling from 'Catagory'
    name = models.CharField(max_length=150, null=False, blank=False)
    image = CloudinaryField('image', upload_preset='gokulraj')
    description = models.TextField(max_length=500, null=False, blank=False)
    status = models.BooleanField(default=False, help_text="0-Show, 1-Hidden")
    trending = models.BooleanField(default=False, help_text="0-Default, 1-Trending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
    

class Product(models.Model):
    category = models.ForeignKey(Catagory, on_delete=models.CASCADE)
    name = models.CharField(max_length=150, null=False, blank=False)
    vendor = models.CharField(max_length=150, null=False, blank=False)
    product_image = CloudinaryField('image', folder='products/', blank=True, null=True)
    quantity = models.IntegerField(null=False, blank=False)
    original_price = models.FloatField(null=False, blank=False)
    selling_price = models.FloatField(null=False, blank=False)
    description = models.TextField(max_length=500, null=False, blank=False)
    status = models.BooleanField(default=False, help_text="0-Show, 1-Hidden")
    trending = models.BooleanField(default=False, help_text="0-Default, 1-Trending")
    created_at = models.DateTimeField(auto_now_add=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    delivery_charge = models.IntegerField(default=0, help_text="ENTER YOUR DELIVERY CHARGES AMOUNT (0 is Free Delivery)")
    about_this_item = models.TextField(max_length=2000, null=True, blank=True, help_text=" WRITE THE POINTS TAP ENTER.")

    def __str__(self):
        return self.name
        
    
    class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
    image = CloudinaryField('image', folder='product_gallery/')
    video = CloudinaryField('video', folder='product_videos/', blank=True, null=True)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='gallery'
    )
    image = models.ImageField(upload_to='product_gallery/')
    video = models.FileField(upload_to='product_videos/', null=True, blank=True)

# models.py
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    terms_accepted = models.BooleanField(default=False)
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile') # இந்த related_name ரொம்ப முக்கியம்


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_qty = models.IntegerField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_cost(self):
        return self.product_qty * self.product.selling_price


class Favourite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Order(models.Model):
    PAYMENT_CHOICES = (
        ('COD', 'Cash On Delivery'),
        ('UPI', 'UPI Payment'),
    )

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Packed', 'Packed'),
        ('Shipped', 'Shipped'),
        ('Out For Delivery', 'Out For Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Removed duplicate line
    order_number = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    email = models.CharField(max_length=150)
    phone = models.CharField(max_length=150)
    address = models.TextField()
    pincode = models.CharField(max_length=150)
    total_amount = models.FloatField(null=True)  
    payment_mode = models.CharField(max_length=150, default="UPI")
    payment_id = models.CharField(max_length=250, null=True, blank=True, help_text="ENTER YOUR REF NO / Transaction ID")
    payment_screenshot = models.ImageField(upload_to='orders/screenshots/', null=True, blank=True, help_text="PAYMENT SCREENSHOT")
    order_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    customer_signature = models.ImageField(upload_to='signatures/customer/', null=True, blank=True)
    admin_signature = models.ImageField(upload_to='signatures/admin/', null=True, blank=True)
    store_seal = models.ImageField(upload_to='seals/', null=True, blank=True)
    is_digitally_verified = models.BooleanField(default=False)
    signed_invoice_image = models.ImageField(upload_to='signed_invoices/', null=True, blank=True)
    is_digitally_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = "ORD" + str(uuid.uuid4().hex[:10]).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number or "New Order"


class OrderItem(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()
    status = models.CharField(max_length=150, choices=STATUS_CHOICES, default='Pending')
    # Removed redundant payment_mode and transaction_id fields (handled by Order parent model)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField()
    review_image = models.ImageField(upload_to='reviews/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# --- Views ---

def orderdetails(request, oid):
    # Safer than Order.objects.get() - returns a 404 page instead of a 500 error code if order is missing
    order = get_object_or_404(Order, id=oid, user=request.user)
    orderitems = OrderItem.objects.filter(order=order)
    delivery_date = order.created_at + timedelta(days=5)

    context = {
        'order': order,
        'orderitems': orderitems,
        'delivery_date': delivery_date,
    }
    return render(request, "shop/orderdetails.html", context)