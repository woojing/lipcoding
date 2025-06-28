import pytest
from django.test import Client
import json


@pytest.mark.django_db
def test_get_me_success_mentor():
    client = Client()
    # 회원가입
    signup_data = {
        "email": "mentor@example.com",
        "password": "password123",
        "name": "김멘토",
        "role": "mentor"
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    # 로그인
    login_data = {
        "email": "mentor@example.com",
        "password": "password123"
    }
    login_response = client.post("/api/login", json.dumps(login_data), content_type="application/json")
    token = json.loads(login_response.content)["token"]
    # 내 정보 조회
    response = client.get("/api/me", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert response.status_code == 200
    user_data = json.loads(response.content)
    assert user_data["email"] == "mentor@example.com"
    assert user_data["role"] == "mentor"
    assert "profile" in user_data
    profile = user_data["profile"]
    assert profile["name"] == "김멘토"
    assert "skills" in profile


@pytest.mark.django_db
def test_get_me_success_mentee():
    client = Client()
    signup_data = {
        "email": "mentee@example.com",
        "password": "password123",
        "name": "이멘티",
        "role": "mentee"
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    login_data = {
        "email": "mentee@example.com",
        "password": "password123"
    }
    login_response = client.post("/api/login", json.dumps(login_data), content_type="application/json")
    token = json.loads(login_response.content)["token"]
    response = client.get("/api/me", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert response.status_code == 200
    user_data = json.loads(response.content)
    assert user_data["email"] == "mentee@example.com"
    assert user_data["role"] == "mentee"
    assert "profile" in user_data
    profile = user_data["profile"]
    assert profile["name"] == "이멘티"
    assert "skills" not in profile


@pytest.mark.django_db
def test_get_me_fail_no_token():
    client = Client()
    response = client.get("/api/me")
    assert response.status_code == 401


@pytest.mark.django_db
def test_get_me_fail_invalid_token():
    client = Client()
    invalid_token = "invalid.jwt.token"
    response = client.get("/api/me", HTTP_AUTHORIZATION=f"Bearer {invalid_token}")
    assert response.status_code == 401


@pytest.mark.django_db
def test_get_me_fail_malformed_token():
    client = Client()
    signup_data = {
        "email": "test@example.com",
        "password": "password123",
        "name": "테스트",
        "role": "mentor"
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    login_response = client.post("/api/login", json.dumps(login_data), content_type="application/json")
    token = json.loads(login_response.content)["token"]
    response = client.get("/api/me", HTTP_AUTHORIZATION=token)
    assert response.status_code == 401
