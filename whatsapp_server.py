import sys
import subprocess
import time
import threading

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

try:
    import pyautogui
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyautogui"])
    import pyautogui

app = Flask(__name__)

# 💡 எரர் வராமல் இருக்க, பேக்கிரவுண்ட் வேலை செய்யும் ஃபங்க்ஷனை தனியாகவும், ஸ்பேஸ் கரெக்ட்டாகவும் மாற்றியுள்ளேன் பாஸ்!
def process_whatsapp_background(number, message):
    try:
        # ⏳ 15 செகண்ட் தாராளமாக வெயிட் செய்து மெசேஜை டைப் செய்ய வைக்கிறோம்
        kit.sendwhatmsg_instantly(phone_no=number, message=message, wait_time=15, tab_close=False)
        
        # 🎯 மெசேஜ் பாக்ஸ்ல டெக்ஸ்ட் விழுந்ததும் 3 செகண்ட் வெயிட் பண்றோம்
        time.sleep(3)
        
        try:
            # வாட்ஸ்அப் வெப் சென்ட் பட்டனின் இடத்தை (Focus) உறுதி செய்ய 2 முறை Tab அமுக்குகிறோம்
            pyautogui.press('tab')
            time.sleep(0.5)
            pyautogui.press('tab')
            time.sleep(0.5)
            
            # இப்போ கன்பார்மா என்டர் தட்டுகிறோம்!
            pyautogui.press('enter')
            print(f"✓ OTP SENT SUCCESSFULLY VIA FOCUS: {number}")
        except Exception as click_error:
            # ஒருவேளை அப்படியும் டிராஃப்டா நின்றால், ஸ்கிரீனின் நடுப்பகுதியை கிளிக் செய்து என்டர் தட்டுகிறோம்
            pyautogui.click(x=pyautogui.size().width // 2, y=pyautogui.size().height // 2)
            time.sleep(0.5)
            pyautogui.press('enter')
            print(f"✓ OTP SENT VIA CLICK BACKUP: {number}")

    except Exception as e:
        print(f"❌ OTP NOT SENT: {str(e)}")

@app.route('/send-whatsapp', methods=['POST'])
def send_whatsapp():
    try:
        data = request.get_json()
        number = data.get('number')
        message = data.get('message')
        
        # 🎯 பேக்கிரவுண்ட் த்ரெட்டை இங்க தான் ஸ்டார்ட் பண்றோம் பாஸ்!
        threading.Thread(target=process_whatsapp_background, args=(number, message)).start()
        
        # ⚠️ ஜாங்கோ வெப்சைட்டுக்கு உடனே சரியான சக்சஸ் ரிஸ்பான்ஸ் அனுப்பி விடுகிறோம்!
        return jsonify({"success": True, "status": "Signal received boss!"}), 200
        
    except Exception as route_error:
        print(f"❌ Route Error: {str(route_error)}")
        return jsonify({"success": False, "error": str(route_error)}), 500

if __name__ == '__main__':
    print("🚀 பைதான் வாட்ஸ்அப் API சர்வர் 5000 போர்ட்ல ரெடி பாஸ்!")
    app.run(port=5000)