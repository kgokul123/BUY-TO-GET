const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const app = express();

app.use(express.json());

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: { 
        headless: true, 
        // 🎯 உங்க லோக்கல் குரோம் பிரௌசரை இது எடுத்துக்கும் பாஸ்!
        executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        args: ['--no-sandbox', '--disable-setuid-sandbox'] 
    }
});

// டெர்மினல்ல QR கோடு காட்டும் இடம்
client.on('qr', (qr) => {
    qrcode.generate(qr, { small: true });
    console.log('பாஸ், உங்க வாட்ஸ்அப்ல இந்த QR கோடை ஸ்கேன் பண்ணுங்க!');
});

client.on('ready', () => {
    console.log('வாட்ஸ்அப் API சர்வர் பக்காவா ரெடி பாஸ்!');
});

// 🎯 Django (Vercel)ல இருந்து வர்ற சிக்னலை வாங்கும் இடம் (API Endpoint)
app.post('/send-whatsapp', async (req, res) => {
    const { number, message } = req.body;
    
    try {
        const formattedNumber = number.includes('@c.us') ? number : `${number.replace('+', '').trim()}@c.us`;
        
        // ⚠️ வாட்ஸ்அப் பேன் ஆகாமல் இருக்க 5 செகண்ட் 'Human-like Delay'
        setTimeout(async () => {
            await client.sendMessage(formattedNumber, message);
            console.log(`மெசேஜ் அனுப்பப்பட்டது: ${number}`);
        }, 5000); 

        return res.json({ success: true, status: "Message queued with safe delay" });
    } catch (error) {
        return res.status(500).json({ success: false, error: error.message });
    }
});

// 5000 போர்ட்ல இந்த சர்வர் ஓடும்
app.listen(5000, () => console.log('API Server running on port 5000'));
client.initialize();