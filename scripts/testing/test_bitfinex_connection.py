#!/usr/bin/env python3
"""Test script för att verifiera Bitfinex API-anslutning."""

import os
import platform
import socket
import sys

from dotenv import load_dotenv


# Detektera om vi kör på jobbdator eller hemdator
def is_work_computer():
    """Detekterar om skriptet körs på jobbdatorn baserat på datornamn."""
    hostname = socket.gethostname().lower()
    # Ändra dessa villkor baserat på ditt datornamn på jobbet
    return "work" in hostname or "job" in hostname


def is_home_computer():
    """Detekterar om skriptet körs på hemdatorn baserat på datornamn."""
    hostname = socket.gethostname().lower()
    # Ändra dessa villkor baserat på ditt datornamn hemma
    return "skynet" in hostname or "home" in hostname


# Anpassa sökvägar baserat på miljö
def setup_environment():
    """Konfigurerar miljön baserat på om det är jobbdator eller hemdator."""
    print(f"🖥️ Datornamn: {socket.gethostname()}")
    print(f"💻 Operativsystem: {platform.system()}")
    
    if is_work_computer():
        print("🏢 Detekterad miljö: JOBBDATOR")
        # Specifika inställningar för jobbdator
    elif is_home_computer():
        print("🏠 Detekterad miljö: HEMDATOR")
        # Specifika inställningar för hemdator
    else:
        print("❓ Detekterad miljö: OKÄND")
        
    # Ladda environment variables från .env
    load_dotenv()


def test_bitfinex_connection():
    """Testa Bitfinex API-anslutning utan att exponera känslig data."""

    print("🧪 TESTAR BITFINEX API-ANSLUTNING...")
    print("=" * 50)

    # Konfigurera miljön
    setup_environment()

    # Kontrollera environment variables
    exchange_id = os.getenv("EXCHANGE_ID")
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")

    print(f"✅ Exchange ID: {exchange_id}")
    print(f"✅ API Key konfigurerad: {'Ja' if api_key else 'Nej'}")
    print(f"✅ API Secret konfigurerad: {'Ja' if api_secret else 'Nej'}")

    if not api_key or not api_secret:
        print("\n❌ API nycklar saknas i .env filen!")
        print("Konfigurera BITFINEX_API_KEY och BITFINEX_API_SECRET")
        return False

    # Testa ccxt anslutning
    try:
        import ccxt

        print(f"✅ CCXT version: {ccxt.__version__}")

        # Skapa Bitfinex instans
        exchange = ccxt.bitfinex(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
            }
        )

        print("✅ Bitfinex exchange instans skapad")

        # Testa basic anslutning (inte authenticated)
        ticker = exchange.fetch_ticker("BTC/USD")
        print(f"✅ Market data test: BTC/USD = ${ticker['last']:.2f}")

        # Testa authenticated anslutning
        try:
            balance = exchange.fetch_balance()
            print("✅ Authenticated API call lyckades!")

            # Visa tillgängliga currencies (utan att visa exakta belopp)
            currencies = [
                curr
                for curr, info in balance.items()
                if isinstance(info, dict) and info.get("total", 0) > 0
            ]
            if currencies:
                print(f"✅ Aktiva currencies: {', '.join(currencies[:5])}")
            else:
                print("✅ Inga aktiva balances (nytt konto?)")

        except Exception as e:
            print(f"❌ Authenticated API call misslyckades: {str(e)}")
            if "Invalid API key" in str(e):
                print("💡 Kontrollera att API nyckeln är korrekt")
            elif "permissions" in str(e).lower():
                print("💡 Kontrollera API key permissions på Bitfinex")
            return False

    except ImportError:
        print("❌ ccxt inte installerat")
        return False
    except Exception as e:
        print(f"❌ Anslutningsfel: {str(e)}")
        return False

    print("\n🎉 BITFINEX ANSLUTNING LYCKAD!")
    print("Du kan nu använda dashboard med riktig data från Bitfinex")
    return True


if __name__ == "__main__":
    success = test_bitfinex_connection()
    sys.exit(0 if success else 1)
