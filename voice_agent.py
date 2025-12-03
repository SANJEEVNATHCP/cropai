"""
AI Voice Agent Routes - Agricultural AI Assistant powered by Google Gemini
Multi-Language Support: Hindi, English, Marathi, Telugu, Tamil, Kannada, Bengali, Gujarati, Punjabi
"""
from flask import Blueprint, request, jsonify
import requests as http_requests
import random
import os

voice_agent_bp = Blueprint('voice_agent', __name__)

# Google Gemini API Key - Load from environment variable
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = 'gemini-2.0-flash'

# Supported Languages with their codes and names
SUPPORTED_LANGUAGES = {
    'en': {'name': 'English', 'native': 'English', 'speech_code': 'en-IN'},
    'hi': {'name': 'Hindi', 'native': 'हिंदी', 'speech_code': 'hi-IN'},
    'mr': {'name': 'Marathi', 'native': 'मराठी', 'speech_code': 'mr-IN'},
    'te': {'name': 'Telugu', 'native': 'తెలుగు', 'speech_code': 'te-IN'},
    'ta': {'name': 'Tamil', 'native': 'தமிழ்', 'speech_code': 'ta-IN'},
    'kn': {'name': 'Kannada', 'native': 'ಕನ್ನಡ', 'speech_code': 'kn-IN'},
    'bn': {'name': 'Bengali', 'native': 'বাংলা', 'speech_code': 'bn-IN'},
    'gu': {'name': 'Gujarati', 'native': 'ગુજરાતી', 'speech_code': 'gu-IN'},
    'pa': {'name': 'Punjabi', 'native': 'ਪੰਜਾਬੀ', 'speech_code': 'pa-IN'},
    'od': {'name': 'Odia', 'native': 'ଓଡ଼ିଆ', 'speech_code': 'or-IN'},
    'ml': {'name': 'Malayalam', 'native': 'മലയാളം', 'speech_code': 'ml-IN'},
}

# Language-specific greetings and UI text
UI_TRANSLATIONS = {
    'en': {
        'welcome': "Hello! I'm GreenMind AI, your agricultural assistant.",
        'ready': 'Ready to help you',
        'listening': 'Listening... Speak now',
        'thinking': 'Thinking...',
        'speaking': 'Speaking...',
        'mic_prompt': 'Click the mic to start speaking',
        'type_prompt': 'Type your question or click mic to speak...',
        'quick_questions': 'Quick Questions',
        'about': 'About GreenMind AI',
        'topics': 'I Can Help With',
        'session_stats': 'Session Stats',
        'questions_asked': 'Questions Asked',
        'session_time': 'Session Time',
        'select_language': 'Select Language',
        'voice_agent': 'AI Voice Agent',
        'talk_expert': 'Talk to our AI expert for instant farming advice',
        'ai_powered': 'AI-Powered',
        'google_gemini': 'Google Gemini AI',
        'voice_enabled': 'Voice Enabled',
        'speak_to_get': 'Speak to get answers',
        'farming_expert': 'Farming Expert',
        'crops_soil_weather': 'Crops, soil, weather & schemes'
    },
    'hi': {
        'welcome': "नमस्ते! मैं GreenMind AI हूं, आपका कृषि सहायक।",
        'ready': 'आपकी मदद के लिए तैयार',
        'listening': 'सुन रहा हूं... अब बोलें',
        'thinking': 'सोच रहा हूं...',
        'speaking': 'बोल रहा हूं...',
        'mic_prompt': 'बोलने के लिए माइक पर क्लिक करें',
        'type_prompt': 'अपना सवाल टाइप करें या माइक पर क्लिक करें...',
        'quick_questions': 'त्वरित प्रश्न',
        'about': 'कृषि AI के बारे में',
        'topics': 'मैं इनमें मदद कर सकता हूं',
        'session_stats': 'सत्र आंकड़े',
        'questions_asked': 'पूछे गए प्रश्न',
        'session_time': 'सत्र समय',
        'select_language': 'भाषा चुनें',
        'voice_agent': 'AI वॉइस एजेंट',
        'talk_expert': 'तुरंत खेती की सलाह के लिए हमारे AI विशेषज्ञ से बात करें',
        'ai_powered': 'AI-संचालित',
        'google_gemini': 'Google Gemini AI',
        'voice_enabled': 'आवाज सक्षम',
        'speak_to_get': 'उत्तर पाने के लिए बोलें',
        'farming_expert': 'खेती विशेषज्ञ',
        'crops_soil_weather': 'फसलें, मिट्टी, मौसम और योजनाएं'
    },
    'mr': {
        'welcome': "नमस्कार! मी कृषी AI आहे, तुमचा कृषी सहाय्यक.",
        'ready': 'तुमच्या मदतीसाठी तयार',
        'listening': 'ऐकत आहे... आता बोला',
        'thinking': 'विचार करत आहे...',
        'speaking': 'बोलत आहे...',
        'mic_prompt': 'बोलण्यासाठी माइकवर क्लिक करा',
        'type_prompt': 'तुमचा प्रश्न टाइप करा किंवा माइकवर क्लिक करा...',
        'quick_questions': 'द्रुत प्रश्न',
        'about': 'कृषी AI बद्दल',
        'topics': 'मी यात मदत करू शकतो',
        'session_stats': 'सत्र आकडेवारी',
        'questions_asked': 'विचारलेले प्रश्न',
        'session_time': 'सत्र वेळ',
        'select_language': 'भाषा निवडा',
        'voice_agent': 'AI व्हॉइस एजंट',
        'talk_expert': 'त्वरित शेती सल्ल्यासाठी आमच्या AI तज्ञाशी बोला'
    },
    'te': {
        'welcome': "నమస్కారం! నేను కృషి AI, మీ వ్యవసాయ సహాయకుడు.",
        'ready': 'మీకు సహాయం చేయడానికి సిద్ధంగా ఉన్నాను',
        'listening': 'వింటున్నాను... ఇప్పుడు మాట్లాడండి',
        'thinking': 'ఆలోచిస్తున్నాను...',
        'speaking': 'మాట్లాడుతున్నాను...',
        'mic_prompt': 'మాట్లాడటానికి మైక్ పై క్లిక్ చేయండి',
        'type_prompt': 'మీ ప్రశ్నను టైప్ చేయండి లేదా మైక్ పై క్లిక్ చేయండి...',
        'quick_questions': 'త్వరిత ప్రశ్నలు',
        'about': 'కృషి AI గురించి',
        'topics': 'నేను వీటిలో సహాయం చేయగలను',
        'session_stats': 'సెషన్ గణాంకాలు',
        'questions_asked': 'అడిగిన ప్రశ్నలు',
        'session_time': 'సెషన్ సమయం',
        'select_language': 'భాష ఎంచుకోండి',
        'voice_agent': 'AI వాయిస్ ఏజెంట్',
        'talk_expert': 'తక్షణ వ్యవసాయ సలహా కోసం మా AI నిపుణుడితో మాట్లాడండి'
    },
    'ta': {
        'welcome': "வணக்கம்! நான் கிருஷி AI, உங்கள் விவசாய உதவியாளர்.",
        'ready': 'உங்களுக்கு உதவ தயாராக உள்ளேன்',
        'listening': 'கேட்கிறேன்... இப்போது பேசுங்கள்',
        'thinking': 'யோசிக்கிறேன்...',
        'speaking': 'பேசுகிறேன்...',
        'mic_prompt': 'பேச மைக்கை கிளிக் செய்யவும்',
        'type_prompt': 'உங்கள் கேள்வியை தட்டச்சு செய்யவும் அல்லது மைக்கை கிளிக் செய்யவும்...',
        'quick_questions': 'விரைவு கேள்விகள்',
        'about': 'கிருஷி AI பற்றி',
        'topics': 'நான் இவற்றில் உதவ முடியும்',
        'session_stats': 'அமர்வு புள்ளிவிவரங்கள்',
        'questions_asked': 'கேட்ட கேள்விகள்',
        'session_time': 'அமர்வு நேரம்',
        'select_language': 'மொழியைத் தேர்ந்தெடுக்கவும்',
        'voice_agent': 'AI குரல் முகவர்',
        'talk_expert': 'உடனடி விவசாய ஆலோசனைக்கு எங்கள் AI நிபுணரிடம் பேசுங்கள்',
        'ai_powered': 'AI-இயங்கும்',
        'google_gemini': 'Google Gemini AI',
        'voice_enabled': 'குரல் இயக்கப்பட்டது',
        'speak_to_get': 'பதில்களைப் பெற பேசுங்கள்',
        'farming_expert': 'விவசாய நிபுணர்',
        'crops_soil_weather': 'பயிர்கள், மண், வானிலை மற்றும் திட்டங்கள்'
    },
    'kn': {
        'welcome': "ನಮಸ್ಕಾರ! ನಾನು ಕೃಷಿ AI, ನಿಮ್ಮ ಕೃಷಿ ಸಹಾಯಕ.",
        'ready': 'ನಿಮಗೆ ಸಹಾಯ ಮಾಡಲು ಸಿದ್ಧ',
        'listening': 'ಕೇಳುತ್ತಿದ್ದೇನೆ... ಈಗ ಮಾತನಾಡಿ',
        'thinking': 'ಯೋಚಿಸುತ್ತಿದ್ದೇನೆ...',
        'speaking': 'ಮಾತನಾಡುತ್ತಿದ್ದೇನೆ...',
        'mic_prompt': 'ಮಾತನಾಡಲು ಮೈಕ್ ಮೇಲೆ ಕ್ಲಿಕ್ ಮಾಡಿ',
        'type_prompt': 'ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ ಅಥವಾ ಮೈಕ್ ಮೇಲೆ ಕ್ಲಿಕ್ ಮಾಡಿ...',
        'quick_questions': 'ತ್ವರಿತ ಪ್ರಶ್ನೆಗಳು',
        'about': 'ಕೃಷಿ AI ಬಗ್ಗೆ',
        'topics': 'ನಾನು ಇವುಗಳಲ್ಲಿ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ',
        'session_stats': 'ಅಧಿವೇಶನ ಅಂಕಿಅಂಶಗಳು',
        'questions_asked': 'ಕೇಳಿದ ಪ್ರಶ್ನೆಗಳು',
        'session_time': 'ಅಧಿವೇಶನ ಸಮಯ',
        'select_language': 'ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ',
        'voice_agent': 'AI ಧ್ವನಿ ಏಜೆಂಟ್',
        'talk_expert': 'ತಕ್ಷಣದ ಕೃಷಿ ಸಲಹೆಗಾಗಿ ನಮ್ಮ AI ತಜ್ಞರೊಂದಿಗೆ ಮಾತನಾಡಿ'
    },
    'bn': {
        'welcome': "নমস্কার! আমি কৃষি AI, আপনার কৃষি সহায়ক।",
        'ready': 'আপনাকে সাহায্য করতে প্রস্তুত',
        'listening': 'শুনছি... এখন বলুন',
        'thinking': 'ভাবছি...',
        'speaking': 'বলছি...',
        'mic_prompt': 'কথা বলতে মাইকে ক্লিক করুন',
        'type_prompt': 'আপনার প্রশ্ন টাইপ করুন বা মাইকে ক্লিক করুন...',
        'quick_questions': 'দ্রুত প্রশ্ন',
        'about': 'কৃষি AI সম্পর্কে',
        'topics': 'আমি এতে সাহায্য করতে পারি',
        'session_stats': 'সেশন পরিসংখ্যান',
        'questions_asked': 'জিজ্ঞাসিত প্রশ্ন',
        'session_time': 'সেশন সময়',
        'select_language': 'ভাষা নির্বাচন করুন',
        'voice_agent': 'AI ভয়েস এজেন্ট',
        'talk_expert': 'তাৎক্ষণিক কৃষি পরামর্শের জন্য আমাদের AI বিশেষজ্ঞের সাথে কথা বলুন'
    },
    'gu': {
        'welcome': "નમસ્તે! હું કૃષિ AI છું, તમારો કૃષિ સહાયક.",
        'ready': 'તમારી મદદ કરવા તૈયાર',
        'listening': 'સાંભળી રહ્યો છું... હવે બોલો',
        'thinking': 'વિચારી રહ્યો છું...',
        'speaking': 'બોલી રહ્યો છું...',
        'mic_prompt': 'બોલવા માટે માઇક પર ક્લિક કરો',
        'type_prompt': 'તમારો પ્રશ્ન ટાઇપ કરો અથવા માઇક પર ક્લિક કરો...',
        'quick_questions': 'ઝડપી પ્રશ્નો',
        'about': 'કૃષિ AI વિશે',
        'topics': 'હું આમાં મદદ કરી શકું છું',
        'session_stats': 'સત્ર આંકડા',
        'questions_asked': 'પૂછેલા પ્રશ્નો',
        'session_time': 'સત્ર સમય',
        'select_language': 'ભાષા પસંદ કરો',
        'voice_agent': 'AI વૉઇસ એજન્ટ',
        'talk_expert': 'તાત્કાલિક ખેતી સલાહ માટે અમારા AI નિષ્ણાત સાથે વાત કરો'
    },
    'pa': {
        'welcome': "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਕ੍ਰਿਸ਼ੀ AI ਹਾਂ, ਤੁਹਾਡਾ ਖੇਤੀ ਸਹਾਇਕ।",
        'ready': 'ਤੁਹਾਡੀ ਮਦਦ ਲਈ ਤਿਆਰ',
        'listening': 'ਸੁਣ ਰਿਹਾ ਹਾਂ... ਹੁਣ ਬੋਲੋ',
        'thinking': 'ਸੋਚ ਰਿਹਾ ਹਾਂ...',
        'speaking': 'ਬੋਲ ਰਿਹਾ ਹਾਂ...',
        'mic_prompt': 'ਬੋਲਣ ਲਈ ਮਾਈਕ ਤੇ ਕਲਿੱਕ ਕਰੋ',
        'type_prompt': 'ਆਪਣਾ ਸਵਾਲ ਟਾਈਪ ਕਰੋ ਜਾਂ ਮਾਈਕ ਤੇ ਕਲਿੱਕ ਕਰੋ...',
        'quick_questions': 'ਤੁਰੰਤ ਸਵਾਲ',
        'about': 'ਕ੍ਰਿਸ਼ੀ AI ਬਾਰੇ',
        'topics': 'ਮੈਂ ਇਨ੍ਹਾਂ ਵਿੱਚ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ',
        'session_stats': 'ਸੈਸ਼ਨ ਅੰਕੜੇ',
        'questions_asked': 'ਪੁੱਛੇ ਗਏ ਸਵਾਲ',
        'session_time': 'ਸੈਸ਼ਨ ਸਮਾਂ',
        'select_language': 'ਭਾਸ਼ਾ ਚੁਣੋ',
        'voice_agent': 'AI ਵਾਇਸ ਏਜੰਟ',
        'talk_expert': 'ਤੁਰੰਤ ਖੇਤੀ ਸਲਾਹ ਲਈ ਸਾਡੇ AI ਮਾਹਰ ਨਾਲ ਗੱਲ ਕਰੋ'
    }
}

def get_language_prompt(lang_code):
    """Get language-specific system prompt for Gemini"""
    lang_name = SUPPORTED_LANGUAGES.get(lang_code, {}).get('name', 'English')
    native_name = SUPPORTED_LANGUAGES.get(lang_code, {}).get('native', 'English')
    
    return f"""You are Krishi AI (कृषि AI), an expert agricultural assistant for Indian farmers.
    
IMPORTANT: You MUST respond in {lang_name} ({native_name}) language only.

Your expertise includes:
- Crop selection, cultivation, and management for Indian conditions
- Soil health, fertilizers, and organic farming
- Pest and disease management
- Irrigation techniques and water conservation
- Government schemes like PM-KISAN, PMFBY, KCC
- Market prices and MSP information
- Weather-based farming advice
- Season-specific guidance (Kharif, Rabi, Zaid)

Guidelines:
1. ALWAYS respond in {lang_name} ({native_name}) language
2. Give practical, actionable advice suitable for Indian farmers
3. Use simple language that rural farmers can understand
4. Include specific numbers (fertilizer doses, spacing, duration)
5. Mention relevant government schemes when applicable
6. Be encouraging and supportive
7. Keep responses concise but informative (max 200 words)
8. Use emojis to make responses friendly: 🌾 🌱 💧 🐛 🏛️ 📈
9. If asked about non-farming topics, politely redirect to farming

Remember: Your response MUST be in {lang_name} ({native_name}), not English (unless lang_code is 'en')."""

# System prompt for farming AI (default English)
FARMING_SYSTEM_PROMPT = get_language_prompt('en')

# Agricultural Knowledge Base
CROP_INFO = {
    'rice': {
        'seasons': ['Kharif'],
        'duration': '120-150 days',
        'water_need': 'High',
        'soil': 'Clay loam, alluvial',
        'states': ['Punjab', 'West Bengal', 'Uttar Pradesh', 'Andhra Pradesh'],
        'tips': [
            'Maintain 5-7 cm water level during vegetative stage',
            'Apply 120 kg N, 60 kg P, 40 kg K per hectare',
            'Use certified seeds for better yield',
            'Practice System of Rice Intensification (SRI) for higher yields'
        ]
    },
    'wheat': {
        'seasons': ['Rabi'],
        'duration': '110-130 days',
        'water_need': 'Medium',
        'soil': 'Loamy, clay loam',
        'states': ['Punjab', 'Haryana', 'Uttar Pradesh', 'Madhya Pradesh'],
        'tips': [
            'Best sowing time is November 10-25',
            'Apply first irrigation 21 days after sowing',
            'Use HD-2967, HD-3086 varieties for higher yield',
            'Control weeds in first 30-35 days'
        ]
    },
    'cotton': {
        'seasons': ['Kharif'],
        'duration': '150-180 days',
        'water_need': 'Medium',
        'soil': 'Black, alluvial',
        'states': ['Gujarat', 'Maharashtra', 'Telangana', 'Punjab'],
        'tips': [
            'Plant spacing: 90x45 cm for hybrids',
            'Apply 120 kg N, 60 kg P, 60 kg K per hectare',
            'Monitor for bollworm using pheromone traps',
            'Pick cotton when 60% bolls are open'
        ]
    },
    'sugarcane': {
        'seasons': ['Kharif', 'Rabi'],
        'duration': '10-12 months',
        'water_need': 'High',
        'soil': 'Deep loamy',
        'states': ['Uttar Pradesh', 'Maharashtra', 'Karnataka', 'Tamil Nadu'],
        'tips': [
            'Use 3-budded setts for planting',
            'Maintain row spacing of 90-120 cm',
            'Earthing up at 90 and 120 days after planting',
            'Apply 250 kg N, 60 kg P, 60 kg K per hectare'
        ]
    }
}

SOIL_TIPS = {
    'fertility': [
        'Add organic matter through compost or farm yard manure',
        'Practice crop rotation to maintain soil health',
        'Use green manuring with dhaincha or sunhemp',
        'Get soil tested every 2-3 years',
        'Apply lime in acidic soils (pH < 5.5)'
    ],
    'conservation': [
        'Practice contour farming on slopes',
        'Use mulching to prevent erosion',
        'Maintain soil cover with cover crops',
        'Avoid over-tillage to preserve soil structure'
    ]
}

PEST_MANAGEMENT = {
    'organic': [
        'Use neem-based pesticides for soft-bodied insects',
        'Install pheromone traps for pest monitoring',
        'Encourage beneficial insects like ladybugs',
        'Practice intercropping to confuse pests',
        'Use Trichoderma for soil-borne diseases'
    ],
    'integrated': [
        'Monitor pest levels before spraying',
        'Use economic threshold levels for decision',
        'Rotate pesticides to prevent resistance',
        'Spray during morning or evening hours'
    ]
}

GOVT_SCHEMES = [
    {
        'name': 'PM-KISAN',
        'benefit': '₹6,000 per year in 3 installments',
        'eligibility': 'All land-holding farmers'
    },
    {
        'name': 'Pradhan Mantri Fasal Bima Yojana',
        'benefit': 'Crop insurance at low premium',
        'eligibility': 'All farmers growing notified crops'
    },
    {
        'name': 'Kisan Credit Card',
        'benefit': 'Credit at 4% interest rate',
        'eligibility': 'All farmers, sharecroppers, tenant farmers'
    },
    {
        'name': 'Soil Health Card Scheme',
        'benefit': 'Free soil testing and recommendations',
        'eligibility': 'All farmers'
    },
    {
        'name': 'PM Krishi Sinchai Yojana',
        'benefit': 'Subsidy for micro-irrigation (up to 55%)',
        'eligibility': 'All farmers'
    }
]

def call_gemini_ai(user_message, language='en'):
    """Call Google Gemini API for intelligent response in specified language"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        
        # Get language-specific system prompt
        system_prompt = get_language_prompt(language)
        lang_name = SUPPORTED_LANGUAGES.get(language, {}).get('name', 'English')
        
        # Prepare context with knowledge base
        context = """
KNOWLEDGE BASE:
Crops: Rice (Kharif, 120-150 days), Wheat (Rabi, 110-130 days), Cotton (Kharif, 150-180 days), Sugarcane (10-12 months)
Government Schemes: PM-KISAN (Rs.6,000/year), PMFBY (crop insurance), KCC (4% loan), Soil Health Card (free testing)
MSP 2024-25: Paddy Rs.2,300/q, Wheat Rs.2,275/q, Cotton Rs.7,121/q
Seasons: Kharif (June-Oct), Rabi (Nov-Apr), Zaid (Mar-Jun)
"""
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\n{context}\n\nFarmer's Question (respond in {lang_name}): {user_message}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 500
            }
        }
        
        print(f"[GEMINI] Calling API for: {user_message[:50]}... (lang={language})")
        response = http_requests.post(url, json=payload, timeout=30)
        print(f"[GEMINI] Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                ai_text = result['candidates'][0]['content']['parts'][0]['text']
                print(f"[GEMINI] Success! Response length: {len(ai_text)}")
                return ai_text
        else:
            print(f"[GEMINI] Error: {response.text}")
        
        # If API fails, fall back to keyword matching
        return None
        
    except Exception as e:
        print(f"[GEMINI] Exception: {e}")
        return None


def generate_response(message, language='en'):
    """Generate AI response - tries Gemini first, then falls back to keyword matching"""
    
    # Try Gemini AI first
    ai_response = call_gemini_ai(message, language)
    if ai_response:
        return ai_response
    
    # Fallback to keyword-based responses
    message_lower = message.lower()
    
    # Crop-specific queries
    for crop, info in CROP_INFO.items():
        if crop in message_lower:
            tips = random.sample(info['tips'], min(2, len(info['tips'])))
            return f"""Here's information about {crop.title()} farming:

🌱 **Season:** {', '.join(info['seasons'])}
⏱️ **Duration:** {info['duration']}
💧 **Water Need:** {info['water_need']}
🌍 **Best Soil:** {info['soil']}
📍 **Top States:** {', '.join(info['states'][:3])}

💡 **Tips:**
• {tips[0]}
• {tips[1] if len(tips) > 1 else 'Consult local agricultural officer for variety selection'}

Would you like more details about {crop} diseases or fertilizer management?"""

    # Soil queries
    if any(word in message_lower for word in ['soil', 'fertility', 'fertilizer', 'manure', 'compost']):
        tips = random.sample(SOIL_TIPS['fertility'], 3)
        return f"""Here are tips to improve soil fertility:

🧪 **Soil Health Tips:**
• {tips[0]}
• {tips[1]}
• {tips[2]}

📌 **Important:** Get your soil tested to know exact nutrient deficiencies. Contact your nearest Krishi Vigyan Kendra for free soil testing under Soil Health Card scheme.

Would you like information about specific fertilizers or organic amendments?"""

    # Pest/Disease queries
    if any(word in message_lower for word in ['pest', 'disease', 'insect', 'fungus', 'weed', 'spray']):
        organic = random.sample(PEST_MANAGEMENT['organic'], 2)
        ipm = random.sample(PEST_MANAGEMENT['integrated'], 2)
        return f"""Here's guidance on pest and disease management:

🌿 **Organic Methods:**
• {organic[0]}
• {organic[1]}

🔬 **Integrated Pest Management:**
• {ipm[0]}
• {ipm[1]}

⚠️ **Safety First:** Always wear protective gear when spraying. Read pesticide labels carefully.

Which crop are you facing pest issues with?"""

    # Government schemes
    if any(word in message_lower for word in ['scheme', 'subsidy', 'government', 'loan', 'insurance', 'pm-kisan', 'credit']):
        schemes = random.sample(GOVT_SCHEMES, 3)
        response = "Here are some government schemes for farmers:\n\n"
        for scheme in schemes:
            response += f"🏛️ **{scheme['name']}**\n"
            response += f"   Benefit: {scheme['benefit']}\n"
            response += f"   Eligibility: {scheme['eligibility']}\n\n"
        response += "Visit your nearest Common Service Centre or Agriculture Office to apply."
        return response

    # Irrigation queries
    if any(word in message_lower for word in ['irrigation', 'water', 'drip', 'sprinkler']):
        return """Here are irrigation tips:

💧 **Irrigation Methods:**
• **Drip Irrigation:** Best for vegetables, orchards. Saves 40-60% water. Get 55% subsidy under PMKSY.
• **Sprinkler:** Good for wheat, groundnut. Saves 30-40% water.
• **Furrow:** Traditional method for row crops.

⏰ **Best Practices:**
• Irrigate during morning or evening to reduce evaporation
• Monitor soil moisture before irrigating
• Match water application to crop growth stage

Would you like information about drip system installation or subsidy process?"""

    # Weather queries
    if any(word in message_lower for word in ['weather', 'rain', 'monsoon', 'climate', 'forecast']):
        return """For weather-related farming advice:

🌤️ **Weather Tips:**
• Check daily forecasts on IMD website or Meghdoot app
• Plan spraying operations during clear weather
• Prepare drainage channels before monsoon
• Harvest mature crops before predicted rain

📱 **Useful Apps:**
• Meghdoot - Weather forecasts
• Kisan Suvidha - Comprehensive farming info
• eNAM - Market prices

Would you like crop-specific weather guidance?"""

    # Kharif season
    if 'kharif' in message_lower:
        return """🌧️ **Kharif Season Crops (June-October):**

**Cereals:** Rice, Maize, Jowar, Bajra
**Pulses:** Urad, Moong, Arhar
**Oilseeds:** Groundnut, Soybean, Sesame
**Cash Crops:** Cotton, Sugarcane

💡 **Key Tips for Kharif:**
• Complete sowing within 2 weeks of monsoon onset
• Prepare fields with pre-monsoon tillage
• Keep seeds, fertilizers ready before rains
• Plan pest management schedule

Which crop would you like detailed information about?"""

    # Rabi season
    if 'rabi' in message_lower:
        return """❄️ **Rabi Season Crops (November-April):**

**Cereals:** Wheat, Barley, Oats
**Pulses:** Gram, Lentil, Peas
**Oilseeds:** Mustard, Sunflower, Safflower
**Vegetables:** Potato, Onion, Garlic

💡 **Key Tips for Rabi:**
• Sow wheat by November end for best results
• Ensure irrigation at critical growth stages
• Protect crops from frost in December-January
• Apply potash for better grain filling

Which crop would you like detailed information about?"""

    # Market/Price queries
    if any(word in message_lower for word in ['price', 'market', 'sell', 'mandi', 'msp']):
        return """📈 **Market Information:**

**Check Current Prices:**
• Agmarknet website for mandi prices
• eNAM app for online trading
• Kisan Rath app for transportation

**MSP 2024-25 (Key Crops):**
• Paddy: ₹2,300/quintal
• Wheat: ₹2,275/quintal
• Cotton: ₹7,121/quintal (long staple)
• Soybean: ₹4,892/quintal

💡 **Tips:**
• Compare prices across nearby mandis
• Consider online trading through eNAM
• Store properly if waiting for better prices

What crop prices do you want to check?"""

    # Default response
    greetings = ['hello', 'hi', 'namaste', 'good morning', 'good evening']
    if any(greet in message_lower for greet in greetings):
        return """🙏 Namaste! I'm Krishi AI, your agricultural assistant.

I can help you with:
• 🌾 Crop selection and cultivation tips
• 🧪 Soil health and fertilizers
• 🐛 Pest and disease management
• 💧 Irrigation techniques
• 🏛️ Government schemes and subsidies
• 📈 Market prices and trends

What would you like to know about?"""

    # Fallback
    return """I understand you're asking about farming. Let me help you better.

Please ask about specific topics like:
• "How to grow rice in Kharif season?"
• "What are the best crops for Maharashtra?"
• "How to control pests organically?"
• "What government schemes are available?"
• "How to improve soil fertility?"

I'm here to help with any agricultural question! 🌾"""


@voice_agent_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with multi-language support"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        language = data.get('language', 'en')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        # Validate language code
        if language not in SUPPORTED_LANGUAGES:
            language = 'en'
        
        response = generate_response(message, language)
        
        # Get speech code for text-to-speech
        speech_code = SUPPORTED_LANGUAGES.get(language, {}).get('speech_code', 'en-IN')
        
        return jsonify({
            'success': True,
            'response': response,
            'language': language,
            'speech_code': speech_code
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@voice_agent_bp.route('/languages', methods=['GET'])
def get_languages():
    """Get all supported languages"""
    languages = []
    for code, info in SUPPORTED_LANGUAGES.items():
        languages.append({
            'code': code,
            'name': info['name'],
            'native': info['native'],
            'speech_code': info['speech_code']
        })
    return jsonify({
        'success': True,
        'languages': languages
    })


@voice_agent_bp.route('/translations/<lang_code>', methods=['GET'])
def get_translations(lang_code):
    """Get UI translations for a specific language"""
    if lang_code not in UI_TRANSLATIONS:
        lang_code = 'en'
    
    return jsonify({
        'success': True,
        'language': lang_code,
        'translations': UI_TRANSLATIONS.get(lang_code, UI_TRANSLATIONS['en']),
        'speech_code': SUPPORTED_LANGUAGES.get(lang_code, {}).get('speech_code', 'en-IN')
    })


@voice_agent_bp.route('/topics', methods=['GET'])
def get_topics():
    """Get available topics with optional language"""
    lang = request.args.get('lang', 'en')
    
    # Topic translations
    topics_translations = {
        'en': [
            {'id': 'crops', 'name': 'Crop Cultivation', 'icon': '🌾'},
            {'id': 'soil', 'name': 'Soil Health', 'icon': '🧪'},
            {'id': 'pests', 'name': 'Pest Management', 'icon': '🐛'},
            {'id': 'irrigation', 'name': 'Irrigation', 'icon': '💧'},
            {'id': 'schemes', 'name': 'Government Schemes', 'icon': '🏛️'},
            {'id': 'market', 'name': 'Market Prices', 'icon': '📈'},
            {'id': 'weather', 'name': 'Weather Tips', 'icon': '🌤️'}
        ],
        'hi': [
            {'id': 'crops', 'name': 'फसल खेती', 'icon': '🌾'},
            {'id': 'soil', 'name': 'मिट्टी स्वास्थ्य', 'icon': '🧪'},
            {'id': 'pests', 'name': 'कीट प्रबंधन', 'icon': '🐛'},
            {'id': 'irrigation', 'name': 'सिंचाई', 'icon': '💧'},
            {'id': 'schemes', 'name': 'सरकारी योजनाएं', 'icon': '🏛️'},
            {'id': 'market', 'name': 'बाजार भाव', 'icon': '📈'},
            {'id': 'weather', 'name': 'मौसम सुझाव', 'icon': '🌤️'}
        ],
        'mr': [
            {'id': 'crops', 'name': 'पीक लागवड', 'icon': '🌾'},
            {'id': 'soil', 'name': 'माती आरोग्य', 'icon': '🧪'},
            {'id': 'pests', 'name': 'कीड व्यवस्थापन', 'icon': '🐛'},
            {'id': 'irrigation', 'name': 'सिंचन', 'icon': '💧'},
            {'id': 'schemes', 'name': 'सरकारी योजना', 'icon': '🏛️'},
            {'id': 'market', 'name': 'बाजार भाव', 'icon': '📈'},
            {'id': 'weather', 'name': 'हवामान टिप्स', 'icon': '🌤️'}
        ],
        'te': [
            {'id': 'crops', 'name': 'పంట సాగు', 'icon': '🌾'},
            {'id': 'soil', 'name': 'నేల ఆరోగ్యం', 'icon': '🧪'},
            {'id': 'pests', 'name': 'తెగులు నిర్వహణ', 'icon': '🐛'},
            {'id': 'irrigation', 'name': 'నీటిపారుదల', 'icon': '💧'},
            {'id': 'schemes', 'name': 'ప్రభుత్వ పథకాలు', 'icon': '🏛️'},
            {'id': 'market', 'name': 'మార్కెట్ ధరలు', 'icon': '📈'},
            {'id': 'weather', 'name': 'వాతావరణ చిట్కాలు', 'icon': '🌤️'}
        ],
        'ta': [
            {'id': 'crops', 'name': 'பயிர் சாகுபடி', 'icon': '🌾'},
            {'id': 'soil', 'name': 'மண் ஆரோக்கியம்', 'icon': '🧪'},
            {'id': 'pests', 'name': 'பூச்சி மேலாண்மை', 'icon': '🐛'},
            {'id': 'irrigation', 'name': 'பாசனம்', 'icon': '💧'},
            {'id': 'schemes', 'name': 'அரசு திட்டங்கள்', 'icon': '🏛️'},
            {'id': 'market', 'name': 'சந்தை விலைகள்', 'icon': '📈'},
            {'id': 'weather', 'name': 'வானிலை குறிப்புகள்', 'icon': '🌤️'}
        ]
    }
    
    topics = topics_translations.get(lang, topics_translations['en'])
    
    return jsonify({
        'success': True,
        'topics': topics,
        'language': lang
    })


@voice_agent_bp.route('/quick-questions', methods=['GET'])
def get_quick_questions():
    """Get quick question suggestions"""
    return jsonify({
        'success': True,
        'questions': [
            'What crops should I grow in Kharif season?',
            'How to improve soil fertility naturally?',
            'What are common rice diseases?',
            'Best irrigation practices for wheat',
            'How to get PM-KISAN benefits?',
            'Current MSP rates for major crops',
            'Organic pest control methods'
        ]
    })
