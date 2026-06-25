import sys
import subprocess
import time

# 🎯 தேவையான லைப்ரரிகள் இல்லைனா அதுவே ஆட்டோமேட்டிக்கா இன்ஸ்டால் பண்ணிக்கும் பாஸ்!
try:
    from flask import Flask, request, jsonify
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Flask"])
    from flask import Flask, request, jsonify

try:
    import pywhatkit as kit
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pywhatkit"])
    import pywhatkit as kit

# 🎯 ஆட்டோமேட்டிக்கா என்டர் தட்டுவதற்கு pyautogui இன்ஸ்டால் செய்கிறோம் பாஸ்!
try:
    import pyautogui
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyautogui"])
    import pyautogui

app = Flask(__name__)

@app.route('/send-whatsapp', methods=['POST'])
def send_whatsapp():
    data = request.get_json()
    number = data.get('number')
    message = data.get('message')
    
    # 💡 வாட்ஸ்அப் வெப் ஓப்பன் ஆகி மெசேஜ் அனுப்பி முடிக்க லேட் ஆகலாம், 
    # அதனால் வெப்சைட்டை காக்க வைக்காமல் உடனே ஜாங்கோவுக்கு 'சக்சஸ்' சிக்னல் அனுப்பி விடுகிறோம் பாஸ்!
    import threading
def process_whatsapp():
        try:
            # ⏳ 15 செகண்ட் தாராளமாக வெயிட் செய்து மெசேஜை டைப் செய்ய வைக்கிறோம் பாஸ்
            kit.sendwhatmsg_instantly(phone_no=number, message=message, wait_time=15, tab_close=False)
            
            # 🎯 மெசேஜ் பாக்ஸ்ல டெக்ஸ்ட் விழுந்ததும் 3 செகண்ட் வெயிட் பண்றோம்
            time.sleep(3)
            
            # 🔥 [மரண மாஸ் ட்ரிக்]: குரோம் விண்டோ முன்னாடி இல்லை என்றாலும், 
            # நேரடியாக வாட்ஸ்அப்பின் 'Send' பட்டனை கண்டுபிடித்து தானாகவே மவுஸ் மூலம் கிளிக் செய்ய வைக்கிறோம் பாஸ்!
            try:
                import pyautogui
                # வாட்ஸ்அப் வெப் சென்ட் பட்டனின் இடத்தை (Focus) உறுதி செய்ய 3 முறை Tab அமுக்குகிறோம்
                pyautogui.press('tab')
                time.sleep(0.5)
                pyautogui.press('tab')
                time.sleep(0.5)
                
                # இப்போ கன்பார்மா என்டர் தட்டுகிறோம்!
                pyautogui.press('enter')
                print(f"✓ OTP SENT SUCCESSFULLY VIA FOCUS: {number}")
            except Exception as click_error:
                # ஒருவேளை அப்படியும் டிராஃப்டா நின்றால், விண்டோவை ஆக்டிவேட் செய்து என்டர் தட்டுகிறோம்
                pyautogui.click(x=pyautogui.size().width // 2, y=pyautogui.size().height // 2)
                time.sleep(0.5)
                pyautogui.press('enter')
                print(f"✓ OTP SENT VIA CLICK BACKUP: {number}")

        except Exception as e:
            print(f"❌ OTP NOT SENT: {str(e)}")

if __name__ == '__main__':
    print("🚀 பைதான் வாட்ஸ்அப் API சர்வர் 5000 போர்ட்ல ரெடி பாஸ்!")
    app.run(port=5000)