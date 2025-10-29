import pybreaker
import logging
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=30,
    exclude=[ValueError],
    name="db_service_breaker"
)


def handle_db_failure(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return db_circuit_breaker.call(func, *args, **kwargs)
        except pybreaker.CircuitBreakerError:
            logger.error(f"Circuit breaker OPEN for {func.__name__}")
            return {
                "status": "degraded",
                "message": "Database service temporarily unavailable",
                "cached": True
            }
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return {
                "status": "error",
                "message": "Service error occurred"
            }
    return wrapper
