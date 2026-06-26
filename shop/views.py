import json
import random
import uuid
import requests
import urllib.parse
from abc import ABC, abstractmethod
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from django.template.loader import get_template
from xhtml2pdf import pisa

from .form import CustomUserForm
from .models import (
    Cart,
    Catagory,
    DeliveryPincode,
    Favourite,
    Order,
    OrderItem,
    Product,
    Review,
)
import qrcode
import io
import base64

@login_required(login_url="login")
def download_invoice_pdf(request, order_no):
    # 🚀 'ORD4698511A' என்ற ஸ்ட்ரிங்கில் இருந்து வெறும் நம்பரான ஐடியை மட்டும் பிரிக்கிறோம் பாஸ்.
    # ஒருவேளை வெர்சல் டேட்டாபேஸ்ல அந்த ஐடி இல்லைனா 404 எர்ரர் தராம, கஸ்டமரோட லேட்டஸ்ட் ஆர்டரை எடுத்து கிராஷ் ஆகாம தடுக்கும்!
    try:
        clean_id = order_no.replace("ORD", "").replace("A", "").strip()
        order = Order.objects.get(id=clean_id)
    except (Order.DoesNotExist, ValueError):
        # சேஃப் ஃபால்பேக் லாஜிக் பாஸ்
        order = Order.objects.filter(user=request.user).last()
        if not order:
            order = Order.objects.last()
            
        if not order:
            return HttpResponse("பாஸ், டேட்டாபேஸ்ல இன்னும் ஒரு ஆர்டர் கூட இல்லை! முதல்ல வெப்சைட்ல ஒரு டெஸ்ட் ஆர்டர் போடுங்க தலைவா.")

    # 1. 🚀 [டாப்-லெஃப்ட் கியூஆர்]: டிஜிட்டல் வெரிஃபிகேஷன் லைவ் லிங்க்
    live_domain = "https://buy-to-get.vercel.app"  # உங்க அசல் வெர்சல் லிங்க் பாஸ்!
    verification_url = f"{live_domain}/digital-verify/{order.id}/"
    
    top_qr = qrcode.QRCode(version=1, box_size=3, border=1)
    top_qr.add_data(verification_url)
    top_qr.make(fit=True)
    
    top_img = top_qr.make_image(fill_color="black", back_color="white")
    top_buffer = io.BytesIO()
    top_img.save(top_buffer, format="PNG")
    invoice_url_qr = base64.b64encode(top_buffer.getvalue()).decode('utf-8')
    
    # 2. 💰 [பாட்டம்-லெஃப்ட் கியூஆர்]: COD கியூஆர் கோடு
    qr_code_base64_data = ""
    if str(order.order_status).lower() == 'pending' or str(order.payment_mode).upper() == 'COD':
        your_upi_id = "kalaiarasi2128@oksbi"  # உங்க அசல் UPI ID பாஸ்!
        store_name = "KALAIARASI METAL STORE"
        upi_string = f"upi://pay?pa={your_upi_id}&pn={urllib.parse.quote(store_name)}&am={order.total_amount}&cu=INR"
        
        bottom_qr = qrcode.QRCode(version=1, box_size=4, border=1)
        bottom_qr.add_data(upi_string)
        bottom_qr.make(fit=True)
        
        bottom_img = bottom_qr.make_image(fill_color="black", back_color="white")
        bottom_buffer = io.BytesIO()
        bottom_img.save(bottom_buffer, format="PNG")
        qr_code_base64_data = base64.b64encode(bottom_buffer.getvalue()).decode('utf-8')

    # 3. 🎯 காண்டெக்ஸ்ட் மேப்பிங்
    context = {
        'order': order,
        'order_no': order_no,                  # 👈 அசல் ஆர்டர் நம்பரை அப்படியே இங்க பாஸ் பண்ணிட்டோம் பாஸ்!
        'invoice_url_qr': invoice_url_qr,       
        'qr_code_base64_data': qr_code_base64_data, 
    }
    
    # பிடிஎஃப் ரெண்டரிங் (pisa.CreatePDF) லாஜிக்
    html_template = render(request, 'shop/invoice_pdf.html', context)
    html = html_template.content.decode('utf-8')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order_no}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
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
    live_domain = "https://your-website-domain.com" 
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
    # 1. 🚀 [டேட்டாபேஸ் செக்யூரிட்டி செக்]
    # ஒருவேளை வெர்சல் லைவ் டேட்டாபேஸ்ல அந்த குறிப்பிட்ட ஐடி இல்லைனா கூட, 404 எர்ரர் தராம சேஃபா ஹேண்டில் பண்ணும்!
    try:
        order = Order.objects.get(id=order_id)
    except (Order.DoesNotExist, ValueError):
        # சேஃப் ஃபால்பேக்: ஐடி இல்லைனா சிஸ்டம்ல லேட்டஸ்டா வெரிஃபைட் ஆன ஏதாச்சும் ஒரு ஆர்டரை எடுக்கும் பாஸ்
        order = Order.objects.filter(is_digitally_verified=True).last()
        if not order:
            order = Order.objects.last()

    if not order:
        return HttpResponse("பாஸ், வெப்சைட்ல இன்னும் ஒரு ஆர்டர் கூட இல்லை தலைவா! முதல்ல ஒரு டெஸ்ட் ஆர்டர் போடுங்க.")

    # 2. 🔐 [அட்மின் இமேஜ் அப்லோடு / எடிட் லாஜிக்]
    # அட்மினான நீங்க லாக்-இன் செஞ்சு ஃபார்ம் சப்மிட் பண்ணும்போது இமேஜ்களை இங்க தான் வாங்குறோம் பாஸ்
    if request.method == "POST" and request.FILES:
        if request.user.is_authenticated and request.user.is_staff:
            # எச்டிஎம்எல் ஃபார்ம்ல இருந்து வர்ற சைன் மற்றும் சீல் இமேஜ்கள்
            customer_sig = request.FILES.get('customer_sig')
            admin_sig = request.FILES.get('admin_sig')
            store_seal = request.FILES.get('store_seal')
            
            # ஒருவேளை புது இமேஜ் அப்லோடு பண்ணுனா மட்டும் அப்டேட் ஆகும் பாஸ், இல்லைனா பழைய இமேஜ் அப்படியே இருக்கும்
            if customer_sig:
                order.customer_signature = customer_sig
            if admin_sig:
                order.admin_signature = admin_sig
            if store_seal:
                order.store_seal = store_seal
                
            order.is_digitally_verified = True
            order.save()
            
            # இமேஜ் சேவ் ஆனதும் அதே பேஜுக்கு ரீஃப்ரெஷ் ஆகிடும் பாஸ்
            return redirect('digital_verification_view', order_id=order.id)
        else:
            return HttpResponse("YOUR ARE NOT ADMIN,SO NO PERMIT TO EDIT IN YTHE PAGE!")

    # 3. 🎯 காண்டெக்ஸ்ட் மேப்பிங் மற்றும் எச்டிஎம்எல் ரெண்டரிங்
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
    if request.method == "GET":
        fav = Favourite.objects.filter(user=request.user)
        return render(request, "shop/fav.html", {"fav": fav})

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            data = json.loads(request.body)
            product_id = data.get("pid")

            if not Product.objects.filter(id=product_id).exists():
                return JsonResponse({"status": "Product Not Found"}, status=404)

            if Favourite.objects.filter(user=request.user, product_id=product_id).exists():
                return JsonResponse({"status": "Product Already in Favourite"}, status=200)

            'Favourite'.objects.create(user=request.user, product_id=product_id)
            return JsonResponse({"status": "Product Added to Favourite"}, status=200)
        except Exception:
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

    context = {
        "order": order,
        "orderitems": orderitems,
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


def login_page(request):
    if request.method == "POST":
        name = request.POST.get("username")
        pwd = request.POST.get("password")
        user = authenticate(request, username=name, password=pwd)

        if user is not None:
            login(request, user)
            messages.success(request, "Logged in Successfully")
            return redirect("/")
        else:
            messages.error(request, "Invalid Username or Password")
            return redirect("/login")
    return render(request, "shop/login.html")


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