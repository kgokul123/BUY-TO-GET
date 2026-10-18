from django.shortcuts import redirect
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin

class RestrictSocialSignupMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 💡 ஆல்-ஆத் அந்த மொட்டை வெள்ளை பக்கங்களுக்கு (Sign Up அல்லது Failure) பிரௌசரை தள்ளும்போது...
        if request.path in ['/accounts/3rdparty/signup/', '/accounts/social/signup/', '/accounts/social/login/cancelled/']:
            
            # 1. அழகான ரெட் அலர்ட் மெசேஜை செட் பண்றோம் பாஸ்
            messages.error(
                request, 
                "Your Google account has not been registered yet! Please register in your account"
            )
            # 2. அந்த மொட்டை வெள்ளை பக்கங்களை யூசர் கண்ணுல காட்டாம ஸ்ட்ரெயிட்டா லாக்-இன் பக்கத்துக்குத் திருப்பி விடுறோம்!
            return redirect('/login/')