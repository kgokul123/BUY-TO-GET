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
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command

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

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Order, Cart, Product # உங்க மாடல் பெயர்களை செக் பண்ணிக்கோங்க பாஸ்
import random
from django.shortcuts import get_object_or_404
from .models import Order # உங்க மாடல் பெயர்களை செக் பண்ணிக்கோங்க பாஸ்



@login_required(login_url='loginpage')
def orderdetails(request, oid):
    # கஸ்டமரோட ஐடி மற்றும் ஆர்டர் ஐடியை வச்சு துல்லியமா அந்த ஒரு ஆர்டரை மட்டும் எடுக்கிறோம் பாஸ்
    order = get_object_or_404(Order, id=oid, user=request.user)
    
    context = {
        'order': order
    }
    return render(request, "shop/orderdetails.html", context)


def placeorder(request):
    if request.method == 'POST':
        # 1. ஃபார்ம்ல இருந்து கஸ்டமர் டேட்டாவை எடுக்குறோம் பாஸ்
        # (பெயர், அட்ரஸ் ஃபீல்டுகள் உங்க கோடுக்கு ஏத்த மாதிரி மாத்திக்கோங்க)
        payment_mode = request.POST.get('payment_mode')
        
        # 2. ஒரு புதிய ஆர்டர் ஆப்ஜெக்ட் கிரியேட் பண்றோம் பாஸ்
        neworder = Order()
        neworder.user = request.user
        
        # கஸ்டமரோட மத்த விபரங்கள் (உதாரணத்திற்கு)
        neworder.fname = request.POST.get('fname')
        neworder.lname = request.POST.get('lname')
        neworder.email = request.POST.get('email')
        neworder.phone = request.POST.get('phone')
        neworder.address = request.POST.get('address')
        
        # கார்ட் டோட்டல் அமௌன்ட் (உங்க கார்ட் லாஜிக் படி இங்க வரும் பாஸ்)
        # neworder.total_price = total_price 

        # 🎯 [மெயின் மேஜிக்]: பேமெண்ட் மோட் என்னன்னு செக் பண்ணி சேவ் பண்றோம் பாஸ்!
        neworder.payment_mode = payment_mode
        
        if payment_mode == "UPI":
            neworder.payment_id = request.POST.get('payment_id') # 12 டிஜிட் UPI Ref No
            
            # ஒருவேளை கஸ்டமர் ஸ்கிரீன்ஷாட் அப்லோட் பண்ணியிருந்தா அதை வாங்குறோம் பாஸ்
            if request.FILES.get('payment_screenshot'):
                neworder.payment_screenshot = request.FILES.get('payment_screenshot')
            
            # UPI-க்கு ஆர்டர் ஸ்டேட்டஸ் முதல்ல 'Pending' அல்லது 'Hold'-ல் வைக்கலாம் (நாம செக் பண்ற வரைக்கும்)
            neworder.status = 'Pending' 
            
        elif payment_mode == "COD":
            neworder.payment_id = "COD_ORDER_" + str(random.randint(111111, 999999))
            neworder.status = 'Approved' # COD ஆர்டரை நேரடியாக கன்பார்ம் பண்ணிக்கலாம் பாஸ்
        
        # ஆர்டர் நம்பர் ஜெனரேட் பண்ணுவது
        trackno = 'kalaiarasi' + str(random.randint(1111111, 9999999))
        while Order.objects.filter(tracking_no=trackno).exists():
            trackno = 'kalaiarasi' + str(random.randint(1111111, 9999999))
        neworder.tracking_no = trackno
        
        neworder.save() # 🚀 டேட்டாபேஸ்ல ஆர்டர் மாஸா சேவ் ஆகிடும் பாஸ்!
        
        # 3. ஆர்டர் முடிஞ்சதும் கார்டை காலி பண்ணிட்டு கஸ்டமரை சக்சஸ் பேஜுக்கு அனுப்பலாம் பா&b
        # Cart.objects.filter(user=request.user).delete()
        
        messages.success(request, f"Order placed successfully! Tracking No: {trackno}")
        return redirect('my_orders') # அல்லது உங்க 'success' யூஆர்எல்க்கு ரீடைரக்ட் பண்ணுங்க பாஸ்
        
    return redirect('checkout')



OTP_STORE = {}

@csrf_exempt
def send_verification_whatsapp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            mobile_number = data.get('mobile_number')
            name = data.get('name')
            
            # 6 இலக்க OTP உருவாக்கம்
            otp = str(random.randint(100000, 999999))
            OTP_STORE[mobile_number] = otp
            
            # உங்க மாஸான Ngrok லிங்க் பாஸ்
            ngrok_url = "https://ludicrous-slighting-negligent.ngrok-free.dev/send-whatsapp"
            
            payload = {
                "number": mobile_number,
                "message": f"WELCOME {name}, YOUR KALAIARASI METAL STORE OTP NUMBER IS: {otp}. IN THE OTP IS EXPIRED IN ONLY 2 MINUTES!"
            }
            
            # 💡 [மரண மாஸ் ட்ரிக்]: லோக்கல் சர்வர் வாட்ஸ்அப்பை ஓப்பன் பண்ணும் வரை ஆன்லைன் வெப்சைட் காத்துக்கொண்டிருக்கத் தேவையில்லை!
            # சிக்னலை அனுப்பிவிட்டு, லோக்கல் சர்வர் பதில் சொல்வதற்கு முன்பே வெப்சைட்டில் ஓடிபி பாக்ஸை ஓப்பன் செய்ய வைக்கிறோம் பாஸ்!
            try:
                requests.post(ngrok_url, json=payload, timeout=2) # 2 செகண்டில் சிக்னலை மட்டும் அனுப்பிவிட்டு வெளியே வந்துவிடும்!
                return JsonResponse({'success': True, 'message': 'OTP initiated boss!'})
            except requests.exceptions.Timeout:
                # டைம் அவுட் ஆனாலும் சிக்னல் லோக்கல் சர்வருக்குப் போயிருக்கும், அதனால் இதையும் சக்சஸ் என்றே கணக்கில் கொள்வோம்!
                return JsonResponse({'success': True, 'message': 'OTP initiated successfully boss!'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
            
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        import json
        body = json.loads(request.body)
        mobile_number = body.get('mobile_number', '')
        user_otp = body.get('otp', '')

        # 💡 போன் நம்பரில் இருக்கும் எண்களை (0-9) மட்டும் பிரித்து எடுக்கிறோம் பாஸ்! (+91 இருந்தாலும், வெறும் 10 இலக்கம் இருந்தாலும் சரி)
        clean_number = "".join([c for c in str(mobile_number) if c.isdigit()])
        
        # இந்திய கண்ட்ரி கோடு (91) முன்னாடி இருந்தால் அதை நீக்கிவிட்டு லோக்கல் நம்பரை மட்டும் எடுக்கிறோம்
        if clean_number.startswith('91') and len(clean_number) > 10:
            clean_number = clean_number[2:]

        # OTP_STORE-ல் இருக்கும் எண்களையும் இதே போல் கிளீன் செய்து செக் செய்கிறோம் பாஸ்
        matched_otp = None
        for key, stored_otp in OTP_STORE.items():
            clean_key = "".join([c for c in str(key) if c.isdigit()])
            if clean_key.startswith('91') and len(clean_key) > 10:
                clean_key = clean_key[2:]
            
            if clean_key == clean_number:
                matched_otp = stored_otp
                break

        # ஓடிபி சரியாக இருந்தால் ஓகே சொல்லி விடுகிறோம்!
        if matched_otp and str(matched_otp).strip() == str(user_otp).strip():
            return JsonResponse({"success": True, "message": "OTP Verified!"})
        
        return JsonResponse({"success": False, "message": "தவறான OTP எண் பாஸ்! மீண்டும் முயலவும்."})


# 🎯 HTML பக்கத்தில் இருக்குற ஜாவாஸ்கிரிப்ட் டைமர் வந்து செக் செய்யும் இடம்
def check_verification_status(request):
    phone = request.GET.get('mobile_number')
    if phone in VERIFICATION_STORE and VERIFICATION_STORE[phone]['verified']:
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
    from urllib.parse import unquote
    clean_cname = unquote(cname).strip()
    clean_pname = unquote(pname).strip()
    
    # 💡 1. டேட்டாபேஸ்ல இருந்து குறிப்பிட்ட அந்த ஒரு ப்ராடக்ட்டை மட்டும் எடுக்கிறோம் பாஸ்!
    single_product = Product.objects.filter(name__icontains=clean_pname, status=0).first()
    
    # 💡 2. ஒருவேளை பெயர்ல கிடைக்கலனா, கலெக்ஷன் பெயரை வச்சு தேடுறோம்
    if not single_product:
        single_product = Product.objects.filter(category__name__icontains=clean_cname, status=0).first()
        
    reviews = []
    # 💡 3. ப்ராடக்ட் கிடைச்சதும், அதோட ரிவியூக்களை மட்டும் தனியா ஃபில்டர் பண்றோம் பாஸ்
    if single_product:
        try:
            reviews = Review.objects.filter(product=single_product)
        except Exception as e:
            print(e)

    # 🎯 [மரண மாஸ் பிக்ஸ்]: HTML-ல் தேடுற மாதிரி "products" கீ-யையும், 
    # கரெக்ட்டான சப்-ஃபோல்டர் பாத்தையும் (shop/products/product_details.html) இங்க வச்சுட்டோம் பாஸ்!
    context = {
        "products": single_product, 
        "reviews": reviews
    }
    return render(request, 'shop/products/product_details.html', context)
  


def collections(request):
    catagory = Catagory.objects.filter(status=0)
    return render(request, "shop/collections.html", {"catagory": catagory})


def collectionsview(request, name):
    from urllib.parse import unquote
    clean_name = unquote(name).strip()
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
                    return JsonResponse({"status": "Product Added to Cart Successfully"}, status=200)
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

            Favourite.objects.create(user=request.user, product_id=product_id)
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
    # 🛒 கார்ட் ஐட்டம்களை முதலிலேயே எடுத்து வச்சுக்கிறோம் பாஸ் (GET மற்றும் POST இரண்டுக்கும் தேவை)
    cartitems = Cart.objects.filter(user=request.user)
    
    # கார்ட்டில் பொருட்கள் ஏதும் இல்லை என்றால் செக்அவுட் செய்ய விடாமல் கார்ட் பக்கத்திற்கே திருப்புவது நல்லது பாஸ்
    if not cartitems.exists() and request.method == "GET":
        messages.warning(request, "Your cart is empty, boss!")
        return redirect("cart")

    # 🎯 [கியூஆர் கோடு & Intent மேஜிக் லாஜிக் - பாஸ்]:
    # உங்க கார்ட் டோட்டலை கணக்கிட்டு அதற்கான UPI URL-ஐ ரெடி பண்றோம்
    from .utils import CartTotalCalculator # உங்க கால்குலேட்டர் ஃபைல் இம்போர்ட் பாத்
    total_calculator = CartTotalCalculator(cartitems)
    total_amount = total_calculator.calculate_total()

    # 💡 [மிக முக்கியம்]: உங்க அட்மின் ஸ்கிரீன்ஷாட்ல பார்த்த அதே UPI ID இங்க கொடுத்திருக்கேன் பாஸ்!
    your_upi_id = "kalaiarasi2128@okaxis" 
    merchant_name = "Kalaiarasi Metal Store"
    
    upi_payload = {
        "pa": your_upi_id,
        "pn": merchant_name,
        "am": str(total_amount), # டோட்டல் பில் அமௌன்ட் ஆட்டோமேட்டிக்கா இங்க உக்காந்துடும் பாஸ்
        "cu": "INR",
        "tn": f"Payment for Order at Kalaiarasi Store"
    }
    # கூகுள் API கியூஆர் கோடு மற்றும் மொபைல் ஆப்ஸ் ஓப்பன் பண்ண இந்த லிங்க் தான் பயன்படும் பாஸ்
    upi_url = "upi://pay?" + urllib.parse.urlencode(upi_payload)


    # 🚀 1. கஸ்டமர் "Place Order" பட்டன் கிளிக் பண்ணும்போது (POST Method)
    if request.method == "POST":
        payment_mode = request.POST.get("payment_mode")
        
        # 💡 உங்க ஃபார்ம்ல 'payment_id' அல்லது 'transaction_id' எதை கொடுத்திருந்தாலும் சேஃபா எடுக்கும்படி செஞ்சிருக்கேன் பாஸ்
        transaction_id = request.POST.get("transaction_id") or request.POST.get("payment_id")
        
        if payment_mode == "COD":
            transaction_id = None
            
        pincode = request.POST.get("pincode")

        # 📍 பின்கோடு டெலிவரி செக்கிங் லாஜிக் (உங்க ஒரிஜினல் கோடு பாஸ்)
        if pincode != "631208":
            return render(
                request,
                "shop/checkout.html",
                {
                    "error": "Delivery Not Available",
                    "total_amount": total_amount,
                    "upi_url": upi_url,
                    "cartitems": cartitems
                },
            )

        form_phone = request.POST.get("phone")
        if not form_phone:
            form_phone = request.session.get('mobile_number')
            
        if not form_phone:
            form_phone = "0000000000"

        # 💾 புது ஆர்டரை டேட்டாபேஸில் கிரியேட் செய்கிறோம் பாஸ்
        order = Order.objects.create(
            user=request.user,
            order_number="ORD" + str(uuid.uuid4().hex[:8]).upper(),
            email=request.user.email,
            phone=form_phone,
            address=request.POST.get("address"),
            pincode=pincode,
            payment_mode=payment_mode,
            transaction_id=transaction_id, # மாடல் ஃபீல்டு பெயருக்கு ஏத்த மாதிரி சேவ் ஆகும்
            total_amount=total_amount,
        )

        # 📦 ஸ்டாக் செக்கிங் மற்றும் மைனஸ் செய்யும் லூப் லாஜிக் (உங்க ஒரிஜினல் கோடு பாஸ்)
        for item in cartitems:
            if item.product.quantity < item.product_qty:
                messages.error(request, f"{item.product.name} stock not available")
                order.delete() # ஆர்டரை கேன்சல் பண்ணிட்டு திருப்புகிறோம் பாஸ்
                return redirect("cart")

            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.product_qty,
                price=item.product.selling_price,
            )

            # ஸ்டாக்கை குறைப்பது
            product = item.product
            product.quantity -= item.product_qty
            product.save()

        # செஷன் மற்றும் கார்டை காலி செய்வது
        if 'mobile_number' in request.session:
            del request.session['mobile_number']

        cartitems.delete()
        order.save()
        return redirect("order_success")

    # 🚀 2. கஸ்டமர் செக்அவுட் பக்கத்தை சும்மா ஓப்பன் பண்ணும்போது (GET Method)
    context = {
        "cartitems": cartitems,
        "total_amount": total_amount,
        "upi_url": upi_url, # 🎯 இந்த வேரியபிள்தான் உங்க HTML-ல் QR கோடாக மாறும் பாஸ்!
    }
    return render(request, "shop/checkout.html", context)


def order_success(request):
    return render(request, "shop/success.html")

@login_required(login_url="login")
def myorders(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-id')
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
    else:
        orders = Order.objects.none()
    return render(request, "shop/myorders.html", {"orders": orders})


@login_required(login_url="login")
def orderdetails(request, oid):
    order = Order.objects.get(id=oid, user=request.user)
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