import os
import io
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from .models import Catagory, Product, ProductImage, Order, OrderItem, Review, Cart, Favourite, DeliveryPincode

admin.site.register(DeliveryPincode)
admin.site.register(Review)
admin.site.register(Cart)
admin.site.register(Favourite)

import json # இதை ஃபைலின் மேலே இம்போர்ட் செய்து கொள்ளவும்

def upload_file_to_drive(file_obj):
    try:
        if not file_obj or (isinstance(file_obj, str) and file_obj.startswith('http')):
            return file_obj
        
        file_name = getattr(file_obj, 'name', 'uploaded_file')
        file_bytes = file_obj.read()
        fh = io.BytesIO(file_bytes)

        SCOPES = ['https://www.googleapis.com/auth/drive']
        
        # 🚀 [மரண மாஸ் பிக்ஸ் பாஸ்]: Vercel Environment Variable-லிருந்து கிரெடென்ஷியல்ஸை நேரடியாக எடுப்பது!
        google_creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        
        if google_creds_json:
            creds_dict = json.loads(google_creds_json)
            creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        else:
            # ஒருவேளை லோக்கல் கம்ப்யூட்டரில் ஒர்க் செய்தால் பழையபடி `credentials.json` ஃபைலைப் பயன்படுத்திக் கொள்ளும்
            SERVICE_ACCOUNT_FILE = os.path.join(settings.BASE_DIR, 'credentials.json')
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        service = build('drive', 'v3', credentials=creds)

        FOLDER_ID = '15vb2MCi3J9XP0brNbGWf2d36INM2t5ng' # உங்கள் கூகுள் டிரைவ் ஃபோல்டர் ஐடி

        file_metadata = {
            'name': file_name,
            'parents': [FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(fh, mimetype='application/octet-stream', resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webContentLink'
        ).execute()

        file_id = file.get('id')
        service.permissions().create(
            fileId=file_id,
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()

        return file.get('webContentLink')
    except Exception as e:
        print(f"Admin Drive Upload Error: {e}")
        return None


@admin.register(Catagory)
class CategoryAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 4, 'cols': 40})}
    }
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'image' in form.base_fields:
            form.base_fields['image'].widget = admin.widgets.AdminFileWidget()
        return form

    def save_model(self, request, obj, form, change):
        if 'image' in request.FILES:
            link = upload_file_to_drive(request.FILES['image'])
            if link:
                obj.image = link
        super().save_model(request, obj, form, change)

    list_display = ('name', 'image_preview', 'status', 'trending',)
    list_editable = ('status', 'trending',)
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover; border-radius:50px;" />', str(obj.image))
        return "No Image"
    image_preview.short_description = 'Image'

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextInputWidget}
    }
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if 'image' in formset.form.base_fields:
            formset.form.base_fields['image'].widget = admin.widgets.AdminFileWidget()
        if 'video' in formset.form.base_fields:
            formset.form.base_fields['video'].widget = admin.widgets.AdminFileWidget()
        return formset

    fields = ['image', 'video', 'image_preview_inline']
    readonly_fields = ['image_preview_inline']

    def image_preview_inline(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover; border-radius:5px;" />', str(obj.image))
        return "No Image"
    image_preview_inline.short_description = 'Preview'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 8, 'cols': 70})}
    }
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'product_image' in form.base_fields:
            form.base_fields['product_image'].widget = admin.widgets.AdminFileWidget()
        return form

    def save_model(self, request, obj, form, change):
        if 'product_image' in request.FILES:
            link = upload_file_to_drive(request.FILES['product_image'])
            if link:
                obj.product_image = link
        super().save_model(request, obj, form, change)

    list_display = ('name', 'product_image_preview', 'original_price', 'selling_price', 'quantity', 'status', 'trending',)
    list_editable = ('quantity', 'original_price', 'selling_price', 'status', 'trending',)
    readonly_fields = ['product_image_preview']
    inlines = [ProductImageInline]

    def product_image_preview(self, obj):
        if obj.product_image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover; border-radius:5px;" />', str(obj.product_image))
        return "No Image"
    product_image_preview.short_description = 'Image'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product', 'quantity', 'price', 'status']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 4, 'cols': 50})}
    }
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for field in ['payment_screenshot', 'customer_signature', 'admin_signature', 'store_seal', 'signed_invoice_image']:
            if field in form.base_fields:
                form.base_fields[field].widget = admin.widgets.AdminFileWidget()
        return form

    def save_model(self, request, obj, form, change):
        for field in ['payment_screenshot', 'customer_signature', 'admin_signature', 'store_seal', 'signed_invoice_image']:
            if field in request.FILES:
                link = upload_file_to_drive(request.FILES[field])
                if link:
                    setattr(obj, field, link)
        super().save_model(request, obj, form, change)

    list_display = [
        'order_number', 'user', 'total_amount', 'payment_mode', 
        'order_status', 'created_at', 'download_invoice_link'
    ]
    list_filter = ['order_status', 'payment_mode', 'created_at']
    readonly_fields = [
        'order_number', 'payment_mode', 'transaction_id', 'payment_id', 
        'created_at', 'payment_screenshot_preview', 'customer_signature_preview'
    ]
    inlines = [OrderItemInline]

    def payment_screenshot_preview(self, obj):
        if obj.payment_screenshot:
            return format_html('<img src="{}" width="150" style="border-radius:5px;" />', str(obj.payment_screenshot))
        return "No Screenshot"
    payment_screenshot_preview.short_description = 'Payment Screenshot Preview'

    def customer_signature_preview(self, obj):
        if obj.customer_signature:
            return format_html('<img src="{}" width="150" style="border-radius:5px;" />', str(obj.customer_signature))
        return "No Signature"
    customer_signature_preview.short_description = 'Customer Signature Preview'

    def download_invoice_link(self, obj):
        url = reverse('download_invoice', args=[obj.order_number])
        return format_html(
            '<a class="button" href="{}" style="background-color: #198754; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-weight: bold;"><i class="fas fa-file-pdf"></i> PDF Bill</a>',
            url
        )
    download_invoice_link.short_description = 'Invoice Copy'