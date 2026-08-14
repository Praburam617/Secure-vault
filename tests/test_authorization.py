import io
import pytest
from app.models import User, FileModel

def test_mandatory_two_user_security_isolation(client, app):
    """
    MANDATORY TWO-USER SECURITY TEST
    User A creates a protected file.
    User B attempts: view, download, decrypt, delete, rename, share, purge.
    EVERY unauthorized operation MUST fail safely with 404 or 403.
    """
    # 1. Register User A
    client.post('/auth/register', data={
        'username': 'usera',
        'email': 'usera@example.com',
        'password': 'PasswordUserA123!',
        'confirm_password': 'PasswordUserA123!'
    })
    # Login User A
    client.post('/auth/login', data={'identifier': 'usera', 'password': 'PasswordUserA123!'})

    # User A uploads & encrypts a file
    file_data = (io.BytesIO(b"Confidential Data for User A Only"), "user_a_secret.txt")
    encrypt_res = client.post('/encrypt', data={
        'file': file_data,
        'password': 'FileProtectionPasswordA!',
        'confirm_password': 'FileProtectionPasswordA!',
        'retention_days': '0'
    }, content_type='multipart/form-data', follow_redirects=True)
    assert encrypt_res.status_code == 200

    # Retrieve created file ID
    with app.app_context():
        user_a = User.query.filter_by(username='usera').first()
        file_a = FileModel.query.filter_by(user_id=user_a.id).first()
        assert file_a is not None
        file_a_id = file_a.id

    # Logout User A
    client.get('/auth/logout')

    # 2. Register & Login User B
    client.post('/auth/register', data={
        'username': 'userb',
        'email': 'userb@example.com',
        'password': 'PasswordUserB123!',
        'confirm_password': 'PasswordUserB123!'
    })
    client.post('/auth/login', data={'identifier': 'userb', 'password': 'PasswordUserB123!'})

    # 3. User B attempts unauthorized access to User A's file
    # Decrypt attempt
    res_decrypt = client.post(f'/vault/decrypt/{file_a_id}', data={'password': 'FileProtectionPasswordA!'})
    assert res_decrypt.status_code == 404

    # Download encrypted payload attempt
    res_download = client.get(f'/vault/download/{file_a_id}')
    assert res_download.status_code == 404

    # Delete attempt
    res_delete = client.post(f'/vault/delete/{file_a_id}')
    assert res_delete.status_code == 404

    # Rename attempt
    res_rename = client.post(f'/vault/rename/{file_a_id}', data={'new_filename': 'hacked.txt'})
    assert res_rename.status_code == 404

    # Share attempt
    res_share = client.post(f'/vault/share/{file_a_id}', data={'share_password': '123'})
    assert res_share.status_code == 404

    # Purge attempt
    res_purge = client.post(f'/vault/purge/{file_a_id}')
    assert res_purge.status_code == 404
