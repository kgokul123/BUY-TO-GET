from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns=[
   path('', views.home, name="home"),
    path('login/', views.login_page, name="login"),
    path('logout/', views.logout_page, name="logout"),
    path('cart/', views.Cart_page, name="cart"),
    path('Fav/', views.Fav_page, name="Fav"),
    path('Favviewpage/', views.Fav_page, name="Favviewpage"),
    path('remove-fav/<int:fid>/', views.remove_fav, name='remove_fav'),
    path('register/', views.register, name="register"),
    
    # Collections மற்றும் Products பாத்துகள்
    path('collections/', views.collections, name="collections_list"),
    path('collections/<str:name>/', views.collectionsview, name="collections_view"),
    path('collections/<str:cname>/<str:pname>/', views.Product_details, name="product_details"),
    path('product-detail/<int:prod_id>/', views.Product_details_by_id, name="product_details_id"),
    path('add-to-cart/', views.add_to_cart, name="addtocart"), 
    path('deletecart/<int:cid>/', views.remove_cart, name='remove_cart'),
    path('checkout/', views.checkout, name='checkout'), # ஒரு முறை மட்டும் போதும்
    path('myorders/', views.myorders, name='myorders'),
    path('check-pincode/', views.check_pincode, name='check_pincode'),
    path('order-success/', views.order_success, name='order_success'), 
    path('add-review/<int:product_id>/', views.add_review, name='add_review'),
    path('run-mig-now/', views.run_online_migration, name='run_online_migration'),
    path('send-verification-whatsapp/', views.send_verification_whatsapp, name='send_verification_whatsapp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('check-verification-status/', views.check_verification_status, name='check_verification_status'),
    path('download-invoice/<str:order_no>/', views.download_invoice_pdf, name='download_invoice'),
    path('orderdetails/<int:oid>/', views.orderdetails, name='orderdetails')
    
]

if settings.DEBUG or not settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)