import os
import logging

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from backend.routes import register_all_routes
from backend.services.exchange import ExchangeService

# Ladda miljövariabler från .env fil
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)
CORS(app)

# DRASTISK logging-reducering: Endast WARNING och ERROR
# Tysta ALL INFO-level spam från alla routes och services
logging.getLogger().setLevel(logging.WARNING)  # Root logger
logging.getLogger('backend').setLevel(logging.WARNING)  # Alla backend modules
logging.getLogger('werkzeug').setLevel(logging.ERROR)  # Flask server logs
logging.getLogger('app').setLevel(logging.WARNING)  # App-specific logs

# Event_logger ska också bara logga WARNING+ (inte INFO)
logging.getLogger('event_logger').setLevel(logging.WARNING)


# Initialize shared exchange service with API keys from .env
def init_services(app):
    """Initialize shared services that routes can use."""
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")
    exchange_id = os.getenv("EXCHANGE_ID", "bitfinex")

    print("🔑 Initializing exchange service...")
    print(f"📊 Exchange: {exchange_id}")
    print(f"🔐 API Key: {'***' + api_key[-4:] if api_key else 'MISSING'}")
    print(f"🔒 Secret: {'***' + api_secret[-4:] if api_secret else 'MISSING'}")

    if not api_key or not api_secret:
        print(
            "⚠️ WARNING: Exchange service will run in DEMO mode "
            "(no real API keys)"
        )
        app._services = {"exchange": None}
    else:
        try:
            exchange_service = ExchangeService(exchange_id, api_key, api_secret)
            app._services = {"exchange": exchange_service}
            print("✅ Exchange service initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize exchange service: {e}")
            app._services = {"exchange": None}


# Initialize services before registering routes
init_services(app)

# Använd den nya centraliserade route-registreringen
register_all_routes(app)

if __name__ == "__main__":
    # Hämta port från miljövariabel eller använd standard
    port = int(os.getenv("CONTAINER_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    print(f"🚀 Starting Flask server on port {port} (debug={debug})")
    print(f"📍 Environment: {os.getenv('FLASK_ENV', 'development')}")
    app.run(debug=debug, port=port, host="0.0.0.0")
