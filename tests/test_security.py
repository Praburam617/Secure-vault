import pytest

def test_security_headers(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-Frame-Options') == 'DENY'
    assert 'Content-Security-Policy' in response.headers

def test_error_pages(client):
    res_404 = client.get('/nonexistent-page-url-12345')
    assert res_404.status_code == 404
    assert b'404' in res_404.data
