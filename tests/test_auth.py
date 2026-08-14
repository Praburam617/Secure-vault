import pytest
from app.models import User, UserSettings
from app.services.security_service import SecurityService

def test_user_registration(client, app):
    response = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Registration successful' in response.data

    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@example.com'
        assert user.check_password('SecurePassword123!')
        assert user.settings is not None

def test_login_and_logout(client, app):
    # Register user first
    client.post('/auth/register', data={
        'username': 'authuser',
        'email': 'auth@example.com',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!'
    })

    # Successful login
    res_login = client.post('/auth/login', data={
        'identifier': 'authuser',
        'password': 'SecurePassword123!'
    }, follow_redirects=True)
    assert res_login.status_code == 200
    assert b'Welcome back, authuser!' in res_login.data

    # Logout
    res_logout = client.get('/auth/logout', follow_redirects=True)
    assert res_logout.status_code == 200
    assert b'You have been logged out securely' in res_logout.data

def test_wrong_password_lockout(client, app):
    client.post('/auth/register', data={
        'username': 'lockuser',
        'email': 'lock@example.com',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!'
    })

    # Fail login 5 times
    for _ in range(5):
        client.post('/auth/login', data={
            'identifier': 'lockuser',
            'password': 'WrongPassword123!'
        })

    # 6th attempt should inform locked out
    res_lock = client.post('/auth/login', data={
        'identifier': 'lockuser',
        'password': 'SecurePassword123!'
    }, follow_redirects=True)
    assert b'locked' in res_lock.data.lower()
