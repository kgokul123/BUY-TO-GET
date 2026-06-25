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
            # வாட்ஸ்அப் வெப் வழியா மெசேஜை டைப் செய்ய வைக்கும்
            kit.sendwhatmsg_instantly(phone_no=number, message=message, wait_time=12, tab_close=True)
            
            # 🎯 மெசேஜ் பாக்ஸ்ல டைப் ஆகி நின்றவுடன் 2 செகண்ட் வெயிட் பண்ணி ஆட்டோமேட்டிக்கா 'Enter' அமுக்கும் ட்ரிக் பாஸ்!
            time.sleep(2)
            pyautogui.press('enter')
            print(f"✓ மெசேஜ் ஆட்டோமேட்டிக்கா சென்ட் செய்யப்பட்டது: {number}")
        except Exception as e:
            print(f"❌ மெசேஜ் அனுப்புவதில் சிக்கல்: {str(e)}")

    # தனி த்ரெட்டில் பேக்கிரவுண்டில் ரன் செய்கிறோம்
    threading.Thread(target=process_whatsapp).start()
    
    return jsonify({"success": True, "status": "Signal received boss!"}), 200

if __name__ == '__main__':
    print("🚀 பைதான் வாட்ஸ்அப் API சர்வர் 5000 போர்ட்ல ரெடி பாஸ்!")
    app.run(port=5000)