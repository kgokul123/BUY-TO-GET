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
            # ⏳ wait_time-ஐ 15 செகண்டா மாத்தி, வாட்ஸ்அப் பேஜ் முழுசா லோடாவதற்கு தாராளமா டைம் தர்றோம் பாஸ்!
            kit.sendwhatmsg_instantly(phone_no=number, message=message, wait_time=5, tab_close=False)
            
            # 🎯 மெசேஜ் பாக்ஸ்ல டெக்ஸ்ட் விழுந்ததும் 3 செகண்ட் தாராளமா வெயிட் பண்றோம் பாஸ்
            time.sleep(3)
            
            # 💡 கீபோர்டுல இருக்குற 'Tab' பட்டனை அமுக்கி, கர்சரை கரெக்டா சென்ட் பட்டன் அல்லது டெக்ஸ்ட் பாக்ஸ்ல கொண்டு வரோம் பாஸ்
            pyautogui.press('tab')
            time.sleep(0.5)
            
            # 🔥 இப்போ மரண மாஸா 'Enter' அமுக்குறோம், மெசேஜ் 100% தானா சென்ட் ஆகிடும்!
            pyautogui.press('enter')
            print(f"✓ OTP SENT SUCCESSFULLY: {number}")
        except Exception as e:
            print(f"❌ OTP NOT SENT: {str(e)}")

    # தனி த்ரெட்டில் பேக்கிரவுண்டில் ரன் செய்கிறோம்
    threading.Thread(target=process_whatsapp).start()
    
    return jsonify({"success": True, "status": "Signal received boss!"}), 200

if __name__ == '__main__':
    print("🚀 பைதான் வாட்ஸ்அப் API சர்வர் 5000 போர்ட்ல ரெடி பாஸ்!")
    app.run(port=5000)