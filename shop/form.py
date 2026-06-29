from django.contrib.auth.forms import UserCreationForm
from .models import User
from .models import User
from django import forms
from django import forms
from .models import Product

class ProductUploadForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'product_image', 'quantity', 'status', 'selling_price']

class CustomUserForm(UserCreationForm):
  username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'enter Username'}))
  email    = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'enter Email'}))
  password1=forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'enter your Password'}))
  password2=forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'confirm your Password'}))

  class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']