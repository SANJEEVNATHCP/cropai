# 🔒 API Key Security Setup

## ⚠️ CRITICAL: Your Gemini API Key Was Leaked!

Google has blocked your old API key. Follow these steps to fix it:

## Step 1: Get a New API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the new API key

## Step 2: Update Your .env File

1. Open the `.env` file in the project root
2. Find this line:
   ```
   GEMINI_API_KEY=YOUR_NEW_API_KEY_HERE
   ```
3. Replace `YOUR_NEW_API_KEY_HERE` with your actual API key
4. Save the file

Example:
```env
GEMINI_API_KEY=AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q
```

## Step 3: Restart the Server

Stop the current server (Ctrl+C) and restart:
```bash
python app.py
```

## Step 4: Test the Voice Agent

1. Open http://localhost:5000/voice-agent
2. Select a language
3. Try asking a farming question
4. You should now get responses instead of 403 errors

## ✅ Security Best Practices

- ✅ API key is now loaded from `.env` file
- ✅ `.env` is in `.gitignore` (won't be committed to Git)
- ✅ Hardcoded API keys have been removed from all files
- ⚠️ **NEVER** commit API keys to Git again!

## 🔐 What Changed?

All hardcoded API keys have been removed from:
- `voice_agent.py`
- `index.py`
- `api/index.py`

Now they all use `os.getenv('GEMINI_API_KEY')` to read from the `.env` file.
