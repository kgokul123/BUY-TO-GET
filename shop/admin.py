from django.contrib import admin
from django.utils.html import format_html  # 🎯 பட்டன் டிசைன் செய்ய இது முக்கியம் பாஸ்
from django.urls import reverse  # 🎯 URL லிங்க் எடுக்க இது முக்கியம் பாஸ்
from .models import (
    Catagory, Product, ProductImage, Order, OrderItem, 
    Review, Cart, Favourite
)

# ⭐️ 1. Review ரெஜிஸ்ட்ரேஷன்
admin.site.register(Review)


# ⭐️ 2. Category செக்ஷன்
@admin.register(Catagory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    list_editable = ('status',)


# ⭐️ 3. Product செக்ஷன் (வித் இமேஜ் இன்லைன்)
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 10
    fields = ['image', 'video']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'original_price', 'selling_price', 'quantity', 'status', 'trending',)
    list_editable = ('quantity','original_price','selling_price', 'status', 'trending',)
    inlines = [ProductImageInline]


# ⭐️ 4. Cart செக்ஷன்
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'product_qty')


# ⭐️ 5. Favourite செக்ஷன்
@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product')


# ⭐️ 6. Order செக்ஷன் (வாங்கிய பொருட்கள் இன்லைன்)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product', 'quantity', 'price', 'status']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # 🎯 'download_invoice_link' ஐ டேபிளோட கடைசி காலமா சேர்த்துட்டேன் பாஸ்!
    list_display = [
        'order_number', 'user', 'total_amount', 'payment_mode', 
        'order_status', 'created_at', 'download_invoice_link'
    ]
    list_filter = ['order_status', 'payment_mode', 'created_at']
    readonly_fields = ['order_number', 'payment_mode', 'transaction_id', 'payment_id', 'created_at']
    inlines = [OrderItemInline]

    # 🔥 [பக்கா இன்டென்டேஷன் பிக்ஸ் பாஸ்]: கிளாஸ்க்குள்ள பக்காவா உக்கார வச்சாச்சு!
    def download_invoice_link(self, obj):
        url = reverse('download_invoice', args=[obj.order_number])
        return format_html(
            '<a class="button" href="{}" style="background-color: #198754; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-weight: bold;"><i class="fas fa-file-pdf"></i> PDF Bill</a>',
            url
        )
    
    download_invoice_link.short_description = 'Invoice Copy'