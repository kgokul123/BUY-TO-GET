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

# 💡 வாட்ஸ்அப் மெசேஜ் அனுப்பும் முக்கிய பேக்கிரவுண்ட் ஃபங்க்ஷன் பாஸ்!
def process_whatsapp_background(number, message):
    try:
        print(f"🔄 வாட்ஸ்அப் வெப் ஓப்பன் ஆகிறது... எண்: {number}")
        # ⏳ 15 செகண்ட் வெயிட் செய்து மெசேஜை டைப் செய்ய வைக்கிறோம்
        kit.sendwhatmsg_instantly(phone_no=number, message=message, wait_time=15, tab_close=False)
        
        # 🎯 மெசேஜ் பாக்ஸ்ல டெக்ஸ்ட் விழுந்ததும் 3 செகண்ட் வெயிட் பண்றோம்
        time.sleep(3)
        
        # 🔥 [மரண மாஸ் ட்ரிக்]: மெசேஜ் பாக்ஸை கன்பார்மா ஆக்டிவேட் பண்ண 
        # ஸ்கிரீனின் நடுப்பகுதியில் ஒரு கிளிக்கை தட்டிவிட்டு 'Enter' அமுக்குகிறோம்!
        try:
            print("🎯 விண்டோவை போக்கஸ் செய்ய கிளிக் செய்யப்படுகிறது...")
            pyautogui.click(x=pyautogui.size().width // 2, y=pyautogui.size().height // 2)
            time.sleep(1)
            
            # இப்போ நேரடியாக 'Enter' தட்டுகிறோம்!
            pyautogui.press('enter')
            print(f"✓ OTP SENT SUCCESSFULLY VIA DIRECT ENTER: {number}")
            
        except Exception as click_error:
            # பேக்கப் பிளான்: ஒருவேளை மாறவில்லை என்றால், பழைய டேப் முறையை ட்ரை செய்கிறோம்
            pyautogui.press('tab')
            time.sleep(0.5)
            pyautogui.press('tab')
            time.sleep(0.5)
            pyautogui.press('enter')
            print(f"✓ OTP SENT VIA TAB BACKUP: {number}")

    except Exception as e:
        print(f"❌ OTP NOT SENT IN BACKGROUND: {str(e)}")

@app.route('/send-whatsapp', methods=['POST'])
def send_whatsapp():
    try:
        # 🎯 சிக்னல் வந்ததும் முதலில் டேட்டாவை பத்திரமாக எடுக்கிறோம் பாஸ்!
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data received"}), 400
            
        number = data.get('number')
        message = data.get('message')
        
        # 🎯 பேக்கிரவுண்ட் த்ரெட்டை இங்க தான் ஸ்டார்ட் பண்றோம் பாஸ்!
        threading.Thread(target=process_whatsapp_background, args=(number, message)).start()
        
        # ⚠️ மிக முக்கியம்: எந்த எரரும் இல்லாமல் உடனே பிளாஸ்க் 200 SUCCESS ரிஸ்பான்ஸ் அனுப்புகிறது பாஸ்!
        return jsonify({"success": True, "status": "Signal received boss!"}), 200
        
    except Exception as route_error:
        print(f"❌ Route Error: {str(route_error)}")
        return jsonify({"success": False, "error": str(route_error)}), 500

if __name__ == '__main__':
    print("🚀 பைதான் வாட்ஸ்அப் API சர்வர் 5000 போர்ட்ல ரெடி பாஸ்!")
    app.run(port=5000, debug=False)