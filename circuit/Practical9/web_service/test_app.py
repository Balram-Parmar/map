import pytest
from app import app, prediction_cache


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 200


def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'circuit_breaker' in data


def test_metrics_endpoint(client):
    response = client.get('/metrics')
    assert response.status_code == 200
    data = response.get_json()
    assert 'circuit_breaker_state' in data
    assert 'cache_size' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
