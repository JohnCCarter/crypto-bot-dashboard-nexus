"""
🚀 Enhanced cache service för aggressiv caching och API load reduction.
Designad för att minimera nonce-förbrukande private API calls enligt hybrid-setup.
"""

import time
from typing import Any, Dict, Optional, List
from threading import Lock
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CacheEntry:
    """Enhanced cache entry med metadata för smart cache management."""
    data: Any
    timestamp: float
    ttl_seconds: int
    access_count: int = 0
    last_access: float = 0.0
    cache_type: str = "standard"  # standard, critical, volatile


class EnhancedCacheService:
    """
    🚀 Enhanced thread-safe cache för AGGRESSIV API load reduction.
    
    FÖRBÄTTRINGAR VS. ORIGINAL:
    - Längre TTL för statiska data (balances, positions, account info)
    - Smart cache invalidation och warming
    - Access pattern tracking
    - Cache type categorization (critical vs volatile)
    - Automatic cache cleanup och monitoring
    - Nonce-preserving cache strategies
    
    CACHE STRATEGIER PER TYP:
    - Balances: 60-90s (relativt statisk under trading)
    - Positions: 30-60s (ändras bara vid trades)
    - Account info: 5-10 minuter (mycket statisk)
    - Market data: INGEN cache (använd WebSocket!)
    - Order history: 2-5 minuter (historisk data)
    """
    
    # Predefined TTL strategies för olika data types
    CACHE_STRATEGIES = {
        "balances": {"ttl": 90, "type": "critical"},  # 90s för balances (ökat från 30s)
        "positions": {"ttl": 60, "type": "critical"},  # 60s för positions (ökat från 20s)
        "account_info": {"ttl": 600, "type": "critical"},  # 10 minuter för account info
        "trading_fees": {"ttl": 3600, "type": "critical"},  # 1 timme för fees (mycket statisk)
        "order_history": {"ttl": 180, "type": "standard"},  # 3 minuter för order history
        "open_orders": {"ttl": 15, "type": "volatile"},  # 15s för open orders (kan ändras)
        "symbols": {"ttl": 7200, "type": "critical"},  # 2 timmar för symbols (statisk)
        "status": {"ttl": 30, "type": "standard"},  # 30s för general status
        # VIKTIGT: Marknadsdata CACHEAS EJ - använd WebSocket!
    }
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._total_requests = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minuter mellan cleanup
        
        print("🚀 Enhanced CacheService initialized with aggressive caching strategies")
        print("📊 Configured TTL strategies:", self.CACHE_STRATEGIES)
    
    def get(self, key: str, ttl_seconds: Optional[int] = None) -> Optional[Any]:
        """
        Get cached value med smart TTL och access tracking.
        
        Args:
            key: Cache key
            ttl_seconds: Override TTL (annars används smart strategy)
            
        Returns:
            Cached value if valid, None otherwise
        """
        with self._lock:
            self._total_requests += 1
            
            # Automatic cleanup check
            if time.time() - self._last_cleanup > self._cleanup_interval:
                self._cleanup_expired_entries()
            
            if key in self._cache:
                entry = self._cache[key]
                current_time = time.time()
                
                # Use provided TTL or entry's original TTL
                effective_ttl = ttl_seconds or entry.ttl_seconds
                
                if current_time - entry.timestamp < effective_ttl:
                    # Cache hit! Update access patterns
                    entry.access_count += 1
                    entry.last_access = current_time
                    self._cache_hits += 1
                    
                    cache_age = current_time - entry.timestamp
                    print(f"📊 Cache HIT: {key} (age: {cache_age:.1f}s, "
                          f"ttl: {effective_ttl}s, hits: {entry.access_count})")
                    
                    return entry.data
                else:
                    # Expired - remove and count as miss
                    del self._cache[key]
                    self._cache_misses += 1
                    print(f"⏰ Cache EXPIRED: {key} "
                          f"(age: {current_time - entry.timestamp:.1f}s)")
            else:
                self._cache_misses += 1
                print(f"❌ Cache MISS: {key}")
            
            return None
    
    def set(self, key: str, data: Any, ttl_seconds: Optional[int] = None, 
            cache_type: str = "standard") -> None:
        """
        Store data med smart TTL strategies och kategorisering.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl_seconds: Custom TTL (annars smart detection)
            cache_type: Type of cache entry (critical/standard/volatile)
        """
        with self._lock:
            current_time = time.time()
            
            # Smart TTL detection based on key patterns
            effective_ttl = ttl_seconds or self._determine_smart_ttl(key)
            detected_type = self._determine_cache_type(key)
            final_type = cache_type if cache_type != "standard" else detected_type
            
            # Create enhanced cache entry
            entry = CacheEntry(
                data=data,
                timestamp=current_time,
                ttl_seconds=effective_ttl,
                access_count=0,
                last_access=current_time,
                cache_type=final_type
            )
            
            self._cache[key] = entry
            
            print(f"💾 Cache SET: {key} (ttl: {effective_ttl}s, type: {final_type})")
            
            # Log if this is an important cache save
            if final_type == "critical" and effective_ttl >= 60:
                print(f"🔑 CRITICAL cache saved: {key} - will reduce nonce consumption för {effective_ttl}s")
    
    def _determine_smart_ttl(self, key: str) -> int:
        """Determine optimal TTL based on key patterns och data type."""
        key_lower = key.lower()
        
        # Check för predefined strategies
        for pattern, config in self.CACHE_STRATEGIES.items():
            if pattern in key_lower:
                return config["ttl"]
        
        # Fallback patterns
        if any(pattern in key_lower for pattern in ["balance", "wallet"]):
            return 90  # Aggressiv 90s för balance-relaterad data
        elif any(pattern in key_lower for pattern in ["position", "trade"]):
            return 60  # 60s för position data
        elif any(pattern in key_lower for pattern in ["order", "fill"]):
            return 30  # 30s för order-relaterad data
        elif any(pattern in key_lower for pattern in ["account", "user", "info"]):
            return 300  # 5 minuter för account info
        else:
            return 30  # Conservative fallback
    
    def _determine_cache_type(self, key: str) -> str:
        """Determine cache type based on key patterns."""
        key_lower = key.lower()
        
        # Check för predefined types
        for pattern, config in self.CACHE_STRATEGIES.items():
            if pattern in key_lower:
                return config["type"]
        
        # Pattern-based detection
        if any(pattern in key_lower for pattern in ["balance", "position", "account", "symbol", "fee"]):
            return "critical"  # Data that changes slowly
        elif any(pattern in key_lower for pattern in ["order", "fill", "active"]):
            return "volatile"  # Data that changes frequently
        else:
            return "standard"
    
    def get_smart(self, key: str, data_type: str = None) -> Optional[Any]:
        """
        Smart get med auto-detection av optimal caching strategy.
        
        Args:
            key: Cache key
            data_type: Optional hint om data type för optimal caching
            
        Returns:
            Cached value if valid, None otherwise
        """
        if data_type and data_type in self.CACHE_STRATEGIES:
            config = self.CACHE_STRATEGIES[data_type]
            return self.get(key, ttl_seconds=config["ttl"])
        else:
            return self.get(key)
    
    def set_smart(self, key: str, data: Any, data_type: str = None) -> None:
        """
        Smart set med auto-detection av optimal caching strategy.
        
        Args:
            key: Cache key
            data: Data to cache
            data_type: Hint om data type för optimal caching
        """
        if data_type and data_type in self.CACHE_STRATEGIES:
            config = self.CACHE_STRATEGIES[data_type]
            self.set(key, data, ttl_seconds=config["ttl"], cache_type=config["type"])
        else:
            self.set(key, data)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching pattern.
        
        Args:
            pattern: Pattern to match in keys
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            
            for key in keys_to_remove:
                del self._cache[key]
            
            if keys_to_remove:
                print(f"🗑️ Invalidated {len(keys_to_remove)} cache entries matching '{pattern}'")
            
            return len(keys_to_remove)
    
    def warm_cache(self, warming_data: Dict[str, Any]) -> None:
        """
        Warm cache med initial data för att förhindra initial API calls.
        
        Args:
            warming_data: Dict med key-value pairs för cache warming
        """
        for key, data in warming_data.items():
            self.set_smart(key, data)
        
        print(f"🔥 Cache warmed with {len(warming_data)} entries")
    
    def _cleanup_expired_entries(self) -> None:
        """Clean up expired cache entries för memory efficiency."""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if current_time - entry.timestamp >= entry.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        self._last_cleanup = current_time
        
        if expired_keys:
            print(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
    
    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()
            print(f"🗑️ Cleared all {cleared_count} cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics för monitoring."""
        with self._lock:
            current_time = time.time()
            
            # Categorize entries by type
            type_stats = {}
            access_stats = []
            total_size = 0
            
            for key, entry in self._cache.items():
                # Type statistics
                cache_type = entry.cache_type
                if cache_type not in type_stats:
                    type_stats[cache_type] = {"count": 0, "total_accesses": 0}
                
                type_stats[cache_type]["count"] += 1
                type_stats[cache_type]["total_accesses"] += entry.access_count
                
                # Access statistics
                age = current_time - entry.timestamp
                remaining_ttl = max(0, entry.ttl_seconds - age)
                
                access_stats.append({
                    "key": key,
                    "age_seconds": round(age, 1),
                    "remaining_ttl": round(remaining_ttl, 1),
                    "access_count": entry.access_count,
                    "cache_type": entry.cache_type
                })
                
                total_size += 1
            
            # Calculate hit rate
            hit_rate = (self._cache_hits / max(1, self._total_requests)) * 100
            
            return {
                "total_entries": total_size,
                "cache_hit_rate": round(hit_rate, 2),
                "total_requests": self._total_requests,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "type_distribution": type_stats,
                "configured_strategies": self.CACHE_STRATEGIES,
                "most_accessed": sorted(access_stats, key=lambda x: x["access_count"], reverse=True)[:10],
                "cleanup_info": {
                    "last_cleanup": datetime.fromtimestamp(self._last_cleanup).isoformat(),
                    "cleanup_interval_seconds": self._cleanup_interval
                }
            }
    
    def get_nonce_savings_estimate(self) -> Dict[str, Any]:
        """
        Estimate nonce savings från cache usage.
        
        Returns:
            Dict med estimated nonce savings och API call reduction
        """
        with self._lock:
            # Count critical data cache hits (these save nonces)
            critical_hits = sum(
                entry.access_count for entry in self._cache.values() 
                if entry.cache_type == "critical"
            )
            
            # Estimate based on cache hit rate för critical operations
            total_critical_requests = self._cache_hits  # Simplified estimate
            estimated_api_calls_saved = critical_hits
            
            return {
                "estimated_nonce_calls_saved": critical_hits,
                "critical_cache_hits": critical_hits,
                "estimated_api_load_reduction_percent": min(90, (critical_hits / max(1, total_critical_requests)) * 100),
                "cache_efficiency": {
                    "balances_cache_active": any("balance" in key for key in self._cache.keys()),
                    "positions_cache_active": any("position" in key for key in self._cache.keys()),
                    "account_info_cache_active": any("account" in key for key in self._cache.keys())
                }
            }


# Backwards compatibility
CacheService = EnhancedCacheService

# Global cache instance
_cache_service = None


def get_cache_service() -> EnhancedCacheService:
    """Get enhanced global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = EnhancedCacheService()
    return _cache_service 