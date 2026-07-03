import json
import os
import io
import base64
import requests
import urllib.parse
import qrcode
from abc import ABC, abstractmethod
from datetime import timedelta, date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.template.loader import get_template

from xhtml2pdf import pisa

# உங்கள் மாடல்கள் மற்றும் ஃபார்ம்களை ஒருமுறை மட்டும் இம்போர்ட் செய்யவும்
from .models import (
    Profile, Cart, Catagory, DeliveryPincode, Favourite, 
    Order, OrderItem, Product, Review, User
)
from .forms import ProductUploadForm, CustomUserForm
from vercel_blob import put

@csrf_exempt
def upload_to_blob(request):
    if request.method == 'POST':
        filename = request.GET.get('filename')
        # இங்கே 'put' சரியாக வேலை செய்யும்
        blob = put(filename, request.body, access='public')
        return JsonResponse({'url': blob.url})
    
    # POST ரிக்வெஸ்ட் இல்லையென்றால் எரர் காட்டவும்
    return JsonResponse({'error': 'Only POST allowed'}, status=400)


def get_upload_url(request):
    # இங்கிருந்து நேரடியாக Vercel Blob-க்கு ஃபைல் போகும்
    # நீங்கள் client-side-ல் `put` பயன்படுத்தினால், இந்த பகுதி தானாக நடக்கும்.
    return JsonResponse({'message': 'Upload ready'})

def upload_product(request):
    if request.method == 'POST':
        form = ProductUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('success_page')
    else:
        form = ProductUploadForm()
    return render(request, 'shop/upload.html', {'form': form})


@login_required
def accept_terms(request):
    if request.method == 'POST':
        profile, created = Profile.objects.get_or_create(user=request.user)
        profile.terms_accepted = True
        profile.save() # இதுதான் டேட்டாபேஸில் சேமிக்கும்
    return redirect('home') # இது ஹோம் பேஜுக்கு திருப்பிவிடும்

def terms_view(request):
    return render(request, 'shop/inc/terms.html')

# views.py
def home(request):
    show_terms = False
    if request.user.is_authenticated:
        profile = UserProfile.objects.get(user=request.user)
        if not profile.terms_accepted:
            show_terms = True
    return render(request, 'home.html', {'show_terms': show_terms})


@login_required(login_url="login")
def download_invoice_pdf(request, order_no):
    try:
        clean_id = order_no.replace("ORD", "").replace("A", "").strip()
        order = Order.objects.get(id=clean_id)
    except (Order.DoesNotExist, ValueError):
        order = Order.objects.filter(user=request.user).last()
        if not order:
            order = Order.objects.last()
        if not order:
            return HttpResponse("பாஸ், டேட்டாபேஸ்ல இன்னும் ஒரு ஆர்டர் கூட இல்லை!")

    logo_base64 = ""
    try:
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'uploads', 'images', 'logo.jpg.jpeg')
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as image_file:
                logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"லோகோ கிடைக்கல: {e}")

    live_domain = "https://buy-to-get.vercel.app"
    verification_url = f"{live_domain}/digital-verify/{order.id}/"
    top_qr = qrcode.QRCode(version=1, box_size=3, border=1)
    top_qr.add_data(verification_url)
    top_qr.make(fit=True)
    top_img = top_qr.make_image(fill_color="black", back_color="white")
    top_buffer = io.BytesIO()
    top_img.save(top_buffer, format="PNG")
    invoice_url_qr = base64.b64encode(top_buffer.getvalue()).decode('utf-8')
    
    qr_code_base64_data = ""
    if str(order.order_status).lower() == 'pending' or str(order.payment_mode).upper() == 'COD':
        your_upi_id = "kalaiarasi2128@oksbi"
        store_name = "KALAIARASI METAL STORE"
        upi_string = f"upi://pay?pa={your_upi_id}&pn={urllib.parse.quote(store_name)}&am={order.total_amount}&cu=INR"
        bottom_qr = qrcode.QRCode(version=1, box_size=4, border=1)
        bottom_qr.add_data(upi_string)
        bottom_qr.make(fit=True)
        bottom_img = bottom_qr.make_image(fill_color="black", back_color="white")
        bottom_buffer = io.BytesIO()
        bottom_img.save(bottom_buffer, format="PNG")
        qr_code_base64_data = base64.b64encode(bottom_buffer.getvalue()).decode('utf-8')

    context = {
        'order': order,
        'order_no': order_no,
        'invoice_url_qr': invoice_url_qr,           
        'qr_code_base64_data': qr_code_base64_data, 
        'logo_base64': logo_base64,
    }
    
    html_template = render(request, 'shop/invoice_pdf.html', context)
    html = html_template.content.decode('utf-8')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order_no}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors')
    return response


def upload_verification_images(request, order_id):
    order = Order.objects.get(id=order_id)
    
    if request.method == "POST" and request.FILES:
        # கஸ்டமர் சைன், அட்மின் சைன் மற்றும் சீல் இமேஜ்களை ஃபார்ம் மூலமா வாங்குறோம் பாஸ்
        order.customer_signature = request.FILES.get('customer_sig')
        order.admin_signature = request.FILES.get('admin_sig')
        order.store_seal = request.FILES.get('store_seal')
        order.is_digitally_verified = True
        order.save()
        return redirect('admin_dashboard')


# 🎯 [உங்க இன்வாய்ஸ் வியூவ் ஃபங்க்ஷனுக்கு உள்ளே இந்த லாஜிக்கை வைங்க பாஸ்]
def your_invoice_pdf_view(request, order_id):
    order = Order.objects.get(id=order_id)
    
    # 🚀 [லைவ் வெப்சைட் வெரிஃபிகேஷன் லிங்க் பாஸ்]:
    # கஸ்டமர் ஸ்கேன் பண்ணா நேரா உங்க வெப்சைட்ல இருக்குற 'digital-verify' பக்கத்துக்கு போகும்!
    # (உங்க ஒரிஜினல் டொமைன் நேமை 'https://kalaiarasi-metal-store.vercel.app' மாதிரி இங்க மாத்திக்கோங்க பாஸ்)
    live_domain = "https://buy-to-get.vercel.com" 
    verification_url = f"{live_domain}/digital-verify/{order.id}/"
    
    # டாப் லெஃப்ட் கியூஆர் கோடு இமேஜ் ஜெனரேட் பண்றோம் பாஸ்
    top_qr = qrcode.QRCode(version=1, box_size=3, border=1)
    top_qr.add_data(verification_url)
    top_qr.make(fit=True)
    
    top_img = top_qr.make_image(fill_color="black", back_color="white")
    
    top_buffer = io.BytesIO()
    top_img.save(top_buffer, format="PNG")
    invoice_url_qr_base64 = base64.b64encode(top_buffer.getvalue()).decode('utf-8')
    
    # 💰 உங்க பழைய பாட்டம் பேமெண்ட் யூபிஐ கியூஆர் கோடு லாஜிக் (COD-க்காக மட்டும்)
    qr_code_base64_data = ""
    if order.order_status|lower == 'pending' or order.payment_mode|upper == 'COD':
        your_upi_id = "kalaiarasi2128@oksbi"
        upi_string = f"upi://pay?pa={your_upi_id}&pn=KALAIARASI%20METAL%20STORE&am={order.total_amount}&cu=INR"
        
        bottom_qr = qrcode.QRCode(version=1, box_size=4, border=1)
        bottom_qr.add_box_data(upi_string) if hasattr(bottom_qr, 'add_box_data') else bottom_qr.add_data(upi_string)
        bottom_qr.make(fit=True)
        
        bottom_img = bottom_qr.make_image(fill_color="black", back_color="white")
        bottom_buffer = io.BytesIO()
        bottom_img.save(bottom_buffer, format="PNG")
        qr_code_base64_data = base64.b64encode(bottom_buffer.getvalue()).decode('utf-8')

    context = {
        'order': order,
        'invoice_url_qr': invoice_url_qr_base64, # 👈 டாப்-லெஃப்ட் வெரிஃபிகேஷன் லிங்க் கியூஆர் பாஸ்!
        'qr_code_base64_data': qr_code_base64_data, # பாட்டம் பேமெண்ட் கியூஆர்
    }
    # உங்க பிடிஎஃப் ரெண்டரிங் லாஜிக் அப்படியே கீழே தொடரட்டும் பாஸ்...


# === 1. OTP & WHATSAPP VERIFICATION ===

def digital_verification_view(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except (Order.DoesNotExist, ValueError):
        order = Order.objects.filter(is_digitally_verified=True).last()
        if not order:
            order = Order.objects.last()

    if not order:
        return HttpResponse("பாஸ், வெப்சைட்ல இன்னும் ஆர்டர்கள் எதுவும் இல்லை!")

    # 🔐 [ஒரே ஒரு முழு பில் போட்டோவை மட்டும் வாங்கி சேவ் செய்யும் லாஜிக் பாஸ்]
    if request.method == "POST" and request.FILES:
        if request.user.is_authenticated and request.user.is_staff:
            invoice_photo = request.FILES.get('signed_invoice')
            
            if invoice_photo:
                order.signed_invoice_image = invoice_photo
                order.is_digitally_verified = True
                order.save()
            
            return redirect('digital_verification_view', order_id=order.id)
        else:
            return HttpResponse("பாஸ், நீங்க அட்மின் இல்லை!")

    context = {
        'order': order,
    }
    return render(request, 'shop/digital_verification.html', context)


OTP_STORE = {}

@csrf_exempt
def send_verification_whatsapp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            mobile_number = data.get('mobile_number')
            name = data.get('name')
            
            otp = str(random.randint(100000, 999999))
            OTP_STORE[mobile_number] = otp
            
            ngrok_url = "https://ludicrous-slighting-negligent.ngrok-free.dev/send-whatsapp"
            
            payload = {
                "number": mobile_number,
                "message": f"WELCOME {name}, YOUR KALAIARASI METAL STORE OTP NUMBER IS: {otp}. IN THE OTP IS EXPIRED IN ONLY 2 MINUTES!"
            }
            
            try:
                requests.post(ngrok_url, json=payload, timeout=2)
                return JsonResponse({'success': True, 'message': 'OTP initiated boss!'})
            except requests.exceptions.Timeout:
                return JsonResponse({'success': True, 'message': 'OTP initiated successfully boss!'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
            
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        body = json.loads(request.body)
        mobile_number = body.get('mobile_number', '')
        user_otp = body.get('otp', '')

        clean_number = "".join([c for c in str(mobile_number) if c.isdigit()])
        
        if clean_number.startswith('91') and len(clean_number) > 10:
            clean_number = clean_number[2:]

        matched_otp = None
        for key, stored_otp in OTP_STORE.items():
            clean_key = "".join([c for c in str(key) if c.isdigit()])
            if clean_key.startswith('91') and len(clean_key) > 10:
                clean_key = clean_key[2:]
            
            if clean_key == clean_number:
                matched_otp = stored_otp
                break

        if matched_otp and str(matched_otp).strip() == str(user_otp).strip():
            return JsonResponse({"success": True, "message": "OTP Verified!"})
        
        return JsonResponse({"success": False, "message": "தவறான OTP எண் பாஸ்! மீண்டும் முயலவும்."})


def check_verification_status(request):
    phone = request.GET.get('mobile_number')
    if phone in OTP_STORE:
        return JsonResponse({"verified": True})
    return JsonResponse({"verified": False})


@csrf_exempt
def send_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            mobile_number = data.get('mobile_number') or data.get('phone')
            
            if not mobile_number:
                return JsonResponse({'success': False, 'message': 'Mobile number required!'}, status=400)
            
            request.session['mobile_number'] = mobile_number
            otp = str(random.randint(100000, 999999))
            request.session['generated_otp'] = otp
            
            return JsonResponse({
                'success': True,
                'status': 'success',
                'dev_otp': otp
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid Request'}, status=400)


# === 2. UTILITIES & MIGRATIONS ===

def run_online_migration(request):
    try:
        call_command('migrate', interactive=False)
        return HttpResponse("<h1>Success: Database Migrated Successfully!</h1>")
    except Exception as e:
        return HttpResponse(f"<h1>Error: {str(e)}</h1>")


def check_pincode(request):
    pincode = request.GET.get("pincode", "").strip()
    available = (pincode == "631208")
    return JsonResponse({"available": available})


# === 3. HOME & PRODUCTS ===

def home(request):
    products = Product.objects.filter(trending=1)
    return render(request, "shop/index.html", {"products": products})


def Product_details_by_id(request, prod_id):
    products = Product.objects.get(id=prod_id)
    reviews = Review.objects.filter(product=products).order_by("-created_at")
    context = {"products": products, "reviews": reviews}
    return render(request, "shop/products/product_details.html", context)


def Product_details(request, cname, pname):
    clean_cname = urllib.parse.unquote(cname).strip()
    clean_pname = urllib.parse.unquote(pname).strip()
    
    single_product = Product.objects.filter(name__icontains=clean_pname, status=0).first()
    
    if not single_product:
        single_product = Product.objects.filter(category__name__icontains=clean_cname, status=0).first()
        
    reviews = []
    trending_products = [] # 👈 டிரெண்டிங் பொருட்களுக்கான புது லிஸ்ட் பாஸ்!
    
    if single_product:
        try:
            reviews = Review.objects.filter(product=single_product)
        except Exception as e:
            print(e)
            
        # 🚀 [மரண மாஸ் லாஜிக் பாஸ்]: 
        # தற்போதைய சிங்கிள் ப்ராடக்ட் ஐடியை எக்ஸ்க்ளூட் (Exclude) பண்ணிட்டு, மீதி இருக்குற டிரெண்டிங் பொருட்களை மட்டும் 4 கார்டுகளாக எடுக்கிறோம்!
        trending_products = Product.objects.filter(trending=True, status=0).exclude(id=single_product.id)[:4]
    else:
        # ஒருவேளை மெயின் ப்ராடக்ட் இல்லைனா, பொதுவான ஏதாச்சும் 4 டிரெண்டிங் பொருட்களைக் காட்டுவோம் பாஸ்
        trending_products = Product.objects.filter(trending=True, status=0)[:4]

    context = {
        "products": single_product, 
        "reviews": reviews,
        "trending_products": trending_products # 👈 இந்த புது வேரியபிளை இப்போ காண்டெக்ஸ்ட்ல ஏத்தியாச்சு தலைவா!
    }
    return render(request, 'shop/products/product_details.html', context)


def collections(request):
    catagory = Catagory.objects.filter(status=0)
    return render(request, "shop/collections.html", {"catagory": catagory})


def collectionsview(request, name):
    clean_name = urllib.parse.unquote(name).strip()
    category = Catagory.objects.filter(name__iexact=clean_name, status=0).first()
    if not category:
        category = Catagory.objects.filter(slug__iexact=clean_name, status=0).first()

    if category:
        products = Product.objects.filter(category=category)
        return render(
            request,
            "shop/products/index.html",
            {"products": products, "category_name": category.name},
        )
    else:
        messages.warning(request, "No Such Category Found")
        return redirect("collections_list")


# === 4. CART & FAVOURITES ===

@login_required(login_url="login")
def Cart_page(request):
    cart = Cart.objects.filter(user=request.user)
    total_price = CartTotalCalculator(cart).calculate_total()
    context = {"cart": cart, "total_price": total_price}
    return render(request, "shop/cart.html", context)


@login_required(login_url="login")
def add_to_cart(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if request.user.is_authenticated:
            data = json.load(request)
            product_qty = data["product_qty"]
            product_id = data["pid"]
            product_status = Product.objects.get(id=product_id)

            if product_status:
                if Cart.objects.filter(user=request.user.id, product_id=product_id):
                    return JsonResponse({"status": "Product Already in Cart"}, status=200)
                else:
                    if product_status.quantity >= product_qty:
                        Cart.objects.create(
                            user=request.user,
                            product_id=product_id,
                            product_qty=product_qty,
                        )
                        return JsonResponse({"status": "Product Added to Cart Successfully"}, status=200)
                    else:
                        return JsonResponse({"status": "Product Stock Not Available"}, status=200)
        return JsonResponse({"status": "Login to Continue"}, status=401)
    return JsonResponse({"status": "Invalid Request"}, status=400)


@login_required(login_url="login")
def remove_cart(request, cid):
    Cart.objects.filter(id=cid).delete()
    return redirect("/cart")


@login_required(login_url="login")
def Fav_page(request):
    # 1. பக்கத்தை லோட் செய்யும்போது (GET)
    if request.method == "GET":
        fav = Favourite.objects.filter(user=request.user)
        return render(request, "shop/fav.html", {"fav": fav})

    # 2. ப்ராடக்ட்டை ஃபேவரிட்டில் ஆட் செய்யும்போது (AJAX POST)
    if request.method == "POST" or request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            data = json.loads(request.body)
            product_id = data.get("pid")

            if not Product.objects.filter(id=product_id).exists():
                return JsonResponse({"status": "Product Not Found"}, status=404)

            if Favourite.objects.filter(user=request.user, product_id=product_id).exists():
                return JsonResponse({"status": "Product Already in Favourite"}, status=200)

            # 🎯 ஸ்ட்ரிங் குறிகளைத் தூக்கியாச்சு பாஸ்! ஒரிஜினல் மாடல் இப்போ வேலை செய்யும்:
            Favourite.objects.create(user=request.user, product_id=product_id)
            return JsonResponse({"status": "Product Added to Favourite"}, status=200)
            
        except Exception as e:
            print(e)  # லோக்கல் டெர்மினல்ல என்ன எர்ரர்னு பார்க்க இது உதவும் பாஸ்
            return JsonResponse({"status": "Error Processing Request"}, status=500)
            
    return JsonResponse({"status": "Invalid Request Type"}, status=400)


@login_required(login_url="login")
def remove_fav(request, fid):
    favitem = Favourite.objects.get(id=fid)
    favitem.delete()
    return redirect("Fav")


# === 5. CHECKOUT & ORDERS ===

@login_required(login_url="login")
def checkout(request):
    cartitems = Cart.objects.filter(user=request.user)
    
    if not cartitems.exists() and request.method == "GET":
        messages.warning(request, "Your cart is empty, boss!")
        return redirect("cart")

    # 🎯 [பக்கா பிக்ஸ்]: ஃபைலுக்குள்ளேயே இருக்குற கிளாஸை நேரடியாகப் பயன்படுத்துகிறோம் பாஸ்!
    total_calculator = CartTotalCalculator(cartitems)
    total_amount = total_calculator.calculate_total()

    your_upi_id = "kalaiarasi2128@okaxis" 
    merchant_name = "Kalaiarasi Metal Store"
    
    upi_payload = {
        "pa": your_upi_id,
        "pn": merchant_name,
        "am": str(total_amount),
        "cu": "INR",
        "tn": f"Payment for Order at Kalaiarasi Store"
    }
    upi_url = "upi://pay?" + urllib.parse.urlencode(upi_payload)

    # 🎯 [மரண மாஸ் செக் பாயிண்ட் பாஸ்]: கஸ்டமர் ஏற்கனவே ஏதாச்சும் ஒரு ஆர்டர் வெற்றிகரமா பண்ணியிருக்காங்களான்னு பார்க்கிறோம்!
    already_verified = Order.objects.filter(user=request.user).exists()

    if request.method == "POST":
        payment_mode = request.POST.get("payment_mode")
        transaction_id = request.POST.get("transaction_id") or request.POST.get("payment_id")
        
        if payment_mode == "COD":
            transaction_id = None
            
        pincode = request.POST.get("pincode")

        if pincode != "631208":
            return render(
                request,
                "shop/checkout.html",
                {
                    "error": "Delivery Not Available",
                    "total_amount": total_amount,
                    "upi_url": upi_url,
                    "cartitems": cartitems,
                    "already_verified": already_verified  # எரர் வந்தாலும் இந்த ஸ்டேட்டஸ் வேணும் பாஸ்
                },
            )

        form_phone = request.POST.get("phone")
        if not form_phone:
            form_phone = request.session.get('mobile_number')
            
        if not form_phone:
            form_phone = "0000000000"

        # 💾 புது ஆர்டரை உருவாக்குதல்
        order = Order.objects.create(
            user=request.user,
            order_number="ORD" + str(uuid.uuid4().hex[:8]).upper(),
            email=request.user.email,
            phone=form_phone,
            address=request.POST.get("address"),
            pincode=pincode,
            payment_mode=payment_mode,
            transaction_id=transaction_id,
            total_amount=total_amount,
        )

        for item in cartitems:
            if item.product.quantity < item.product_qty:
                messages.error(request, f"{item.product.name} stock not available")
                order.delete()
                return redirect("cart")

            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.product_qty,
                price=item.product.selling_price,
            )

            product = item.product
            product.quantity -= item.product_qty
            product.save()

        if 'mobile_number' in request.session:
            del request.session['mobile_number']

        # 🎯 [மாஸ் அன்-கமெண்ட்]: ஆர்டர் பிளேஸ் ஆனதும் கஸ்டமர் கார்ட் ஆட்டோமேட்டிக்கா காலி ஆகிடும் பாஸ்!
        cartitems.delete()
        order.save()
        return redirect("order_success")

    context = {
        "cartitems": cartitems,
        "total_amount": total_amount,
        "upi_url": upi_url,
        "already_verified": already_verified, # 🎯 இங்கதான் நம்ம HTML-க்கு டேட்டாவை அனுப்புறோம் பாஸ்!
    }
    return render(request, "shop/checkout.html", context)


def order_success(request):
    return render(request, "shop/success.html")


@login_required(login_url="login")
def myorders(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "shop/myorders.html", {"orders": orders})


@login_required(login_url="login")
def orderdetails(request, oid):
    order = get_object_or_404(Order, id=oid, user=request.user)
    orderitems = OrderItem.objects.filter(order=order)
    delivery_date = order.created_at + timedelta(days=5)
    today = date.today()
    remaining_days = (delivery_date.date() - today).days

    context = {
        "order": order,
        "orderitems": orderitems,
        'remaining_days': remaining_days,
        "delivery_date": delivery_date,
    }
    return render(request, "shop/orderdetails.html", context)


# === 6. REVIEWS & AUTHENTICATION ===

@login_required(login_url="login")
def add_review(request, product_id):
    if request.method == "POST":
        product = Product.objects.get(id=product_id)
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")
        review_image = request.FILES.get("review_image")

        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment,
            review_image=review_image,
        )
        return redirect("product_details", cname=product.category.name, pname=product.name)


def login_view(request):
    if request.method == 'POST':
        # AuthenticationForm என்பது Django-விலேயே இருக்கும் லாகின் ஃபார்ம்
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # யூசர் நேம் மற்றும் பாஸ்வேர்டு கரெக்டா இருந்தா லாகின் செய்யும்
            user = form.get_user()
            login(request, user)
            messages.success(request, "Login Successful!")
            return redirect('home') # லாகின் ஆனதும் ஹோம் பேஜுக்கு போகும்
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'shop/login.html', {'form': form})


def logout_page(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Logged out successfully")
    return redirect("/")


def register(request):
    form = CustomUserForm()
    if request.method == "POST":
        form = CustomUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration Success. You can Login Now...")
            return redirect("/login")
    return render(request, "shop/register.html", {"form": form})


# === 7. CALCULATION CLASSES ===

class TotalBase(ABC):
    @abstractmethod
    def calculate_subtotal(self):
        raise NotImplementedError

    @abstractmethod
    def calculate_tax(self):
        raise NotImplementedError

    @abstractmethod
    def calculate_total(self):
        raise NotImplementedError


class CartTotalCalculator(TotalBase):
    def __init__(self, cart_items, tax_rate=0.0, shipping_cost=0.0):
        self.cart_items = cart_items
        self.tax_rate = float(tax_rate)
        self.shipping_cost = float(shipping_cost)

    def calculate_subtotal(self):
        return sum(item.product.selling_price * item.product_qty for item in self.cart_items)

    def calculate_tax(self):
        return round(self.calculate_subtotal() * self.tax_rate, 2)

    def calculate_total(self):
        return self.calculate_subtotal() + self.calculate_tax() + self.shipping_cost

    def to_dict(self):
        subtotal = self.calculate_subtotal()
        tax = self.calculate_tax()
        return {
            "subtotal": subtotal,
            "tax": tax,
            "shipping_cost": self.shipping_cost,
            "total": subtotal + tax + self.shipping_cost,
        }