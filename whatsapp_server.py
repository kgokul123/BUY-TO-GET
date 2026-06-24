import sys
import subprocess

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

app = Flask(__name__)

@app.route('/send-whatsapp', methods=['POST'])
def send_whatsapp():
    data = request.get_json()
    number = data.get('number')
    message = data.get('message')
    
    try:
        # வாட்ஸ்அப் வெப் வழியா மெசேஜை உடனே அனுப்பும்
        kit.sendwhatmsg_instantly(phone_no=number, message=message, wait_time=15, tab_close=True)
        print(f"✓ மெசேஜ் அனுப்பப்பட்டது: {number}")
        return jsonify({"success": True, "status": "Message sent successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 பைதான் வாட்ஸ்அப் API சர்வர் 5000 போர்ட்ல ரெடி பாஸ்!")
    app.run(port=5000)