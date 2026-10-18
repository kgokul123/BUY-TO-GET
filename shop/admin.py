import os
import io
import json
import base64
import time
import uuid
import traceback
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db import models
from django.conf import settings
from django.contrib.admin.widgets import AdminFileWidget
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from django.contrib import admin
from django.db.models import Sum
from shop.models import OrderItem, Product

from django.contrib import admin
from django.db.models import Sum
from shop.models import OrderItem, Product  # ungaloda models-ku etha maari maathikonga

from django.contrib import admin
from django.db.models import Sum
from shop.models import OrderItem, Product


from django.contrib import admin
from django.db.models import Sum
from shop.models import OrderItem, Product
from django.urls import path
from django.contrib import admin
from django.db.models import Sum
from .models import OrderItem, Product, ProductImage, Catagory, Order, Review, Cart, Favourite, DeliveryPincode

# 📊 Django-வின் டீஃபால்ட் அட்மின் இன்டெக்ஸ் பக்கத்தை ஓவர்ரைடு செய்வது
original_admin_index = admin.site.index


def custom_admin_index(request, extra_context=None):
    # டாப் செல்லிங் ப்ராடக்ட்ஸ் டேட்டா எடுப்பது
    top_products = OrderItem.objects.values('product__name').annotate(total_sold=Sum('quantity')).order_by('-total_sold')[:5]
    
    chart_labels = [item['product__name'] for item in top_products]
    chart_data = [item['total_sold'] for item in top_products]
    
    extra_context = extra_context or {}
    extra_context['chart_labels'] = chart_labels
    extra_context['chart_data'] = chart_data
    
    return original_admin_index(request, extra_context)

# டீஃபால்ட் அட்மின் இன்டெக்ஸை மாற்றுகிறோம்
admin.site.index = custom_admin_index


SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    creds = None
    token_path = os.path.join(settings.BASE_DIR, 'token.json')
    client_secret_path = os.path.join(settings.BASE_DIR, 'client_secret.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

def delete_file_from_drive(file_url):
    try:
        if file_url:
            file_id = None
            url_str = str(file_url)
            if '/d/' in url_str:
                file_id = url_str.split('/d/')[-1].split('/')[0]
            elif 'id=' in url_str:
                file_id = url_str.split('id=')[-1].split('&')[0]
                
            if file_id:
                service = get_drive_service()
                service.files().delete(fileId=file_id).execute()
                print(f"🗑️ Old drive file deleted successfully: {file_id}")
    except Exception as e:
        print(f"🔥 DRIVE FILE DELETE ERROR: {e}")

def upload_file_to_drive(file_obj, product_id=None, folder_name="product images"):
    try:
        if not file_obj:
            return None
        if isinstance(file_obj, str) and file_obj.startswith('http'):
            return file_obj
        if not hasattr(file_obj, 'read'):
            return file_obj
            
        original_name = getattr(file_obj, 'name', 'uploaded_file')
        ext = original_name.split('.')[-1] if '.' in original_name else 'jpg'
        
        unique_suffix = int(time.time())
        random_str = uuid.uuid4().hex[:6]
        prod_prefix = f"product_{product_id}" if product_id else "item"
        file_name = f"{prod_prefix}_{unique_suffix}_{random_str}.{ext}"
        
        file_bytes = file_obj.read()
        if not file_bytes:
            return file_obj

        fh = io.BytesIO(file_bytes)
        service = get_drive_service()

        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        folders = results.get('files', [])

        if folders:
            folder_id = folders[0]['id']
        else:
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
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

        return f"https://lh3.googleusercontent.com/d/{file_id}"
        
    except Exception as e:
        print(f"🔥 OAUTH DRIVE UPLOAD ERROR: {e}")
        return file_obj



from django.contrib import admin
from .models import Catagory, Product, Order, OrderItem, Review, Cart, Favourite, DeliveryPincode
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from django.conf import settings

# 📂 Google Drive Upload Function
def upload_image_to_google_drive(file_obj, filename):
    try:
        creds_path = os.path.join(settings.BASE_DIR, 'credentials.json')
        FOLDER_ID = '1-iWWSNb7sjPQ1HMFQ-zXtKD_nzSUZNip'
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': filename,
            'parents': [FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(file_obj, mimetype='image/jpeg', resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink'
        ).execute()
        
        return file.get('webContentLink')
    except Exception as e:
        print(f"Drive Upload Error: {e}")
        return None

from django.contrib import admin
from .models import Catagory
from .utils import upload_image_to_google_drive

class CatagoryAdminForm(forms.ModelForm):
    image = forms.ImageField(required=False) # இது அட்மினில் Choose File பட்டனைக் கொண்டுவரும்

    class Meta:
        model = Catagory
        fields = '__all__'

# 2. Admin கிளாஸ்
from django.contrib import admin
from django import forms
from .models import Catagory
from .utils import  upload_image_to_google_drive

class CatagoryForm(forms.ModelForm):
    image = forms.ImageField(required=False)  # இது அட்மினில் Choose File பட்டனைக் கொண்டுவரும்[cite: 26]

    class Meta:
        model = Catagory
        fields = '__all__'


from django.db.models import Count


class CatagoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count', 'status', 'trending')
    
    # ஒவ்வொரு கேட்டகிரிக்கும் கீழே உள்ள ப்ராடக்ட்ஸ்களின் எண்ணிக்கையைக் கணக்கிட
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(num_products=Count('product')) # 'product' என்பது Product மாடலில் உள்ள ForeignKey ரிலேஷன் பெயர்

    def product_count(self, obj):
        return obj.num_products
    product_count.short_description = 'Products Count'
    product_count.admin_order_field = 'num_products'

    def direct_upload_view(self, request):
        if request.method == 'POST':
            try:
                cat_id = request.POST.get('cat_id')
                uploaded_file = request.FILES.get('new_image_file')
                
                if not cat_id or not uploaded_file:
                    return JsonResponse({'status': 'error', 'message': 'Missing category or file'})
                
                category = Catagory.objects.get(pk=cat_id)
                
                if category.image:
                    delete_file_from_drive(category.image)
                
                link = upload_file_to_drive(uploaded_file, folder_name="categories images")
                if link and str(link).startswith('http'):
                    category.image = link
                    category.save()
                    return JsonResponse({'status': 'success', 'url': link})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Drive upload failed'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'image' in form.base_fields:
            form.base_fields['image'].widget = GoogleDriveCategoryFileWidget()
        return form

    def save_model(self, request, obj, form, change):
        if 'image' in request.FILES:
            if change:
                try:
                    old_obj = Catagory.objects.get(pk=obj.pk)
                    if old_obj.image:
                        delete_file_from_drive(old_obj.image)
                except Catagory.DoesNotExist:
                    pass

            file_obj = request.FILES['image']
            link = upload_file_to_drive(file_obj, folder_name="categories images")
            if link and str(link).startswith('http'):
                obj.image = link
        elif change:
            try:
                original_obj = Catagory.objects.get(pk=obj.pk)
                if not obj.image and original_obj.image:
                    obj.image = original_obj.image
            except Catagory.DoesNotExist:
                pass
            
        super().save_model(request, obj, form, change)


admin.site.register(Catagory, CatagoryAdmin)
admin.site.register(DeliveryPincode)
admin.site.register(Review)
admin.site.register(Cart)
admin.site.register(Favourite)



class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2
    readonly_fields = ['image_preview_inline', 'video_preview_inline', 'live_preview_script']
    show_change_link = True
    formfield_overrides = {
        models.CharField: {'widget': AdminFileWidget()},
    }

    def image_preview_inline(self, obj):
        if obj and obj.image:
            img_url = str(obj.image)
            if img_url and img_url != 'None' and img_url != '':
                if not img_url.startswith('http') and not img_url.startswith('/'):
                    display_url = f"{settings.MEDIA_URL}{img_url}"
                else:
                    display_url = img_url
                return format_html('<a href="{0}" target="_blank"><img src="{0}" width="60" height="60" style="object-fit:cover; border-radius:6px; border:1px solid #ccc;" /></a>', display_url)
        return mark_safe('<span>No Image</span>')
    image_preview_inline.short_description = 'Image Preview'

    def video_preview_inline(self, obj):
        if obj and hasattr(obj, 'video') and obj.video:
            vid_url = str(obj.video)
            if vid_url and vid_url != 'None' and vid_url != '':
                if not vid_url.startswith('http') and not vid_url.startswith('/'):
                    display_vid_url = f"{settings.MEDIA_URL}{vid_url}"
                else:
                    display_vid_url = vid_url
                return format_html('<a href="{0}" target="_blank" style="color: #0d6efd; font-weight: bold; text-decoration: none;">🎥 View Video</a>', display_vid_url)
        return mark_safe('<span>No Video</span>')
    video_preview_inline.short_description = 'Video Preview'

    def live_preview_script(self, obj):
        return mark_safe("""
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                const inlineRows = document.querySelectorAll('.tabular.inline-related tbody tr');
                inlineRows.forEach(row => {
                    const fileInputs = row.querySelectorAll('input[type="file"]');
                    fileInputs.forEach(input => {
                        input.addEventListener('change', function(e) {
                            if (this.files && this.files[0]) {
                                const reader = new FileReader();
                                const file = this.files[0];
                                reader.onload = function(event) {
                                    if(input.name.includes('image')) {
                                        let prevTd = row.querySelector('.column-image_preview_inline');
                                        if(prevTd) {
                                            prevTd.innerHTML = '<img src="' + event.target.result + '" width="60" height="60" style="object-fit:cover; border-radius:6px; border:1px solid #198754;" />';
                                        }
                                    } else if(input.name.includes('video')) {
                                        let prevTd = row.querySelector('.column-video_preview_inline');
                                        if(prevTd) {
                                            prevTd.innerHTML = '<span style="color: #198754; font-weight: bold;">🎬 Selected</span>';
                                        }
                                    }
                                }
                                reader.readAsDataURL(file);
                            }
                        });
                    });
                });
            });
            </script>
        """)
    live_preview_script.short_description = ''


# 3. Modern Google Drive File Widget
class GoogleDriveFileWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        widget_html = super().render(name, value, attrs, renderer)
        
        preview_img_id = f"preview_{name}"
        
        preview_html = (
            '<div style="background: #f8f9fa; padding: 18px; border-radius: 14px; border: 1px solid #e9ecef; margin-bottom: 15px; max-width: 320px; box-shadow: 0 4px 15px rgba(0,0,0,0.04);">'
            '<span style="font-weight: 600; color: #495057; display: block; margin-bottom: 10px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">Live Product Preview</span>'
            f'<div style="width: 100%; height: 380px; border-radius: 10px; background: #ffffff; overflow: hidden; border: 1px solid #dee2e6; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s ease;" title="Click to Crop / Zoom Image" onclick="openCropperModal(\'{value}\')" onmouseover="this.style.boxShadow=\'0 6px 20px rgba(0,0,0,0.1)\'" onmouseout="this.style.boxShadow=\'none\'">'
            f'<img id="{preview_img_id}" src="{value}" style="width: 100% !important; height: 380px !important; object-fit: cover !important; object-position: center !important;" '
            'onerror="this.onerror=null; this.src=\'data:image/svg+xml,%3Csvg xmlns=\\\'http://www.w3.org/2000/svg\\\' width=\\\'300\\\' height=\\\'380\\\' viewBox=\\\'0 0 300 380\\\'%3E%3Crect width=\\\'300\\\' height=\\\'380\\\' fill=\\\'%23f1f3f5\\\'/%3E%3Ctext x=\\\'50%25\\\' y=\\\'50%25\\\' font-family=\\\'Segoe UI, Arial\\\' font-size=\\\'16\\\' fill=\\\'%23adb5bd\\\' dy=\\\'.3em\\\' text-anchor=\\\'middle\\\'%3ENo Image Uploaded%3C/text%3E%3C/svg%3E\';" />'
            '</div>'
            f'<div style="margin-top: 12px; text-align: center;"><span style="color: #0dcaf0; background: #cff4fc; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; cursor: pointer; display: inline-block;" onclick="openCropperModal(\'{value}\')">✨ Zoom, Crop & Adjust Image</span></div>'
            '</div>'
        )
        
        custom_upload_button = """
            <div style="background: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #ced4da; margin-top: 10px; display: flex; flex-direction: column; gap: 10px; max-width: 320px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.02);">
                <div style="font-size: 13px; font-weight: 600; color: #6c757d;">📁 Select & Sync with Google Drive:</div>
                <div style="display: flex; align-items: center; gap: 10px; word-break: break-all;">
                    %s
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px;">
                    <button type="button" onclick="uploadSelectedFile(this)" style="padding: 8px 16px; background: linear-gradient(135deg, #0d6efd, #0b5ed7); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px; box-shadow: 0 2px 5px rgba(13,110,253,0.3); transition: 0.2s; width: 100%%; text-align: center;">☁️ Upload & Replace in Drive</button>
                    <span class="uploadStatus" style="font-size: 12px; font-weight: 600; color: #198754;"></span>
                </div>
            </div>
            
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                const fileInputs = document.querySelectorAll('input[type="file"]');
                fileInputs.forEach(fileInput => {
                    fileInput.addEventListener('change', function(event) {
                        if (this.files && this.files[0]) {
                            const reader = new FileReader();
                            reader.onload = function(e) {
                                const container = fileInput.closest('div');
                                const previewBox = container ? container.parentElement.parentElement.querySelector('img') : null;
                                if (previewBox) {
                                    previewBox.src = e.target.result;
                                }
                            }
                            reader.readAsDataURL(this.files[0]);
                        }
                    });
                });
            });

            function uploadSelectedFile(btn) {
                const container = btn.closest('div').parentElement;
                const fileInput = container.querySelector('input[type="file"]');
                
                if (!fileInput || !fileInput.files || !fileInput.files[0]) {
                    alert("Please choose a file first using 'Choose File'!");
                    return;
                }
                
                const pathParts = window.location.pathname.split('/');
                let productId = '';
                for (let i = 0; i < pathParts.length; i++) {
                    if (!isNaN(pathParts[i]) && pathParts[i] !== '') {
                        productId = pathParts[i];
                        break;
                    }
                }
                
                if (!productId) {
                    alert("Please save the product first before uploading images!");
                    return;
                }
                
                const formData = new FormData();
                formData.append('product_id', productId);
                formData.append('new_image_file', fileInput.files[0]);
                
                const csrftoken = getCookie('csrftoken');
                const statusSpan = container.querySelector('.uploadStatus');
                if(statusSpan) statusSpan.innerHTML = "Syncing with Drive...";

                fetch('/admin/shop/product/direct-upload/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        alert("New image uploaded and old image replaced in Google Drive successfully!");
                        location.reload();
                    } else {
                        alert("Error: " + data.message);
                        if(statusSpan) statusSpan.innerHTML = "";
                    }
                })
                .catch((error) => {
                    console.error('Error:', error);
                    alert("Upload failed!");
                    if(statusSpan) statusSpan.innerHTML = "";
                });
            }
            </script>
        """ % widget_html
        
        cropper_modal_and_global_js = """
            <div id="cropperModal" style="display:none; position:fixed; z-index:99999; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.6); backdrop-filter: blur(4px); align-items:center; justify-content:center;">
                <div style="background:#fff; padding:25px; border-radius:16px; width:90%; max-width:650px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                    <h3 style="margin-top:0; color:#212529; font-family: 'Segoe UI', Arial; font-weight: 600;">✨ Image Zoom & Crop Studio</h3>
                    <div style="max-height:400px; overflow:hidden; background:#111; border-radius: 8px; display:flex; justify-content:center; margin-top: 15px;">
                        <img id="cropperImage" src="" style="max-width:100%; display:block;" />
                    </div>
                    <div id="cropSyncStatus" style="margin-top: 15px; font-weight: bold; color: #0d6efd; text-align: center; font-size: 14px;"></div>
                    <div style="margin-top:20px; display:flex; justify-content:space-between; align-items:center;">
                        <div style="display: flex; gap: 8px;">
                            <button type="button" onclick="if(cropperObj) cropperObj.zoom(0.1)" style="padding:6px 12px; background:#e9ecef; color:#495057; border:none; border-radius:6px; cursor:pointer; font-weight:600; font-size:12px;">Zoom +</button>
                            <button type="button" onclick="if(cropperObj) cropperObj.zoom(-0.1)" style="padding:6px 12px; background:#e9ecef; color:#495057; border:none; border-radius:6px; cursor:pointer; font-weight:600; font-size:12px;">Zoom -</button>
                            <button type="button" onclick="if(cropperObj) cropperObj.rotate(90)" style="padding:6px 12px; background:#e9ecef; color:#495057; border:none; border-radius:6px; cursor:pointer; font-weight:600; font-size:12px;">Rotate ↺</button>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button type="button" onclick="closeCropperModal()" style="padding:7px 16px; background:#6c757d; color:#fff; border:none; border-radius:6px; cursor:pointer; font-weight:600; font-size:13px;">Cancel</button>
                            <button type="button" onclick="saveCroppedImage()" style="padding:7px 16px; background:#198754; color:#fff; border:none; border-radius:6px; cursor:pointer; font-weight:600; font-size:13px;">Crop & Replace</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
            let cropperObj = null;
            
            function openCropperModal(imgUrl) {
                const modal = document.getElementById('cropperModal');
                const image = document.getElementById('cropperImage');
                
                if (imgUrl.startsWith('data:') || imgUrl === 'None' || imgUrl === '' || !imgUrl.startsWith('http')) {
                    alert("Please Save the product first before cropping images!");
                    return;
                }
                
                image.src = imgUrl;
                modal.style.display = 'flex';
                
                const statusDiv = document.getElementById('cropSyncStatus');
                if(statusDiv) statusDiv.innerHTML = "";
                
                if (cropperObj) {
                    cropperObj.destroy();
                }
                setTimeout(() => {
                    cropperObj = new Cropper(image, {
                        aspectRatio: 3 / 4,
                        viewMode: 1,
                        autoCropArea: 0.9,
                    });
                }, 200);
            }
            
            function closeCropperModal() {
                document.getElementById('cropperModal').style.display = 'none';
                if (cropperObj) {
                    cropperObj.destroy();
                }
            }
            
            function getCookie(name) {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

            function saveCroppedImage() {
                if (!cropperObj) return;
                const canvas = cropperObj.getCroppedCanvas({ width: 600, height: 800 });
                if (!canvas) return;
                
                const base64data = canvas.toDataURL('image/jpeg');
                const pathParts = window.location.pathname.split('/');
                let productId = '';
                for (let i = 0; i < pathParts.length; i++) {
                    if (!isNaN(pathParts[i]) && pathParts[i] !== '') {
                        productId = pathParts[i];
                        break;
                    }
                }
                
                if (!productId) {
                    alert("Please save the product first before cropping images!");
                    closeCropperModal();
                    return;
                }
                
                const statusDiv = document.getElementById('cropSyncStatus');
                if(statusDiv) statusDiv.innerHTML = "🔄 Syncing with Drive...";
                
                const csrftoken = getCookie('csrftoken');
                
                fetch('/admin/shop/product/crop-upload/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify({ product_id: productId, image_data: base64data })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        if(statusDiv) statusDiv.innerHTML = "✅ Synced Successfully! Reloading...";
                        setTimeout(() => {
                            location.reload();
                        }, 1000);
                    } else {
                        alert("Error: " + data.message);
                        closeCropperModal();
                    }
                })
                .catch((error) => {
                    console.error('Error:', error);
                    alert("Upload failed!");
                    closeCropperModal();
                });
            }
            </script>
        """
        
        return mark_safe(
            preview_html +
            custom_upload_button +
            cropper_modal_and_global_js
        )

from django.shortcuts import render, redirect
from django.db.models import Count

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css',)
        }
        js = ('https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js',)

    save_on_top = True
    save_as = False

    # 🌟 Products-ஐக் கிளிக் செய்தவுடன் Categories லிஸ்ட்டைக் காட்டுவதற்கான லாஜிக்
    def changelist_view(self, request, extra_context=None):
        category_id = request.GET.get('category__id__exact')
        
        # ஒருவேளை எந்த கேட்டிரியும் தேர்ந்தெடுக்கப்படவில்லை என்றால், Categories லிஸ்ட்டைக் காட்டுவோம்
        if not category_id:
            # அனைத்து கேட்டகிரிகளையும், அவற்றுள் உள்ள ப்ராடக்ட் எண்ணிக்கையுடன் எடுப்பது
            categories = Catagory.objects.annotate(product_count=Count('product'))
            
            context = {
                **self.admin_site.each_context(request),
                'title': 'Select Category to View Products',
                'categories': categories,
            }
            return render(request, 'shop/products/category_list.html', context)
            
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('crop-upload/', self.admin_site.admin_view(self.crop_upload_view)),
            path('direct-upload/', self.admin_site.admin_view(self.direct_upload_view)),
        ]
        return custom_urls + urls

    def crop_upload_view(self, request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                product_id = data.get('product_id')
                image_data = data.get('image_data')
                
                product = Product.objects.get(pk=product_id)
                
                if product.product_image:
                    delete_file_from_drive(product.product_image)

                header, encoded = image_data.split(',', 1)
                file_bytes = base64.b64decode(encoded)
                file_obj = io.BytesIO(file_bytes)
                file_obj.name = f"product_cropped_{product.pk}.jpg"
                
                link = upload_file_to_drive(file_obj, product_id=product.pk)
                if link and str(link).startswith('http'):
                    product.product_image = link
                    product.save()
                    return JsonResponse({'status': 'success', 'url': link})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})

    def direct_upload_view(self, request):
        if request.method == 'POST':
            try:
                product_id = request.POST.get('product_id')
                uploaded_file = request.FILES.get('new_image_file')
                
                if not product_id or not uploaded_file:
                    return JsonResponse({'status': 'error', 'message': 'Missing product or file'})
                
                product = Product.objects.get(pk=product_id)
                
                if product.product_image:
                    delete_file_from_drive(product.product_image)
                
                link = upload_file_to_drive(uploaded_file, product_id=product.pk)
                if link and str(link).startswith('http'):
                    product.product_image = link
                    product.save()
                    return JsonResponse({'status': 'success', 'url': link})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Drive upload failed'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 8, 'cols': 70})}
    }

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'product_image' in form.base_fields:
            form.base_fields['product_image'].widget = GoogleDriveFileWidget()
        return form

    def save_model(self, request, obj, form, change):
        if 'product_image' in request.FILES:
            if change:
                try:
                    old_obj = Product.objects.get(pk=obj.pk)
                    if old_obj.product_image:
                        delete_file_from_drive(old_obj.product_image)
                except Product.DoesNotExist:
                    pass

            file_obj = request.FILES['product_image']
            link = upload_file_to_drive(file_obj, product_id=obj.pk if obj.pk else None)
            if link and str(link).startswith('http'):
                obj.product_image = link
        elif change:
            try:
                original_obj = Product.objects.get(pk=obj.pk)
                if not obj.product_image:
                    obj.product_image = original_obj.product_image
            except Product.DoesNotExist:
                pass
            
        super().save_model(request, obj, form, change)

    list_display = ('name', 'product_image_preview', 'original_price', 'selling_price', 'quantity', 'status', 'trending', 'out_of_stock')
    list_editable = ('quantity', 'original_price', 'selling_price', 'status', 'trending', 'out_of_stock')
    readonly_fields = ['product_image_preview']
    inlines = [ProductImageInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        
        for inline_form in formset.forms:
            if not inline_form.is_valid():
                continue
            
            obj = inline_form.instance
            if not isinstance(obj, ProductImage):
                continue
                
            # 🎯 புதிய ஃபைல் அப்லோட் செய்யப்படவில்லை என்றால் பழைய கூகுள் டிரைவ் லிங்க்கைப் பாதுகாக்கிறோம்
            has_new_file = False
            for field_name, file_obj in request.FILES.items():
                if inline_form.prefix in field_name and file_obj:
                    has_new_file = True
                    if 'image' in field_name:
                        link = upload_file_to_drive(file_obj, product_id=obj.product.pk if obj.product else None, folder_name="product images")
                        if link and str(link).startswith('http'):
                            obj.image = link
                    elif 'video' in field_name:
                        link = upload_file_to_drive(file_obj, product_id=obj.product.pk if obj.product else None, folder_name="product videos")
                        if link and str(link).startswith('http'):
                            obj.video = link

            # புதிய ஃபைல் கொடுக்கப்படாவிட்டால், ஏற்கனவே உள்ள தரவு மாறாமல் இருக்க டேட்டபேஸில் உள்ள பழைய மதிப்பை எடுக்கிறோம்
            if not has_new_file and obj.pk:
                try:
                    old_instance = ProductImage.objects.get(pk=obj.pk)
                    if not obj.image and old_instance.image:
                        obj.image = old_instance.image
                    if not obj.video and old_instance.video:
                        obj.video = old_instance.video
                except ProductImage.DoesNotExist:
                    pass

        formset.save()
        super().save_formset(request, form, formset, change)

    def product_image_preview(self, obj):
        try:
            if obj.product_image:
                img_url = bytes(str(obj.product_image), 'utf-8', errors='ignore').decode('utf-8')
                if img_url.startswith('http'):
                    return mark_safe(f'<div style="display: flex; align-items: center; gap: 8px;"><a href="{img_url}" target="_blank"><img src="{img_url}" width="45" height="45" style="object-fit:cover; border-radius:4px; border:1px solid #ccc;" /></a><span style="color: #198754; font-size: 11px; font-weight: bold;">Active</span></div>')
        except Exception:
            pass
        return mark_safe('<span style="color: #dc3545; font-style: italic;">No Image Uploaded</span>')
    
    product_image_preview.short_description = 'Google Drive Image Preview'


# 5. Order Admin
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
        *list(dict.fromkeys([
            'order_number', 'user', 'total_amount', 'payment_mode', 
            'order_status', 'created_at', 'download_invoice_link'
        ]))
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
        image_url = str(obj.customer_signature) if obj.customer_signature else ""
        if image_url:
            return format_html('<img src="{}" width="150" style="border-radius:5px;" />', image_url)
        return "No Signature"
    customer_signature_preview.short_description = 'Customer Signature Preview'

    def download_invoice_link(self, obj):
        url = reverse('download_invoice', args=[obj.order_number])
        return format_html(
            '<a class="button" href="{}" style="background-color: #198754; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-weight: bold;"><i class="fas fa-file-pdf"></i> PDF Bill</a>',
            url
        )
    download_invoice_link.short_description = 'Invoice Copy'


class GoogleDriveCategoryFileWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        widget_html = super().render(name, value, attrs, renderer)
        preview_img_id = f"preview_{name}"
        
        img_src = value if value and str(value).startswith('http') else ''
        
        preview_html = (
            '<div style="background: #f8f9fa; padding: 18px; border-radius: 14px; border: 1px solid #e9ecef; margin-bottom: 15px; max-width: 320px; box-shadow: 0 4px 15px rgba(0,0,0,0.04);">'
            '<span style="font-weight: 600; color: #495057; display: block; margin-bottom: 10px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">Live Category Preview</span>'
            f'<div style="width: 100%; height: 250px; border-radius: 10px; background: #ffffff; overflow: hidden; border: 1px solid #dee2e6; display: flex; align-items: center; justify-content: center;">'
            f'<img id="{preview_img_id}" src="{img_src}" style="width: 100% !important; height: 250px !important; object-fit: cover !important; object-position: center !important;" '
            'onerror="this.onerror=null; this.src=\'data:image/svg+xml,%3Csvg xmlns=\\\'http://www.w3.org/2000/svg\\\' width=\\\'300\\\' height=\\\'250\\\' viewBox=\\\'0 0 300 250\\\'%3E%3Crect width=\\\'300\\\' height=\\\'250\\\' fill=\\\'%23f1f3f5\\\'/%3E%3Ctext x=\\\'50%25\\\' y=\\\'50%25\\\' font-family=\\\'Segoe UI, Arial\\\' font-size=\\\'15\\\' fill=\\\'%23adb5bd\\\' dy=\\\'.3em\\\' text-anchor=\\\'middle\\\'%3ENo Image Uploaded%3C/text%3E%3C/svg%3E\';" />'
            '</div>'
            '</div>'
        )
        
        custom_upload_button = f"""
            <div style="background: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #ced4da; margin-top: 10px; display: flex; flex-direction: column; gap: 10px; max-width: 320px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.02);">
                <div style="font-size: 13px; font-weight: 600; color: #6c757d;">📁 Select & Sync with Google Drive:</div>
                <div style="display: flex; align-items: center; gap: 10px; word-break: break-all;">
                    {widget_html}
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px;">
                    <button type="button" onclick="uploadCategoryFile(this)" style="padding: 8px 16px; background: linear-gradient(135deg, #0d6efd, #0b5ed7); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px; box-shadow: 0 2px 5px rgba(13,110,253,0.3); width: 100%; text-align: center;">☁️ Upload & Replace in Drive</button>
                    <span class="uploadStatus" style="font-size: 12px; font-weight: 600; color: #198754;"></span>
                </div>
            </div>
        """
        
        js_script = """
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                const fileInputs = document.querySelectorAll('input[type="file"]');
                fileInputs.forEach(fileInput => {
                    fileInput.addEventListener('change', function(event) {
                        if (this.files && this.files[0]) {
                            const reader = new FileReader();
                            reader.onload = function(e) {
                                const container = fileInput.closest('div');
                                const previewBox = container ? container.parentElement.parentElement.querySelector('img') : null;
                                if (previewBox) {
                                    previewBox.src = e.target.result;
                                }
                            }
                            reader.readAsDataURL(this.files[0]);
                        }
                    });
                });
            });

            function uploadCategoryFile(btn) {
                const container = btn.closest('div').parentElement;
                const fileInput = container.querySelector('input[type="file"]');
                const statusSpan = container.querySelector('.uploadStatus');
                
                if (!fileInput || !fileInput.files || !fileInput.files[0]) {
                    alert("Please choose a file first using 'Choose File'!");
                    return;
                }
                
                const pathParts = window.location.pathname.split('/');
                let catId = '';
                for (let i = 0; i < pathParts.length; i++) {
                    if (!isNaN(pathParts[i]) && pathParts[i] !== '') {
                        catId = pathParts[i];
                        break;
                    }
                }
                
                if (!catId) {
                    alert("Please save the category first before uploading images!");
                    return;
                }
                
                const formData = new FormData();
                formData.append('cat_id', catId);
                formData.append('new_image_file', fileInput.files[0]);
                
                const csrftoken = getCookie('csrftoken');
                if(statusSpan) {
                    statusSpan.style.color = "#0d6efd";
                    statusSpan.innerHTML = "🔄 Syncing with Drive...";
                }

                fetch('/admin/shop/catagory/direct-upload/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrftoken },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        if(statusSpan) {
                            statusSpan.style.color = "#198754";
                            statusSpan.innerHTML = "✅ Successfully Saved!";
                        }
                        setTimeout(() => {
                            location.reload();
                        }, 1200);
                    } else {
                        alert("Error: " + data.message);
                        if(statusSpan) statusSpan.innerHTML = "";
                    }
                })
                .catch((error) => {
                    console.error('Error:', error);
                    alert("Upload failed!");
                    if(statusSpan) statusSpan.innerHTML = "";
                });
            }

            function getCookie(name) {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            </script>
        """
        
        return mark_safe(preview_html + custom_upload_button + js_script)


def direct_upload_view(self, request):
        if request.method == 'POST':
            try:
                cat_id = request.POST.get('cat_id')
                uploaded_file = request.FILES.get('new_image_file')
                
                if not cat_id or not uploaded_file:
                    return JsonResponse({'status': 'error', 'message': 'Missing category or file'})
                
                category = Catagory.objects.get(pk=cat_id)
                
                # 🗑️ பழைய இமேஜ் டிரைவில் இருந்தால் அதை டெீலீட் செய்வது
                if category.image:
                    delete_file_from_drive(category.image)
                
                # ☁️ புதிய இமேஜை டிரைவில் அப்லோட் செய்வது
                link = upload_file_to_drive(uploaded_file, folder_name="categories images")
                if link and str(link).startswith('http'):
                    category.image = link
                    category.save()
                    return JsonResponse({'status': 'success', 'url': link})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Drive upload failed'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})

