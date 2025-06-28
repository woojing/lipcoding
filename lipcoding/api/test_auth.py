import pytest
from django.test import Client
import jwt


@pytest.mark.django_db
def test_signup_success_as_mentor():
    """멘토 회원가입 성공 테스트"""
    client = Client()
    data = {
        "email": "mentor@example.com",
        "password": "password123",
        "name": "김멘토",
        "role": "mentor"
    }
    response = client.post("/api/signup", data, content_type="application/json")
    assert response.status_code == 201


@pytest.mark.django_db
def test_signup_success_as_mentee():
    """멘티 회원가입 성공 테스트"""
    client = Client()
    data = {
        "email": "mentee@example.com",
        "password": "password123",
        "name": "이멘티",
        "role": "mentee"
    }
    response = client.post("/api/signup", data, content_type="application/json")
    assert response.status_code == 201


@pytest.mark.django_db
def test_signup_fail_with_missing_fields():
    """필수 필드 누락 시 회원가입 실패 테스트"""
    client = Client()
    data = {
        "email": "test@example.com",
        "password": "password123"
        # name, role 필드 누락
    }
    response = client.post("/api/signup", data, content_type="application/json")
    # API 명세에 따라 400 Bad Request를 기대 (Ninja는 보통 422를 반환하나, 핸들링 필요)
    assert response.status_code == 400


@pytest.mark.django_db
def test_signup_fail_with_duplicate_email():
    """중복 이메일로 회원가입 실패 테스트"""
    client = Client()
    data = {
        "email": "duplicate@example.com",
        "password": "password123",
        "name": "김중복",
        "role": "mentor"
    }
    # 먼저 성공적으로 가입
    response1 = client.post("/api/signup", data, content_type="application/json")
    assert response1.status_code == 201

    # 동일한 이메일로 다시 가입 시도
    response2 = client.post("/api/signup", data, content_type="application/json")
    assert response2.status_code == 400


# 로그인 테스트 케이스들
@pytest.mark.django_db
def test_login_success():
    """올바른 이메일/비밀번호로 로그인 성공 테스트"""
    client = Client()
    
    # 먼저 사용자 등록
    signup_data = {
        "email": "test@example.com",
        "password": "password123",
        "name": "테스트유저",
        "role": "mentor"
    }
    client.post("/api/signup", signup_data, content_type="application/json")
    
    # 로그인 시도
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    response = client.post("/api/login", login_data, content_type="application/json")
    
    assert response.status_code == 200
    response_data = response.json()
    assert "token" in response_data
    assert isinstance(response_data["token"], str)


@pytest.mark.django_db
def test_login_fail_wrong_password():
    """잘못된 비밀번호로 로그인 실패 테스트"""
    client = Client()
    
    # 먼저 사용자 등록
    signup_data = {
        "email": "test@example.com",
        "password": "password123",
        "name": "테스트유저",
        "role": "mentor"
    }
    client.post("/api/signup", signup_data, content_type="application/json")
    
    # 잘못된 비밀번호로 로그인 시도
    login_data = {
        "email": "test@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/login", login_data, content_type="application/json")
    
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_fail_wrong_email():
    """존재하지 않는 이메일로 로그인 실패 테스트"""
    client = Client()
    
    # 등록하지 않은 이메일로 로그인 시도
    login_data = {
        "email": "nonexistent@example.com",
        "password": "password123"
    }
    response = client.post("/api/login", login_data, content_type="application/json")
    
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_fail_missing_fields():
    """필수 필드 누락 시 로그인 실패 테스트"""
    client = Client()
    
    # 이메일만 있고 비밀번호 누락
    login_data = {
        "email": "test@example.com"
        # password 필드 누락
    }
    response = client.post("/api/login", login_data, content_type="application/json")
    
    assert response.status_code == 400


@pytest.mark.django_db
def test_login_jwt_token_contains_correct_claims():
    """JWT 토큰에 올바른 클레임들이 포함되어 있는지 테스트"""
    client = Client()
    
    # 먼저 사용자 등록
    signup_data = {
        "email": "jwt_test@example.com",
        "password": "password123",
        "name": "JWT테스트",
        "role": "mentee"
    }
    client.post("/api/signup", signup_data, content_type="application/json")
    
    # 로그인하여 JWT 토큰 받기
    login_data = {
        "email": "jwt_test@example.com",
        "password": "password123"
    }
    response = client.post("/api/login", login_data, content_type="application/json")
    
    assert response.status_code == 200
    token = response.json()["token"]
    
    # JWT 토큰 디코딩 (서명 검증 없이 페이로드만 확인)
    # 실제 구현에서는 올바른 secret key로 검증해야 함
    decoded = jwt.decode(token, options={"verify_signature": False})
    
    # 요구사항에 명시된 클레임들이 포함되어 있는지 확인
    assert "iss" in decoded  # issuer
    assert "sub" in decoded  # subject
    assert "aud" in decoded  # audience
    assert "exp" in decoded  # expiration time
    assert "nbf" in decoded  # not before
    assert "iat" in decoded  # issued at
    assert "jti" in decoded  # JWT ID
    assert "name" in decoded
    assert "email" in decoded
    assert "role" in decoded
    
    # 실제 값 검증
    assert decoded["email"] == "jwt_test@example.com"
    assert decoded["name"] == "JWT테스트"
    assert decoded["role"] == "mentee"
