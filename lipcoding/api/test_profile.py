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
        "role": "mentor",
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    # 로그인
    login_data = {"email": "mentor@example.com", "password": "password123"}
    login_response = client.post(
        "/api/login", json.dumps(login_data), content_type="application/json"
    )
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
        "role": "mentee",
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    login_data = {"email": "mentee@example.com", "password": "password123"}
    login_response = client.post(
        "/api/login", json.dumps(login_data), content_type="application/json"
    )
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
        "role": "mentor",
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    login_data = {"email": "test@example.com", "password": "password123"}
    login_response = client.post(
        "/api/login", json.dumps(login_data), content_type="application/json"
    )
    token = json.loads(login_response.content)["token"]
    response = client.get("/api/me", HTTP_AUTHORIZATION=token)
    assert response.status_code == 401


@pytest.mark.django_db
def test_update_profile_success_mentor():
    client = Client()
    # 회원가입
    signup_data = {
        "email": "mentor@example.com",
        "password": "password123",
        "name": "김멘토",
        "role": "mentor",
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    # 로그인
    login_data = {"email": "mentor@example.com", "password": "password123"}
    login_response = client.post(
        "/api/login", json.dumps(login_data), content_type="application/json"
    )
    token = json.loads(login_response.content)["token"]

    # 프로필 수정
    update_data = {
        "name": "수정된멘토",
        "bio": "수정된 소개",
        "skills": ["Python", "Django"],
    }
    response = client.put(
        "/api/profile",
        json.dumps(update_data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    profile_data = json.loads(response.content)
    assert profile_data["profile"]["name"] == "수정된멘토"
    assert profile_data["profile"]["bio"] == "수정된 소개"
    assert profile_data["profile"]["skills"] == ["Python", "Django"]


@pytest.mark.django_db
def test_update_profile_success_mentee():
    client = Client()
    # 회원가입
    signup_data = {
        "email": "mentee@example.com",
        "password": "password123",
        "name": "이멘티",
        "role": "mentee",
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    # 로그인
    login_data = {"email": "mentee@example.com", "password": "password123"}
    login_response = client.post(
        "/api/login", json.dumps(login_data), content_type="application/json"
    )
    token = json.loads(login_response.content)["token"]

    # 프로필 수정
    update_data = {"name": "수정된멘티", "bio": "수정된 소개"}
    response = client.put(
        "/api/profile",
        json.dumps(update_data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    profile_data = json.loads(response.content)
    assert profile_data["profile"]["name"] == "수정된멘티"
    assert profile_data["profile"]["bio"] == "수정된 소개"
    assert "skills" not in profile_data["profile"]


@pytest.mark.django_db
def test_update_profile_fail_no_token():
    client = Client()
    update_data = {"name": "테스트", "bio": "테스트 소개"}
    response = client.put(
        "/api/profile", json.dumps(update_data), content_type="application/json"
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_update_profile_fail_invalid_data():
    client = Client()
    # 회원가입 및 로그인
    signup_data = {
        "email": "test@example.com",
        "password": "password123",
        "name": "테스트",
        "role": "mentor",
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    login_data = {"email": "test@example.com", "password": "password123"}
    login_response = client.post(
        "/api/login", json.dumps(login_data), content_type="application/json"
    )
    token = json.loads(login_response.content)["token"]

    # 잘못된 데이터로 프로필 수정 시도
    update_data = {}  # 필수 필드 누락
    response = client.put(
        "/api/profile",
        json.dumps(update_data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_update_profile_with_image_mentor():
    client = Client()
    # 회원가입
    signup_data = {
        "email": "mentor@example.com",
        "password": "password123",
        "name": "김멘토",
        "role": "mentor",
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    # 로그인
    login_data = {"email": "mentor@example.com", "password": "password123"}
    login_response = client.post(
        "/api/login", json.dumps(login_data), content_type="application/json"
    )
    token = json.loads(login_response.content)["token"]

    # Base64 이미지 데이터 (1x1 픽셀 빨간색 PNG)
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    # 프로필 수정 (이미지 포함)
    update_data = {
        "name": "수정된멘토",
        "bio": "수정된 소개",
        "skills": ["Python", "Django"],
        "image": base64_image,
    }
    response = client.put(
        "/api/profile",
        json.dumps(update_data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    profile_data = json.loads(response.content)
    assert profile_data["profile"]["name"] == "수정된멘토"
    assert profile_data["profile"]["bio"] == "수정된 소개"
    assert profile_data["profile"]["skills"] == ["Python", "Django"]
    # 이미지 URL이 올바른 패턴인지 확인
    assert profile_data["profile"]["imageUrl"].startswith("/images/mentor/")


@pytest.mark.django_db
def test_update_profile_with_image_mentee():
    client = Client()
    # 회원가입
    signup_data = {
        "email": "mentee@example.com",
        "password": "password123",
        "name": "이멘티",
        "role": "mentee",
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    # 로그인
    login_data = {"email": "mentee@example.com", "password": "password123"}
    login_response = client.post(
        "/api/login", json.dumps(login_data), content_type="application/json"
    )
    token = json.loads(login_response.content)["token"]

    # Base64 이미지 데이터
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    # 프로필 수정 (이미지 포함)
    update_data = {"name": "수정된멘티", "bio": "수정된 소개", "image": base64_image}
    response = client.put(
        "/api/profile",
        json.dumps(update_data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    profile_data = json.loads(response.content)
    assert profile_data["profile"]["name"] == "수정된멘티"
    assert profile_data["profile"]["bio"] == "수정된 소개"
    # 이미지 URL이 올바른 형식인지 확인
    assert profile_data["profile"]["imageUrl"].startswith("/images/mentee/")


@pytest.mark.django_db
def test_get_profile_image_mentor():
    client = Client()
    # 회원가입
    signup_data = {
        "email": "mentor@example.com",
        "password": "password123",
        "name": "김멘토",
        "role": "mentor",
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    # 로그인
    login_data = {"email": "mentor@example.com", "password": "password123"}
    login_response = client.post(
        "/api/login", json.dumps(login_data), content_type="application/json"
    )
    token = json.loads(login_response.content)["token"]

    # Base64 이미지로 프로필 업데이트
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    update_data = {
        "name": "김멘토",
        "bio": "테스트 소개",
        "image": base64_image,
        "skills": ["Python"],
    }
    client.put(
        "/api/profile",
        json.dumps(update_data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    # 내 정보 조회로 user ID 가져오기
    me_response = client.get("/api/me", HTTP_AUTHORIZATION=f"Bearer {token}")
    user_data = json.loads(me_response.content)
    user_id = user_data["id"]

    # 이미지 조회
    response = client.get(
        f"/api/images/mentor/{user_id}", HTTP_AUTHORIZATION=f"Bearer {token}"
    )
    assert response.status_code == 200
    assert response["Content-Type"].startswith("image/")


@pytest.mark.django_db
def test_get_profile_image_mentee():
    client = Client()
    # 회원가입
    signup_data = {
        "email": "mentee@example.com",
        "password": "password123",
        "name": "이멘티",
        "role": "mentee",
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    # 로그인
    login_data = {"email": "mentee@example.com", "password": "password123"}
    login_response = client.post(
        "/api/login", json.dumps(login_data), content_type="application/json"
    )
    token = json.loads(login_response.content)["token"]

    # Base64 이미지로 프로필 업데이트
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    update_data = {"name": "이멘티", "bio": "테스트 소개", "image": base64_image}
    client.put(
        "/api/profile",
        json.dumps(update_data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    # 내 정보 조회로 user ID 가져오기
    me_response = client.get("/api/me", HTTP_AUTHORIZATION=f"Bearer {token}")
    user_data = json.loads(me_response.content)
    user_id = user_data["id"]

    # 이미지 조회
    response = client.get(
        f"/api/images/mentee/{user_id}", HTTP_AUTHORIZATION=f"Bearer {token}"
    )
    assert response.status_code == 200
    assert response["Content-Type"].startswith("image/")


@pytest.mark.django_db
def test_get_profile_image_not_found():
    client = Client()
    # 회원가입
    signup_data = {
        "email": "test@example.com",
        "password": "password123",
        "name": "테스트",
        "role": "mentor",
    }
    client.post("/api/signup", json.dumps(signup_data), content_type="application/json")
    # 로그인
    login_data = {"email": "test@example.com", "password": "password123"}
    login_response = client.post(
        "/api/login", json.dumps(login_data), content_type="application/json"
    )
    token = json.loads(login_response.content)["token"]

    # 존재하지 않는 이미지 조회
    response = client.get(
        "/api/images/mentor/999", HTTP_AUTHORIZATION=f"Bearer {token}"
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_get_profile_image_no_auth():
    client = Client()
    # 인증 없이 이미지 조회 시도
    response = client.get("/api/images/mentor/1")
    assert response.status_code == 401
