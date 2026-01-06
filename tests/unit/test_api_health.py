import json


class TestHealthAPI:

    def test_health_check(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'uptime_seconds' in data

    def test_readiness_check(self, client):
        response = client.get('/api/readiness')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ready'
