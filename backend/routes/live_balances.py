"""
Live balance API route with authenticated WebSocket integration.
Provides real-time balance updates when available.
"""

import logging
from flask import Blueprint, jsonify
from backend.services.balance_service import fetch_balances
from backend.services.authenticated_websocket_service import (
    authenticated_ws_service
)

live_balances_bp = Blueprint('live_balances', __name__)
logger = logging.getLogger(__name__)

# Store latest WebSocket balance updates
latest_balance_updates = {}


def on_balance_update(balance_data):
    """Callback for authenticated WebSocket balance updates."""
    global latest_balance_updates
    currency = balance_data.get('currency')
    if currency:
        latest_balance_updates[currency] = balance_data
        logger.info(f"💰 [Live Balance] WebSocket update: {currency}")


# Set up WebSocket callback
authenticated_ws_service.set_balance_callback(on_balance_update)


@live_balances_bp.route('/api/live-balances', methods=['GET'])
def get_live_balances_route():
    """
    Get live balances with WebSocket enhancements.
    
    Returns:
        JSON response with live balance data
    """
    try:
        logger.info("💰 [Live Balance] Request received")
        
        # Get base balances from REST API
        balance_data = fetch_balances()
        
        # Transform ccxt format to our format
        base_balances = []
        for currency, data in balance_data['total'].items():
            if float(data) > 0:
                base_balances.append({
                    'currency': currency,
                    'total_balance': float(data),
                    'available': float(balance_data['free'].get(currency, 0))
                })
        
        # Enhance with WebSocket data if available
        enhanced_balances = []
        for balance in base_balances:
            currency = balance.get('currency')
            
            # Check if we have newer WebSocket data
            if currency in latest_balance_updates:
                ws_update = latest_balance_updates[currency]
                
                # Use WebSocket data if newer
                balance.update({
                    'total_balance': ws_update.get('total_balance', balance['total_balance']),
                    'available': ws_update.get('available', balance['available']),
                    'last_update': ws_update.get('timestamp'),
                    'source': 'websocket'
                })
                logger.info(f"💰 [Live Balance] Using WebSocket data for {currency}")
            else:
                balance['source'] = 'rest'
            
            enhanced_balances.append(balance)
        
        logger.info(f"✅ [Live Balance] Returning {len(enhanced_balances)} balances")
        return jsonify(enhanced_balances)
        
    except Exception as e:
        error_msg = f"Failed to fetch live balances: {str(e)}"
        logger.error(f"❌ [Live Balance] {error_msg}")
        return jsonify({"error": error_msg}), 500

@live_balances_bp.route('/api/live-balances/websocket-status', methods=['GET'])
def websocket_status():
    """Get authenticated WebSocket connection status."""
    try:
        status = {
            'connected': authenticated_ws_service.authenticated,
            'user_id': authenticated_ws_service.user_id,
            'available_updates': len(latest_balance_updates),
            'last_updates': list(latest_balance_updates.keys())
        }
        
        return jsonify(status)
        
    except Exception as e:
        error_msg = f"Failed to get WebSocket status: {str(e)}"
        logger.error(f"❌ [Live Balance] {error_msg}")
        return jsonify({"error": error_msg}), 500