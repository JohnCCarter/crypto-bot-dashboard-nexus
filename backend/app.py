import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from backend.routes import register_all_routes

# Ladda miljövariabler från .env fil
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)
CORS(app)

# Använd den nya centraliserade route-registreringen
register_all_routes(app)

if __name__ == "__main__":
    # Hämta port från miljövariabel eller använd standard
    port = int(os.getenv("CONTAINER_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    print(f"🚀 Starting Flask server on port {port} (debug={debug})")
    print(f"📍 Environment: {os.getenv('FLASK_ENV', 'development')}")
    app.run(debug=debug, port=port, host="0.0.0.0")
