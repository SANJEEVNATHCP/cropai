# CropYield AI - Agricultural Prediction & Recommendation System

🌾 An intelligent agricultural assistant that helps farmers predict crop yields and get personalized crop recommendations with LiveKit-powered expert consultations.

## 🌟 Features

### 1. Crop Yield Prediction
- Predict yields for 20+ crops
- Considers soil quality (NPK, pH)
- Accounts for weather conditions
- Regional adjustments

### 2. Crop Recommendation
- AI-powered crop suggestions
- Based on soil, climate, and budget
- Seasonal recommendations (Kharif, Rabi, Zaid)
- State-specific suggestions

### 3. Expert Consultation (LiveKit)
- Real-time video calls with agricultural experts
- Voice chat support
- Get personalized advice
- Book consultations

### 4. User Profile
- Track farming history
- Save predictions and recommendations
- Manage farm details

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd cropyield-ai
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run the application**
```bash
python wsgi.py
```

6. **Open in browser**
```
http://localhost:5000
```

## 📁 Project Structure

```
cropyield-ai/
├── backend/
│   ├── __init__.py
│   ├── app.py                 # Main Flask application
│   ├── models/
│   │   └── __init__.py        # Database models
│   └── routes/
│       ├── __init__.py
│       ├── yield_prediction.py    # Yield prediction API
│       ├── crop_recommendation.py # Crop recommendation API
│       ├── livekit_routes.py      # LiveKit video calls
│       └── auth.py               # Authentication
├── frontend/
│   ├── templates/
│   │   └── index.html         # Main UI
│   └── static/
│       ├── css/
│       │   └── style.css      # Styling
│       └── js/
│           └── app.js         # Frontend logic
├── requirements.txt           # Python dependencies
├── wsgi.py                   # Production entry point
├── Procfile                  # Railway deployment
├── railway.json              # Railway config
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🌐 Deployment

### Backend (Railway)

1. Push code to GitHub
2. Connect Railway to your repo
3. Add environment variables:
   - `SECRET_KEY`
   - `LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET`
   - `LIVEKIT_URL`
4. Deploy!

### Frontend (Netlify)

1. Build frontend for static hosting
2. Update API URL in `app.js`
3. Deploy `frontend/` folder to Netlify

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login
- `GET /api/auth/profile` - Get profile

### Yield Prediction
- `POST /api/yield/predict` - Predict yield
- `GET /api/yield/crops` - List crops
- `GET /api/yield/history` - Prediction history

### Crop Recommendation
- `POST /api/recommendation/recommend` - Get recommendations
- `GET /api/recommendation/seasons` - Season info
- `GET /api/recommendation/states` - Supported states

### LiveKit
- `POST /api/livekit/token` - Get video token
- `POST /api/livekit/create-room` - Create room
- `GET /api/livekit/experts` - List experts

## 📊 Supported Crops

Rice, Wheat, Maize, Sugarcane, Cotton, Soybean, Groundnut, Mustard, Potato, Tomato, Onion, Chilli, Turmeric, Banana, Mango, Coconut, Tea, Coffee, Jute, Pulses, Millets

## 🇮🇳 Supported States

Maharashtra, Punjab, Uttar Pradesh, Madhya Pradesh, Rajasthan, Gujarat, Karnataka, Tamil Nadu, Andhra Pradesh, West Bengal, Bihar, Haryana, Kerala, Odisha, Telangana

## 🛠️ Tech Stack

- **Backend**: Flask, SQLAlchemy, JWT
- **Frontend**: HTML5, CSS3, JavaScript
- **Video Calls**: LiveKit
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Deployment**: Railway + Netlify

## 📄 License

MIT License - Feel free to use and modify!

## 🤝 Contributing

1. Fork the repo
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open PR

---

Made with ❤️ for Indian Farmers
