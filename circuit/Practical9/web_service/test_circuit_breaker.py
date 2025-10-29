import pytest
import time
from circuit_breaker import db_circuit_breaker
import requests


def test_circuit_breaker_opens_after_failures():
    for i in range(3):
        try:
            db_circuit_breaker.call(lambda: requests.get(
                "http://invalid-url", timeout=1))
        except:
            pass

    assert db_circuit_breaker.current_state == "open"


def test_circuit_breaker_half_open_after_timeout():
    time.sleep(31)
    assert db_circuit_breaker.current_state == "half_open"


def test_circuit_breaker_closes_on_success():
    db_circuit_breaker.call(lambda: "success")
    assert db_circuit_breaker.current_state == "closed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
