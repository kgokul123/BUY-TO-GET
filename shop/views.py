import json
import random
import uuid
import requests
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
                "message": f"வணக்கம் {name}, உங்களது காளையரசி மெட்டல் ஸ்டோர் லாகின் OTP எண்: {otp}. இது 1 நிமிடத்திற்கு மட்டுமே செல்லுபடியாகும் பாஸ்!"
            }
            
            # 💡 இங்க தான் ட்ரிக்: டைம் அவுட்டை 25 செகண்டா மாத்தியிருக்கோம்
            try:
                response = requests.post(ngrok_url, json=payload, timeout=25)
                # லோக்கல் சர்வர் சிக்னல் வாங்கிடுச்சுனாலே நமக்கு சக்சஸ் தான் பாஸ்!
                if response.status_code == 200:
                    return JsonResponse({'success': True, 'message': 'OTP sent successfully boss!'})
                else:
                    return JsonResponse({'success': False, 'message': 'Local server replied with error.'})
            except requests.exceptions.Timeout:
                # ஒருவேளை லோக்கல் சர்வர் பதில் சொல்ல லேட் ஆனாலும், மெசேஜ் சென்ட் ஆகியிருக்கும். 
                # அதனால் வெப்சைட்டை க்ளோஸ் பண்ணாம ஓடிபி பாக்ஸை ஓப்பன் பண்ண வைக்கிறோம் பாஸ்!
                return JsonResponse({'success': True, 'message': 'Timeout but OTP initiated.'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
            
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
def verify_otp(request):
    """கஸ்டமர் டைப் செய்யும் OTP-யைச் சரிபார்க்கும் புதிய ஃபங்க்ஷன் பாஸ்!"""
    if request.method == "POST":
        import json
        body = json.loads(request.body)
        mobile_number = body.get('mobile_number', '')
        user_otp = body.get('otp', '')

        clean_number = "".join([c for c in mobile_number if c.isdigit()])

        if clean_number in OTP_STORE and OTP_STORE[clean_number] == str(user_otp):
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
    
    products = Product.objects.filter(name__icontains=clean_pname, status=0).first()
    if not products:
        products = Product.objects.filter(category__name__icontains=clean_cname, status=0).first()
        
    # 🎯 இங்கிருந்து தான் பாஸ் அலைன்மென்ட் மிக முக்கியம்!
    if products:
        try:
            products = Product.objects.all()
            reviews = Review.objects.all()
        except Exception as e:
            print(e)

    context = {"products": products, "reviews": reviews}
    return render(request, 'shop/index.html', context)


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
    if request.method == "POST":
        payment_mode = request.POST.get("payment_mode")
        transaction_id = request.POST.get("transaction_id")
        if payment_mode == "COD":
            transaction_id = None
        pincode = request.POST.get("pincode")

        if pincode != "631208":
            return render(
                request,
                "shop/checkout.html",
                {"error": "Delivery Not Available"},
            )

        cartitems = Cart.objects.filter(user=request.user)
        total_calculator = CartTotalCalculator(cartitems)
        total_amount = total_calculator.calculate_total()

        form_phone = request.POST.get("phone")
        if not form_phone:
            form_phone = request.session.get('mobile_number')
            
        if not form_phone:
            form_phone = "0000000000"

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

        cartitems.delete()
        order.save()
        return redirect("order_success")

    return render(request, "shop/checkout.html")


def order_success(request):
    return render(request, "shop/success.html")


def myorders(request):
    if request.user.is_authenticated:
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