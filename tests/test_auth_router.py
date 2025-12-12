import pytest

def test_login_success(client):
    response = client.post(
        "/api/auth/token",
        data={
            "username": "johndoe",
            "password": "rahasia"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0

def test_login_wrong_password(client):
    response = client.post(
        "/api/auth/token",
        data={
            "username": "johndoe",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_nonexistent_user(client):
    response = client.post(
        "/api/auth/token",
        data={
            "username": "nonexistent",
            "password": "password"
        }
    )
    
    assert response.status_code == 401

def test_login_empty_credentials(client):
    response = client.post(
        "/api/auth/token",
        data={
            "username": "",
            "password": ""
        }
    )
    
    # OAuth2PasswordRequestForm validation fails (422)
    assert response.status_code == 422

def test_login_alice_user(client):
    response = client.post(
        "/api/auth/token",
        data={
            "username": "alice",
            "password": "rahasia2"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_login_missing_username(client):
    response = client.post(
        "/api/auth/token",
        data={
            "password": "somepassword"
        }
    )
    
    assert response.status_code == 422  # Validation error

def test_login_missing_password(client):
    response = client.post(
        "/api/auth/token",
        data={
            "username": "johndoe"
        }
    )
    
    assert response.status_code == 422  # Validation error

def test_login_invalid_content_type(client):
    response = client.post(
        "/api/auth/token",
        json={  
            "username": "johndoe",
            "password": "rahasia"
        }
    )
    
    assert response.status_code == 422

def test_login_token_can_be_used(client):
    # Login to get token
    login_response = client.post(
        "/api/auth/token",
        data={
            "username": "johndoe",
            "password": "rahasia"
        }
    )
    
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Use token to access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/perencanaan/00000000-0000-0000-0000-000000000000", headers=headers)
    
    # Should get 404 (not found) not 401 (unauthorized)
    assert response.status_code == 404