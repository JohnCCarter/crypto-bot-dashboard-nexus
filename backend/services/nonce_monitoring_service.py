"""
📊🔐 Enhanced Nonce Monitoring & Logging Service
"""

import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class NonceMonitoringStats:
    """Basic nonce monitoring statistics"""

    total_nonces_issued: int = 0
    race_conditions_detected: int = 0
    uptime_seconds: float = 0.0


class EnhancedNonceMonitoringService:
    """Enhanced monitoring service för nonce usage"""

    def __init__(self):
        self.stats = NonceMonitoringStats()
        self.startup_time = time.time()
        print("📊 Enhanced Nonce Monitoring Service initialized")

    def log_nonce_usage(self, nonce: int, service_name: str):
        """Log nonce usage event"""
        self.stats.total_nonces_issued += 1
        logger.info(f"🔢 Nonce {nonce} → {service_name}")

    def get_monitoring_report(self) -> Dict[str, Any]:
        """Get monitoring report"""
        uptime_hours = (time.time() - self.startup_time) / 3600

        return {
            "monitoring_status": {"uptime_hours": round(uptime_hours, 2)},
            "nonce_usage_stats": {
                "total_nonces_issued": self.stats.total_nonces_issued
            },
        }


_monitoring_service: Optional[EnhancedNonceMonitoringService] = None


def get_nonce_monitoring_service() -> EnhancedNonceMonitoringService:
    """Get the global nonce monitoring service instance."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = EnhancedNonceMonitoringService()
    return _monitoring_service
