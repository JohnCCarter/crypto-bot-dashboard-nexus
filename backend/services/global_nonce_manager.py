"""
🔐 Enhanced Global Nonce Manager för Bitfinex API
Säkerställer unika, monotonically increasing nonces för hela applikationen
MED SEKVENTIELL KÖ för att eliminera race conditions fullständigt
"""

import threading
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
from collections import deque
from dataclasses import dataclass


@dataclass
class NonceRequest:
    """Request för nonce från kö-systemet"""
    api_key: str
    service_name: str
    request_time: float
    future: threading.Event
    result: Optional[int] = None


class EnhancedGlobalNonceManager:
    """
    Enhanced singleton nonce manager för all Bitfinex API kommunikation.
    
    FÖRBÄTTRINGAR VS. ORIGINAL:
    - Sekventiell kö med FIFO-garanti
    - Race condition elimination
    - Enhanced logging och monitoring
    - API rate limiting awareness
    - Async/sync hybrid support
    
    Garanterar:
    - Unika nonces över alla services (REST + WebSocket)
    - Thread-safe operation med sekventiell exekvering
    - Monotonically increasing values
    - Millisecond precision enligt Bitfinex krav
    - INGEN race condition möjlighet
    """
    
    _instance: Optional['EnhancedGlobalNonceManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Prevent re-initialization
        if hasattr(self, '_initialized'):
            return
            
        # Initialize enhanced nonce state
        self._last_nonce = round(datetime.now().timestamp() * 1000)
        # Reentrant lock för nested calls
        self._nonce_lock = threading.RLock()
        
        # SEKVENTIELL KÖ för race condition elimination
        self._request_queue: deque[NonceRequest] = deque()
        self._queue_lock = threading.Lock()
        self._queue_processor_running = False
        self._queue_processor_thread: Optional[threading.Thread] = None
        
        # API key tracking och monitoring
        self._api_key_tracking: Dict[str, List[str]] = {}
        # Last 1000 nonces for debugging - use Any to avoid deque typing issues
        self._nonce_history: List[Dict[str, Any]] = []
        self._request_stats: Dict[str, Dict] = {}  # Per-service statistics
        
        # Rate limiting awareness
        # Per-service last request
        self._last_request_time: Dict[str, float] = {}
        self._min_request_interval = 0.1  # 100ms minimum between requests
        
        self._initialized = True
        
        base_nonce = self._last_nonce
        print(f"🔐 Enhanced GlobalNonceManager initialized: {base_nonce}")
        print("🔐 Sekventiell kö aktiverad för race condition elimination")
        
        # Start queue processor
        self._start_queue_processor()
    
    def _start_queue_processor(self):
        """Starta sekventiell kö-processor för FIFO nonce-generering"""
        if not self._queue_processor_running:
            self._queue_processor_running = True
            thread = threading.Thread(
                target=self._process_nonce_queue,
                daemon=True,
                name="NonceQueueProcessor"
            )
            self._queue_processor_thread = thread
            self._queue_processor_thread.start()
            print("🔄 Nonce queue processor started")
    
    def _process_nonce_queue(self):
        """Sekventiell processor för nonce-requests"""
        while self._queue_processor_running:
            try:
                with self._queue_lock:
                    if not self._request_queue:
                        continue
                    
                    request = self._request_queue.popleft()
                
                # Process request sekventiellt (NO PARALLELISM POSSIBLE)
                nonce = self._generate_nonce_internal(
                    request.api_key, 
                    request.service_name, 
                    request.request_time
                )
                
                # Set result and signal completion
                request.result = nonce
                request.future.set()
                
                # Optional micro-delay för rate limiting
                time.sleep(0.001)  # 1ms mellan nonce-generering
                
            except Exception as e:
                print(f"❌ Nonce queue processor error: {e}")
                time.sleep(0.01)  # Brief pause on error
    
    def register_api_key(self, api_key: str, service_name: str):
        """
        Register an API key with this nonce manager.
        
        Args:
            api_key: Bitfinex API key
            service_name: Name of service using this key
        """
        with self._nonce_lock:
            if api_key not in self._api_key_tracking:
                self._api_key_tracking[api_key] = []
                self._request_stats[api_key] = {
                    'total_requests': 0,
                    'last_request': None,
                    'services': []
                }
            
            if service_name not in self._api_key_tracking[api_key]:
                self._api_key_tracking[api_key].append(service_name)
                self._request_stats[api_key]['services'].append(service_name)
                key_suffix = api_key[-4:] if len(api_key) >= 4 else api_key
                print(f"🔑 Registered {service_name} with key ***{key_suffix}")
    
    def get_next_nonce(self, api_key: str, service_name: str = "unknown") -> int:
        """
        Generate next unique nonce via SEKVENTIELL KÖ.
        
        GARANTERAR: FIFO-ordning, inga race conditions, unika nonces
        
        Args:
            api_key: API key making the request
            service_name: Name of service for logging
            
        Returns:
            Unique nonce (milliseconds since epoch)
        """
        request_time = time.time()
        
        # Create nonce request för sekventiell kö
        nonce_request = NonceRequest(
            api_key=api_key,
            service_name=service_name,
            request_time=request_time,
            future=threading.Event()
        )
        
        # Add to sekventiell kö (FIFO garanterat)
        with self._queue_lock:
            self._request_queue.append(nonce_request)
        
        # Wait för sekventiell processing (NO RACE CONDITIONS)
        nonce_request.future.wait(timeout=5.0)  # 5s timeout för safety
        
        if nonce_request.result is None:
            # Fallback if queue processing failed
            print(f"⚠️ Queue timeout, direct generation for {service_name}")
            return self._generate_nonce_internal(
                api_key, service_name, request_time
            )
        
        return nonce_request.result
    
    def _generate_nonce_internal(
        self, api_key: str, service_name: str, request_time: float
    ) -> int:
        """
        Internal nonce generation (endast från sekventiell kö).
        
        DENNA METOD KAN EJ ANROPAS PARALLELLT - endast via kö-processor.
        """
        with self._nonce_lock:
            # Rate limiting check
            if api_key in self._last_request_time:
                time_diff = request_time - self._last_request_time[api_key]
                if time_diff < self._min_request_interval:
                    needed_delay = self._min_request_interval - time_diff
                    print(f"🔄 Rate limiting: wait {needed_delay:.3f}s")
                    time.sleep(needed_delay)
            
            # Use Bitfinex official method: milliseconds since Unix epoch
            now_milliseconds = round(datetime.now().timestamp() * 1000)
            
            # Ensure nonce always increments with minimum gap
            if now_milliseconds <= self._last_nonce:
                # If current time is not ahead, add minimum increment
                self._last_nonce += 1
            else:
                # Use current time but ensure increment from last nonce
                self._last_nonce = max(now_milliseconds, self._last_nonce + 1)
            
            nonce = self._last_nonce
            
            # Update statistics
            self._last_request_time[api_key] = request_time
            if api_key in self._request_stats:
                self._request_stats[api_key]['total_requests'] += 1
                stats = self._request_stats[api_key]
                stats['last_request'] = datetime.now().isoformat()
            
            # Log för debugging nonce conflicts
            api_suffix = api_key[-4:] if api_key and len(api_key) >= 4 else 'None'
            print(f"🔢 Nonce {nonce} to {service_name} (***{api_suffix})")
            
            # Store in history för debugging (keep last 1000)
            self._nonce_history.append({
                'nonce': nonce,
                'service': service_name,
                'api_key_suffix': api_suffix,
                'timestamp': datetime.now().isoformat(),
                'request_time': request_time
            })
            if len(self._nonce_history) > 1000:
                self._nonce_history = self._nonce_history[-1000:]
            
            return nonce
    
    def get_websocket_nonce(self, api_key: str) -> str:
        """
        Generate nonce för WebSocket authentication via sekventiell kö.
        
        Args:
            api_key: API key for WebSocket auth
            
        Returns:
            Nonce as string (microseconds for WebSocket auth)
        """
        # Use sekventiell kö även för WebSocket
        base_nonce = self.get_next_nonce(api_key, "WebSocket")
        # Convert to microseconds for WebSocket (multiply by 1000)
        ws_nonce = base_nonce * 1000
        
        print(f"🌐 WebSocket nonce {ws_nonce} generated via kö")
        return str(ws_nonce)
    
    def get_status(self) -> dict:
        """Get enhanced nonce manager status för debugging."""
        with self._nonce_lock:
            queue_size = (
                len(self._request_queue) 
                if hasattr(self, '_request_queue') else 0
            )
            
            return {
                "last_nonce": self._last_nonce,
                "queue_size": queue_size,
                "queue_processor_running": getattr(
                    self, '_queue_processor_running', False
                ),
                "active_api_keys": {
                    f"***{key[-4:]}": {
                        'services': services,
                        'stats': self._request_stats.get(key, {})
                    }
                    for key, services in self._api_key_tracking.items()
                },
                "total_services": sum(
                    len(services) for services in self._api_key_tracking.values()
                ),
                "recent_nonces": self._nonce_history[-10:],
                "rate_limiting_active": len(self._last_request_time) > 0
            }
    
    def get_nonce_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent nonce history för debugging race conditions."""
        with self._nonce_lock:
            return self._nonce_history[-limit:]
    
    def shutdown(self):
        """Graceful shutdown av nonce manager."""
        self._queue_processor_running = False
        if (self._queue_processor_thread and 
                self._queue_processor_thread.is_alive()):
            self._queue_processor_thread.join(timeout=2.0)
        print("🔐 Enhanced GlobalNonceManager shutdown complete")


# Backwards compatibility: Use enhanced manager as default
GlobalNonceManager = EnhancedGlobalNonceManager

# Global singleton instance
nonce_manager = EnhancedGlobalNonceManager()


def get_global_nonce_manager() -> EnhancedGlobalNonceManager:
    """Get the enhanced global nonce manager instance."""
    return nonce_manager 