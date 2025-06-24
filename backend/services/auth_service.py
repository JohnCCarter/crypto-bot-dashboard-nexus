"""
Security Authentication Service for Trading Bot API
Implements JWT-based authentication with rate limiting for production security.
"""

import jwt
import os
import secrets
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Dict, Any, Optional
from flask import request, jsonify, current_app, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


class AuthService:
    """JWT Authentication service with security best practices."""
    
    def __init__(self):
        """Initialize authentication service with secure defaults."""
        # Setup logger for initialization
        self.logger = logging.getLogger(__name__)
        
        # Use environment variable or generate secure random key
        self.jwt_secret = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(64)
        if not os.getenv("JWT_SECRET_KEY"):
            self.logger.warning(
                "⚠️ SECURITY: JWT_SECRET_KEY not set! Using random key (sessions won't persist across restarts)"
            )
        
        # JWT configuration
        self.jwt_algorithm = "HS256"
        self.token_expiry_hours = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
        
        # Default admin credentials (should be changed in production)
        self.admin_username = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_password = os.getenv("ADMIN_PASSWORD")
        
        if not self.admin_password:
            # Generate secure random password if not set
            self.admin_password = secrets.token_urlsafe(16)
            self.logger.warning(
                f"⚠️ SECURITY: No ADMIN_PASSWORD set! Generated temporary password: {self.admin_password}"
            )
    
    def generate_token(self, username: str, role: str = "user") -> str:
        """
        Generate JWT token for authenticated user.
        
        Args:
            username: User identifier
            role: User role (admin, user, readonly)
            
        Returns:
            JWT token string
        """
        payload = {
            "username": username,
            "role": role,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=self.token_expiry_hours),
            "iss": "crypto-trading-bot",
            "aud": "trading-api"
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm],
                audience="trading-api",
                issuer="crypto-trading-bot"
            )
            return payload
        except jwt.ExpiredSignatureError:
            current_app.logger.warning("🔒 JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            current_app.logger.warning(f"🔒 Invalid JWT token: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user credentials.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            User info if authenticated, None if failed
        """
        # Simple admin authentication (extend for multiple users)
        if username == self.admin_username and password == self.admin_password:
            return {
                "username": username,
                "role": "admin",
                "permissions": ["read", "write", "trade", "admin"]
            }
        
        # Add more user authentication logic here
        return None


# Initialize rate limiter
def init_rate_limiter(app):
    """Initialize Flask-Limiter for rate limiting."""
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"  # Use Redis in production: "redis://localhost:6379"
    )
    return limiter


def require_auth(required_role: str = "user", require_trading: bool = False):
    """
    Decorator to require authentication for API endpoints.
    
    Args:
        required_role: Minimum role required (admin, user, readonly)
        require_trading: Whether endpoint requires trading permissions
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                current_app.logger.warning(
                    f"🔒 Unauthorized access attempt to {request.endpoint} from {get_remote_address()}"
                )
                return jsonify({
                    "error": "Authentication required",
                    "message": "Please provide valid Authorization header"
                }), 401
            
            token = auth_header.split(" ")[1]
            auth_service = current_app._auth_service
            payload = auth_service.verify_token(token)
            
            if not payload:
                return jsonify({
                    "error": "Invalid or expired token",
                    "message": "Please login again"
                }), 401
            
            # Check role permissions
            user_role = payload.get("role", "")
            role_hierarchy = {"readonly": 1, "user": 2, "admin": 3}
            required_level = role_hierarchy.get(required_role, 2)
            user_level = role_hierarchy.get(user_role, 0)
            
            if user_level < required_level:
                current_app.logger.warning(
                    f"🔒 Insufficient permissions: {payload.get('username')} tried to access {request.endpoint}"
                )
                return jsonify({
                    "error": "Insufficient permissions",
                    "message": f"Role '{required_role}' or higher required"
                }), 403
            
            # Check trading permissions for high-risk endpoints
            if require_trading and user_role not in ["admin"]:
                return jsonify({
                    "error": "Trading permissions required",
                    "message": "Only admin users can perform trading operations"
                }), 403
            
            # Store user info in Flask's g object for use in endpoint
            g.current_user = {
                "username": payload.get("username"),
                "role": payload.get("role"),
                "authenticated": True
            }
            
            current_app.logger.info(
                f"✅ Authenticated access: {payload.get('username')} ({user_role}) -> {request.endpoint}"
            )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def public_endpoint(f):
    """
    Decorator to mark endpoint as public (no authentication required).
    Use sparingly and only for safe, read-only endpoints.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Log public access for monitoring
        current_app.logger.info(
            f"📖 Public access to {request.endpoint} from {get_remote_address()}"
        )
        return f(*args, **kwargs)
    return decorated_function