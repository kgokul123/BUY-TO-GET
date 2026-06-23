import json
import random
import uuid
from abc import ABC, abstractmethod
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
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
from django.core.management import call_command
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client




@csrf_exempt
def send_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            mobile_number = data.get('mobile_number')
            
            if not mobile_number:
                return JsonResponse({'status': 'error', 'message': 'மொபைல் எண் தேவை!'}, status=400)
            
            # ஃபயர்பேஸ் ஃபிரண்ட்-எண்டிலேயே நேரடியாக SMS அனுப்பிவிடும் பாஸ்!
            # ஜாங்கோ செஷனில் கஸ்டமரின் மொபைல் எண்ணை மட்டும் சேவ் செய்து வைக்கிறோம்.
            request.session['mobile_number'] = mobile_number
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Firebase ஓடிபி அனுப்ப தயாராக உள்ளது பாஸ்!'
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid Request'}, status=400)




def send_otp(request):
    if request.method == "POST":
        data = json.loads(request.body)
        phone = data.get("phone")
        
        # 6 இலக்க ரகசிய நம்பரை (OTP) சிஸ்டம் உருவாக்குகிறது
        otp = str(random.randint(100000, 999999))
        
        # பயனர் வெரிஃபை செய்யும் வரை தற்காலிகமாக செஷனில் (Session) சேமிக்கிறோம்
        request.session['generated_otp'] = otp
        
        # 💡 [மிக முக்கியம்]: இப்போதைக்கு டெஸ்டிங் செய்ய உங்க VS Code டெர்மினலில் (Terminal) இந்த ஓடிபி பிரிண்ட் ஆகும்!
        print(f"\n========================================\n🔥 OTP FOR {phone} IS: {otp}\n========================================\n")
        
        return JsonResponse({"success": True, "status": " OTP SENT SUCESSFULLY !"})
    return JsonResponse({"success": False, "status": "தவறான கோரிக்கை"})

# 2. பயனர் டைப் செய்த ஓடிபி சரியா என்று பார்க்கும் இடம்
def verify_otp(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_otp = data.get("otp")
        saved_otp = request.session.get('generated_otp')
        
        # இரண்டு ஓடிபி-யும் சமமாக இருக்கிறதா என்று பார்க்கிறோம்
        if saved_otp and user_otp == saved_otp:
            # வெரிஃபை ஆனவுடன் செஷனில் இருந்து ஓடிபி-யை நீக்கிவிடலாம்
            del request.session['generated_otp'] 
            return JsonResponse({"success": True, "status": "OTP VERIFY SUCESSFULLY!"})
        else:
            return JsonResponse({"success": False, "status": "WRONG OTP PLEASE OTP VERIFY AGAIN."})
            
    return JsonResponse({"success": False, "status": "Invalid Request"})




def Product_details_by_id(request, prod_id):
    # பெயருக்குப் பதிலாக ID மூலமாகத் தேடுவதால் ஸ்பேஸ் இருந்தாலும் எரர் வராது!
    products = Product.objects.get(id=prod_id)
    reviews = Review.objects.filter(product=products).order_by("-created_at")
    context = {"products": products, "reviews": reviews}
    return render(request, "shop/products/product_details.html", context)



def run_online_migration(request):
    try:
        # இது ஜாங்கோவின் 'python manage.py migrate' கமாண்ட்டை ஆன்லைன் சர்வர்ல ரன் செய்யும்
        call_command('migrate', interactive=False)
        return HttpResponse("<h1>Success: Neon Database Migrated Successfully!</h1>")
    except Exception as e:
        return HttpResponse(f"<h1>Error: {str(e)}</h1>")


# === 1. MY ORDERS PAGE (SAFE FROM ERROR) ===
def myorders(request):
    if request.user.is_authenticated:
        # பயனர் லாக்-இன் செய்திருந்தால் புதிய ஆர்டர்கள் முதலில் காட்டும்
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
    else:
        # லாக்-இன் செய்யவில்லை எனில் இணையதளம் முடங்காமல் வெற்றுப் பட்டியலை அனுப்பும்
        orders = Order.objects.none()

    return render(request, "shop/myorders.html", {"orders": orders})


# === 2. ORDER DETAILS ===
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


# === 3. ADD REVIEW ===
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

        return redirect(
            "product_details", cname=product.category.name, pname=product.name
        )


# === 4. HOME PAGE ===
def home(request):
    products = Product.objects.filter(trending=1)
    return render(request, "shop/index.html", {"products": products})


# === 5. CHECKOUT ===
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
        total_calculator = total(cartitems)
        total_amount = total_calculator.calculate_total()

        order = Order.objects.create(
            user=request.user,
            order_number="ORD" + str(uuid.uuid4().hex[:8]).upper(),
            email=request.user.email,
            phone=request.POST.get("phone"),
            address=request.POST.get("address"),
            pincode=pincode,
            payment_mode=payment_mode,
            transaction_id=transaction_id,
            total_amount=total_amount,
        )

        for item in cartitems:
            if item.product.quantity < item.product_qty:
                messages.error(
                    request, f"{item.product.name} stock not available"
                )
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

        cartitems.delete()
        order.save()
        return redirect("order_success")

    return render(request, "shop/checkout.html")


def order_success(request):
    return render(request, "shop/success.html")


# === 6. CART MANAGEMENT ===
@login_required(login_url="login")
def Cart_page(request):
    cart = Cart.objects.filter(user=request.user)
    total_price = total(cart).calculate_total()

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
                if Cart.objects.filter(
                    user=request.user.id, product_id=product_id
                ):
                    return JsonResponse(
                        {"status": "Product Added to Cart Sucessfully"},
                        status=200,
                    )
                else:
                    if product_status.quantity >= product_qty:
                        Cart.objects.create(
                            user=request.user,
                            product_id=product_id,
                            product_qty=product_qty,
                        )
                        return JsonResponse(
                            {"status": "Product Added to Cart Sucessfully"},
                            status=200,
                        )
                    else:
                        return JsonResponse(
                            {"status": "Product Stock Not Available"},
                            status=200,
                        )
        return JsonResponse({"status": "Login to Continue"}, status=401)
    return JsonResponse({"status": "Invalid Request"}, status=400)


@login_required(login_url="login")
def remove_cart(request, cid):
    Cart.objects.filter(id=cid).delete()
    return redirect("/cart")


# === 7. FAVOURITE MANAGEMENT ===
# === 5. CHECKOUT (திருத்தப்பட்ட பக்கா கோடு பாஸ்) ===
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
        total_calculator = total(cartitems)
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
                messages.error(
                    request, f"{item.product.name} stock not available"
                )
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


@login_required(login_url="login")
def remove_fav(request, fid):
    favitem = Favourite.objects.get(id=fid)
    favitem.delete()
    return redirect("Fav")


# === 8. AUTHENTICATION ===
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
            messages.error(request, "Invalid User Name or Password")
            return redirect("/login")

    return render(request, "shop/login.html")


def logout_page(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Logged out sucessfully")
    return redirect("/")


def register(request):
    form = CustomUserForm()
    if request.method == "POST":
        form = CustomUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Registration Success. You can Login Now..."
            )
            return redirect("/login")
    return render(request, "shop/register.html", {"form": form})


# === 9. PRODUCT & COLLECTIONS ===
def collections(request):
    catagory = Catagory.objects.filter(status=0)
    return render(request, "shop/collections.html", {"catagory": catagory})


from urllib.parse import unquote

def collectionsview(request, name):
    # 1. URL-ல் இருந்து வரும் %20 போன்றவற்றை சுத்தமான ஸ்பேஸாக மாற்றுகிறது
    clean_name = unquote(name).strip()
    
    # 2. கேட்டகிரி பெயர் அல்லது ஸ்லக் (Slug) மேட்ச் ஆகிறதா என்று தேடுகிறது (Case-insensitive)
    category = Catagory.objects.filter(name__iexact=clean_name, status=0).first()
    
    if not category:
        # ஒருவேளை ஸ்லக் ஃபீல்டு வச்சிருந்தா இதையும் செக் பண்ணும்
        category = Catagory.objects.filter(slug__iexact=clean_name, status=0).first()

    if category:
        # 3. சரியான கேட்டகிரி கிடைத்துவிட்டால், அதிலுள்ள தயாரிப்புகளைத் தேடுகிறது
        products = Product.objects.filter(category=category)
        return render(
            request,
            "shop/products/index.html",
            {"products": products, "category_name": category.name},
        )
    else:
        # 4. அப்படியும் இல்லை என்றால் மட்டுமே இந்த மெசேஜ் வரும்
        messages.warning(request, "No Such Category Found")
        return redirect("collections_list")


def Product_details(request, cname, pname):
    # Vercel-ல் வரும் %20 போன்ற குறியீடுகளைத் தூய்மையான ஸ்பேஸாக மாற்றுகிறது!
    clean_cname = unquote(cname).strip()
    clean_pname = unquote(pname).strip()
    
    # இப்போ டேட்டாபேஸில் தேடுகிறது
    products = Product.objects.filter(name__icontains=clean_pname, status=0).first()
    
    if not products:
        # ஒருவேளை பெயர் மேட்ச் ஆகவில்லை என்றால், அந்த கேட்டகரியில் உள்ள முதல் பொருளைக் காட்டும்
        products = Product.objects.filter(category__name__icontains=clean_cname, status=0).first()
        
    if products:
        try:
            reviews = Review.objects.filter(product=products).order_by("-created_at")
        except:
            reviews = []
            
        context = {"products": products, "reviews": reviews}
        return render(request, "shop/products/product_details.html", context)
    else:
        messages.error(request, "No Such Product Found")
        return redirect("collections_list")

# === 10. UTILITIES ===
def check_pincode(request):
    # யூசர் டைப் பண்ணுற பின்கோடை வாங்குகிறோம்
    pincode = request.GET.get("pincode", "").strip()
    
    # பின்கோடு 631208 ஆக இருந்தால் மட்டும் True (Available) என்று நேரடியா சொல்லிவிடுகிறோம்!
    if pincode == "631208":
        available = True
    else:
        available = False
        
    return JsonResponse({"available": available})


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


class total(TotalBase):

    def __init__(self, cart_items, tax_rate=0.0, shipping_cost=0.0):
        self.cart_items = cart_items
        self.tax_rate = float(tax_rate)
        self.shipping_cost = float(shipping_cost)

    def calculate_subtotal(self):
        return sum(
            item.product.selling_price * item.product_qty
            for item in self.cart_items
        )

    def calculate_tax(self):
        return round(self.calculate_subtotal() * self.tax_rate, 2)

    def calculate_total(self):
        return (
            self.calculate_subtotal() + self.calculate_tax() + self.shipping_cost
        )

    def to_dict(self):
        subtotal = self.calculate_subtotal()
        tax = self.calculate_tax()
        return {
            "subtotal": subtotal,
            "tax": tax,
            "shipping_cost": self.shipping_cost,
            "total": subtotal + tax + self.shipping_cost,
        }