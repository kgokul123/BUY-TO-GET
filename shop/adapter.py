from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import redirect
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

User = get_user_model()

class RestrictNewSocialUsersAdapter(DefaultSocialAccountAdapter):
    
    def pre_social_login(self, request, sociallogin):
        # 💡 கூகுள் டோக்கன் ஓகே ஆகி உள்ளே வரும்போது ஃபர்ஸ்ட் செக் பாஸ்
        email = sociallogin.user.email
        
        # 🎯 [பக்கா பிசினஸ் லாக்]: டேட்டாபேஸ்ல அக்கவுண்ட் இல்லைனா...
        if not User.objects.filter(email=email).exists():
            # 1. அழகான அலர்ட் மெசேஜை செட் பண்றோம் பாஸ்
            messages.error(
                request, 
                "Your Google account has not been registered yet! Please register in your account"
            )
            # 2. லாக்-இன் பக்கத்துக்கே திருப்பி விடுறோம்
            raise ImmediateHttpResponse(redirect('/login/'))
            
            
            
        
            
        
            
            
            