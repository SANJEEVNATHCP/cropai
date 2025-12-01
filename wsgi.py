"""WSGI entry point for production deployment"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.app import app, db

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
