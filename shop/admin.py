from django.contrib import admin
from .models import *
from .models import Catagory, Product, Order, OrderItem
from .models import Product, ProductImage
from .models import Review

admin.site.register(Review)


@admin.register(Catagory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ( 'name', 'status')
    list_editable = ('status',)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 5

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'selling_price', 'quantity', 'status')
    list_editable = ('quantity', 'status')
    inlines = [ProductImageInline]

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'product_qty')

@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product')

from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    #  Only list fields that actually exist in the OrderItem model now
    readonly_fields = ['product', 'quantity', 'price', 'status']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # This displays the parent details, including payment mode and transaction ID
    list_display = ['order_number', 'user', 'total_amount', 'payment_mode', 'order_status', 'created_at']
    list_filter = ['order_status', 'payment_mode', 'created_at']
    
    # You can safely make payment info read-only on the Order level here:
    readonly_fields = ['order_number', 'payment_mode', 'transaction_id', 'payment_id', 'created_at']
    
    inlines = [OrderItemInline]
 def download_invoice_link(self, obj):
        # நம்ம வியூவ்ஸ்ல இருக்குற 'download_invoice' யூஆர்எல் லிங்க்கை எடுக்கிறோம்
        url = reverse('download_invoice', args=[obj.order_number])
        # அட்மின் டேபிள்ல ஒரு அழகான பச்சை கலர் பட்டனை ரெடி பண்றோம் தலைவா
        return format_html(
            '<a class="button" href="{}" style="background-color: #198754; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-weight: bold;"><i class="fas fa-file-pdf"></i> PDF Bill</a>',
            url
        )
    
    # அட்மின் டேபிளோட ஹெடிங் பெயர் என்னவாக இருக்கணும்னு சொல்றோம்
    download_invoice_link.short_description = 'Invoice Copy'