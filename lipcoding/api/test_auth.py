import pytest
from django.test import Client


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
